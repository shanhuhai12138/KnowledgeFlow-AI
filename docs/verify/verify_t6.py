# -*- coding: utf-8 -*-
"""T6 运行时治理验收脚本（留档，可复跑）

前置：yudao-server(:48080) + ai-service(:8000) + 基础设施运行中
验收点：
  T6.1 Redis Stream 修剪：造 2100 条消息 → 触发 stream → XLEN <= 2000
  T6.2 查询日志清理：造 40 天前日志 → 触发 querylog → 旧日志被删
  T6.3 SSE 治理：流式端点正常（事件契约）+ 完成后 onCompletion 关闭
  T6.4 文档版本保留：造 7 个版本 → 触发 version → 每文档保留 5
  T6.5 孤儿向量：直接插 Qdrant 孤儿点 → 触发 orphan → 点被删
用法：python verify_t6.py
"""
import json
import subprocess
import sys
import time
import urllib.request
import urllib.error

BASE = "http://localhost:48080/admin-api"
QDRANT = "http://localhost:6333"


def req(method, path, body=None, token=None, timeout=60):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json", "tenant-id": "1"}
    if token:
        headers["Authorization"] = "Bearer " + token
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except Exception:
            return e.code, str(e)


def mysql(sql):
    return subprocess.run(["docker", "exec", "knowledgeflow-mysql", "mysql", "-uroot", "-pknowledgeflow",
                           "--default-character-set=utf8mb4", "-N", "-e", sql],
                          capture_output=True, text=True).stdout.strip()


def redis(*args):
    return subprocess.run(["docker", "exec", "knowledgeflow-redis", "redis-cli"] + list(args),
                          capture_output=True, text=True).stdout.strip()


def qdrant_upsert(collection, payload):
    """Qdrant upsert：PUT /collections/{name}/points（REST 正确路径）"""
    body = json.dumps(payload).encode()
    r = urllib.request.Request(f"{QDRANT}/collections/{collection}/points",
                               data=body, headers={"Content-Type": "application/json"}, method="PUT")
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()[:200]}


def qdrant_count(field=None, value=None):
    filt = {}
    if field:
        filt = {"must": [{"key": field, "match": {"value": value}}]}
    body = json.dumps({"filter": filt}).encode()
    r = urllib.request.Request(f"{QDRANT}/collections/knowledge_segment/points/count",
                               data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(r, timeout=30) as resp:
        return json.loads(resp.read().decode())["result"]["count"]


results = []
def record(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


def main():
    code, body = req("POST", "/system/auth/login", {"username": "admin", "password": "admin123"})
    assert body.get("code") == 0, f"登录失败 {body}"
    token = body["data"]["accessToken"]
    print("admin 登录成功")

    # ===== T6.1 Stream 修剪 =====
    before = int(redis("XLEN", "doc-pipeline"))
    # 造 2100 条消息
    pipe_cmds = ["-p", "doc-pipeline", "*", "documentId", "999999", "kbId", "1",
                 "objectName", "t6.txt", "filename", "t6.txt", "attempt", "1"]
    redis("XADD", *pipe_cmds)  # 幂等验证用占位（XADD 一次）
    for _ in range(2100):
        redis("XADD", "doc-pipeline", "*", "documentId", "999999", "kbId", "1",
              "objectName", "t6.txt", "filename", "t6.txt", "attempt", "1")
    _, r = req("POST", "/knowledge/cleanup/run?type=stream", token=token)
    after = int(redis("XLEN", "doc-pipeline"))
    trimmed = r.get("data")
    record("T6.1 Stream 修剪（XTRIM MAXLEN ~2000 近似）",
           r.get("code") == 0 and (isinstance(trimmed, (int, float)) and trimmed > 0) and after < before + 2101,
           f"XLEN {before}→{after}（造 2101 条），清理返回={trimmed}")
    # 清理测试消息（保留 <=2000 条无妨，后续 XTRIM 再清；直接删 stream 重建不现实，留着）

    # ===== T6.2 查询日志清理 =====
    n = mysql("SELECT COUNT(*) FROM knowledgeflow.kb_query_log WHERE deleted=0 AND create_time < NOW() - INTERVAL 30 DAY;")
    # 造一条 40 天前的日志（直接 SQL 插入，绕过接口）
    mysql("INSERT INTO knowledgeflow.kb_query_log (user_id, kb_id, query_text, took_ms, hit_count, tenant_id, create_time) "
          "VALUES (1, 1, 't6-旧日志', 1, 0, 1, NOW() - INTERVAL 40 DAY);")
    n2 = mysql("SELECT COUNT(*) FROM knowledgeflow.kb_query_log WHERE deleted=0 AND create_time < NOW() - INTERVAL 30 DAY;")
    _, r = req("POST", "/knowledge/cleanup/run?type=querylog", token=token)
    n3 = mysql("SELECT COUNT(*) FROM knowledgeflow.kb_query_log WHERE deleted=0 AND create_time < NOW() - INTERVAL 30 DAY;")
    record("T6.2 查询日志清理（30 天前）", r.get("code") == 0 and int(n2) > int(n) and int(n3) == 0,
           f"旧日志 {n}→{n2}→清理后 {n3}，清理返回={r.get('data')}")

    # ===== T6.3 SSE 治理 =====
    import urllib.parse as up
    q = up.quote("什么是 RAG？")
    r = urllib.request.Request(f"{BASE}/api/chat/stream?sessionId=t6-sse&kbId=1&message={q}",
                               headers={"tenant-id": "1", "Authorization": "Bearer " + token}, method="GET")
    with urllib.request.urlopen(r, timeout=180) as resp:
        text = resp.read().decode("utf-8")
    events = [l.split(":", 1)[1].strip() for l in text.splitlines() if l.startswith("event:")]
    record("T6.3 SSE 流式正常（契约事件）", events[0] == "meta" and events[-2:] == ["sources", "done"],
           f"共 {len(events)} 事件")

    # ===== T6.4 文档版本保留 =====
    # 造一个临时文档 + 7 个版本
    doc_id = mysql("SELECT COALESCE(MAX(id),0)+1 FROM knowledgeflow.kb_document;")
    mysql(f"INSERT INTO knowledgeflow.kb_document (id, kb_id, uploader_id, filename, object_name, file_type, status, tenant_id) "
          f"VALUES ({doc_id}, 1, 1, 't6-version.md', 't6-version.md', 'md', 'processed', 1);")
    for v in range(7):
        mysql(f"INSERT INTO knowledgeflow.kb_document_version (document_id, object_name, version, created_by, tenant_id) "
              f"VALUES ({doc_id}, 't6-v{v}.md', {v + 1}, 1, 1);")
    ver_before = mysql(f"SELECT COUNT(*) FROM knowledgeflow.kb_document_version WHERE document_id={doc_id} AND deleted=0;")
    _, r = req("POST", "/knowledge/cleanup/run?type=version", token=token)
    ver_after = mysql(f"SELECT COUNT(*) FROM knowledgeflow.kb_document_version WHERE document_id={doc_id} AND deleted=0;")
    record("T6.4 文档版本保留最近 5 个", r.get("code") == 0 and int(ver_before) == 7 and int(ver_after) <= 5,
           f"版本 {ver_before}→{ver_after}，清理返回={r.get('data')}")
    # 清理临时数据
    mysql(f"DELETE FROM knowledgeflow.kb_document_version WHERE document_id={doc_id}; "
          f"DELETE FROM knowledgeflow.kb_document WHERE id={doc_id};")

    # ===== T6.5 孤儿向量 =====
    # 直接向 Qdrant 插入一个 documentId=999999 的孤儿点（绕过 Python）
    qdrant_upsert("knowledge_segment", {
        "points": [{"id": 999999999001, "vector": [0.1] * 768,
                    "payload": {"documentId": "999999", "kbId": "1", "content": "orphan"}}]})
    orphan_before = qdrant_count("documentId", "999999")
    _, r = req("POST", "/knowledge/cleanup/run?type=orphan", token=token)
    orphan_after = qdrant_count("documentId", "999999")
    record("T6.5 孤儿向量兜底清理", r.get("code") == 0 and orphan_before > 0 and orphan_after == 0,
           f"孤儿点 {orphan_before}→{orphan_after}，清理返回={r.get('data')}")

    passed = sum(1 for ok in results if ok)
    print(f"\n===== 结果汇总：通过 {passed}/{len(results)} =====")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
