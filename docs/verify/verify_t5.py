# -*- coding: utf-8 -*-
"""T5 种子演示数据验收脚本（留档，可复跑）

前置：docker compose 服务 + yudao-server(:48080) + ai-service(:8000) 运行中；
      已执行 deploy/seed/mysql-init/05-demo-kb.sql 与 deploy/seed/run_seed.py
验收点（附录 A T5）：
  1. 登录后知识库列表有「软件开发团队知识库」
  2. 文档列表 5 篇、status=processed、chunk_count > 0
  3. 提问「开发环境怎么搭建」→ 真实流式回答 + 引用来源指向演示文档
  4. 幂等：重复灌入不产生重复向量（Qdrant 计数对比）
用法：python verify_t5.py
"""
import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

BASE = "http://localhost:48080/admin-api"
QDRANT = "http://localhost:6333"
COLLECTION = "knowledge_segment"
DEMO_KB = "软件开发团队知识库"
DOC_IDS = [9001, 9002, 9003, 9004, 9005]


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


def qdrant_count(field=None, value=None):
    filt = {}
    if field:
        filt = {"must": [{"key": field, "match": {"value": value}}]}
    body = json.dumps({"filter": filt}).encode()
    r = urllib.request.Request(f"{QDRANT}/collections/{COLLECTION}/points/count",
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

    # 1. 知识库列表包含演示库
    _, r = req("GET", "/knowledge/kb/list", token=token)
    names = [kb["name"] for kb in r["data"]]
    record("知识库列表含「软件开发团队知识库」", DEMO_KB in names, str(names))
    kb = next((k for k in r["data"] if k["name"] == DEMO_KB), None)
    record("演示库为共享（isPrivate=false）", kb is not None and kb["isPrivate"] is False,
           f"isPrivate={kb.get('isPrivate') if kb else None}")
    record("演示库 documentCount=5", kb is not None and kb["documentCount"] == 5,
           f"documentCount={kb.get('documentCount') if kb else None}")

    # 2. 文档列表 5 篇 processed + chunk_count>0
    _, r = req("GET", f"/knowledge/document/page?pageNo=1&pageSize=20&kbId={kb['id']}", token=token)
    docs = [d for d in r["data"]["list"] if d["id"] in DOC_IDS]
    record("文档列表 5 篇演示文档", len(docs) == 5, f"found={len(docs)}")
    record("全部 status=processed", all(d["status"] == "processed" for d in docs), str([d["status"] for d in docs]))
    # chunk_count 查 DB（契约 VO 不含该字段）
    out = subprocess.run(["docker", "exec", "knowledgeflow-mysql", "mysql", "-uroot", "-pknowledgeflow",
                          "-N", "-e",
                          "SELECT COUNT(*) FROM knowledgeflow.kb_document WHERE id BETWEEN 9001 AND 9005 AND chunk_count > 0;"],
                         capture_output=True, text=True).stdout.strip()
    record("全部 chunk_count > 0", out == "5", f"chunk_count>0 的文档数={out}")

    # 3. 提问「开发环境怎么搭建」→ 真实流式回答 + 引用
    q = urllib.parse.quote("开发环境怎么搭建？")
    r = urllib.request.Request(f"{BASE}/api/chat/stream?sessionId=t5-verify&kbId={kb['id']}&message={q}",
                               headers={"tenant-id": "1", "Authorization": "Bearer " + token}, method="GET")
    with urllib.request.urlopen(r, timeout=180) as resp:
        sse_text = resp.read().decode("utf-8")
    events = [l.split(":", 1)[1].strip() for l in sse_text.splitlines() if l.startswith("event:")]
    data_lines = [l[5:].strip() for l in sse_text.splitlines() if l.startswith("data:")]
    record("SSE 事件序列契约", events[0] == "meta" and "content" in events and events[-2:] == ["sources", "done"],
           f"共 {len(events)} 事件")
    content = "".join(json.loads(dl).get("delta", "") for ev, dl in zip(events, data_lines) if ev == "content")
    record("真实流式回答非空", len(content) > 20, f"回答长度={len(content)}")
    print("      AI 回答预览:", content[:150].replace("\n", " "))
    sources = []
    for ev, dl in zip(events, data_lines):
        if ev == "sources":
            d = json.loads(dl)
            sources = d.get("sources", [])
    record("引用来源非空", len(sources) > 0, f"sources={len(sources)}")
    demo_docs = [s for s in sources if s.get("documentId") in [str(i) for i in DOC_IDS]]
    record("引用指向演示文档", len(demo_docs) > 0,
           str([s.get("documentName") for s in demo_docs]))

    # 4. 幂等：重复跑 run_seed.py 后 Qdrant 计数不变
    before = qdrant_count()
    subprocess.run([sys.executable, r"D:\The World\KnowledgeFlow-AI\deploy\seed\run_seed.py"],
                   capture_output=True, timeout=300)
    after = qdrant_count()
    record("幂等（重复灌入向量数不变）", before == after, f"points={before}→{after}")

    passed = sum(1 for ok in results if ok)
    print(f"\n===== 结果汇总：通过 {passed}/{len(results)} =====")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
