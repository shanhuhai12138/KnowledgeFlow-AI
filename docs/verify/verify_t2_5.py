# -*- coding: utf-8 -*-
"""T2.5 文档处理流水线验收脚本（可复跑）

前置：yudao-server 运行中（:48080）；mock AI 服务可选（docs/verify/mock_ai_service.py，:8000）
验收点：
  1. 幂等跳过：幽灵消息（不存在的 documentId）→ 消费 + XACK（XPENDING=0）
  2. 失败重试：Python /ai/ingest 不可达 → attempt 1→2→3 → status=failed + error + XACK（不死循环）
  3. 成功链路：mock /ai/ingest → pending→processing→processed + chunkCount 回填
用法：python verify_t2_5.py [--mock]
"""
import argparse
import json
import subprocess
import sys
import time
import urllib.request
import urllib.error
import io
import uuid

BASE = "http://localhost:48080/admin-api"
REDIS = "knowledgeflow-redis"


def req(method, path, body=None, token=None):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json", "tenant-id": "1"}
    if token:
        headers["Authorization"] = "Bearer " + token
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def redis(cmd):
    return subprocess.run(["docker", "exec", REDIS, "redis-cli"] + cmd,
                          capture_output=True, text=True).stdout.strip()


def upload(token, kb_id, filename, content_bytes):
    boundary = "----B" + uuid.uuid4().hex
    buf = io.BytesIO()
    buf.write(("--%s\r\nContent-Disposition: form-data; name=\"kbId\"\r\n\r\n%s\r\n" % (boundary, kb_id)).encode())
    buf.write(("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\nContent-Type: application/octet-stream\r\n\r\n" % (boundary, filename)).encode())
    buf.write(content_bytes)
    buf.write(("\r\n--%s--\r\n" % boundary).encode())
    r = urllib.request.Request(BASE + "/knowledge/document/upload", data=buf.getvalue(),
        headers={"tenant-id": "1", "Authorization": "Bearer " + token,
                 "Content-Type": "multipart/form-data; boundary=" + boundary}, method="POST")
    with urllib.request.urlopen(r, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))["data"]


def check(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")
    return ok


results = []
def record(name, ok, detail=""):
    results.append(ok)
    check(name, ok, detail)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true", help="使用 mock AI 服务测成功链路")
    args = parser.parse_args()

    _, body = req("POST", "/system/auth/login", {"username": "admin", "password": "admin123"})
    assert body["code"] == 0, f"登录失败 {body}"
    token = body["data"]["accessToken"]

    # ===== 1. 幂等跳过 =====
    ghost_id = str(uuid.uuid4().int % 10**12)
    redis(["XADD", "doc-pipeline", "*", "documentId", ghost_id, "kbId", "1",
           "objectName", "ghost.txt", "filename", "ghost.txt", "attempt", "1"])
    time.sleep(4)
    pending = redis(["XPENDING", "doc-pipeline", "doc-pipeline-group"])
    record("幂等跳过（幽灵消息已消费 + XACK）", pending == "0", f"XPENDING={pending}")

    # ===== 2. 失败重试 3 次 → failed（Python 未起时） =====
    if not args.mock:
        doc = upload(token, 1, "t25-retry.txt", "重试测试".encode("utf-8"))
        time.sleep(25)
        _, body = req("GET", f"/knowledge/document/get?id={doc['id']}", token=token)
        d = body["data"]
        out = subprocess.run(["docker", "exec", "knowledgeflow-mysql", "mysql", "-uroot", "-pknowledgeflow",
                              "--default-character-set=utf8mb4", "-N", "-e",
                              f"SELECT status, IFNULL(LEFT(error,40),'') FROM knowledgeflow.kb_document WHERE id={doc['id']};"],
                             capture_output=True, text=True).stdout.strip().split("\t")
        db_status, db_error = (out + [""])[:2]
        record("失败重试 3 次后 failed", db_status == "failed" and db_error,
               f"DB status={db_status} error={db_error[:40]}")
        pending = redis(["XPENDING", "doc-pipeline", "doc-pipeline-group"])
        record("失败后 PEL 无残留", pending == "0", f"XPENDING={pending}")
        # 清理
        req("DELETE", f"/knowledge/document/delete?ids={doc['id']}", token=token)
    else:
        print("[SKIP] 失败重试（--mock 模式下跳过）")

    # ===== 3. 成功链路（需 mock /ai/ingest 运行） =====
    if args.mock:
        content = ("知识库文档处理成功链路验证：这是一段用于向量化的文档文本，"
                   "包含足够的文字来生成多个分块，流水线将自动完成解析分块向量化入库。").encode("utf-8")
        doc = upload(token, 1, "t25-success.md", content)
        for _ in range(20):
            time.sleep(2)
            _, body = req("GET", f"/knowledge/document/get?id={doc['id']}", token=token)
            d = body["data"]
            if d["status"] in ("processed", "failed"):
                break
        record("成功链路 processed", d["status"] == "processed", f"status={d['status']}")
        # chunkCount 回填验证（契约 VO 不含 chunkCount，查 DB）
        out = subprocess.run(["docker", "exec", "knowledgeflow-mysql", "mysql", "-uroot", "-pknowledgeflow",
                              "--default-character-set=utf8mb4", "-N", "-e",
                              f"SELECT chunk_count FROM knowledgeflow.kb_document WHERE id={doc['id']};"],
                             capture_output=True, text=True).stdout.strip()
        record("chunkCount 回填", out.isdigit() and int(out) > 0, f"chunkCount={out}")
        pending = redis(["XPENDING", "doc-pipeline", "doc-pipeline-group"])
        record("成功后 PEL 无残留", pending == "0", f"XPENDING={pending}")
        # 清理
        req("DELETE", f"/knowledge/document/delete?ids={doc['id']}", token=token)
    else:
        print("[SKIP] 成功链路（需 --mock）")

    passed = sum(1 for ok in results if ok)
    print(f"\n===== 结果汇总：通过 {passed}/{len(results)} =====")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
