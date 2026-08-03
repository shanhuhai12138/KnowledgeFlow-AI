# -*- coding: utf-8 -*-
"""T4.3 问答 SSE 验收脚本（留档，可复跑）

前置：
  - ai-service 有 key 实例 :8000（uvicorn main:app，.env 含 LLM_API_KEY）
  - ai-service 无 key 实例 :8001（LLM_API_KEY= 空环境变量启动）
  - Qdrant :6333
模式：
  --nokey  仅验证无 key 明确报错（8001）
  --all    先 ingest 测试文档，再验证有 key 真实流式（8000）+ 无 key 报错（8001）
用法：python verify_t4_3.py [--nokey|--all]
"""
import json
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

AI = "http://localhost:8000"
AI_NOKEY = "http://localhost:8001"
DOC_ID = "t4-3-verify-" + str(int(time.time()))


def read_env_key():
    """从 ai-service/.env 读 LLM_API_KEY（不打印值）"""
    with open(r"D:\The World\KnowledgeFlow-AI\ai-service\.env", encoding="utf-8") as f:
        for line in f:
            if line.startswith("LLM_API_KEY="):
                return line.strip().split("=", 1)[1]
    return None


def post(path, body, base=AI, key=None, timeout=120):
    headers = {"Content-Type": "application/json"}
    if key:
        headers["X-API-Key"] = key
    r = urllib.request.Request(base + path, data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                               headers=headers, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def get_stream(path, base=AI, key=None, timeout=180):
    headers = {}
    if key:
        headers["X-API-Key"] = key
    r = urllib.request.Request(base + path, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


results = []
def record(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--all"
    api_key = read_env_key()

    if mode in ("--all",):
        # 0. ingest 测试文档（基于真实内容）
        content = ("知识库问答测试：KnowledgeFlow 支持语义检索与智能问答。\n"
                   "文档处理流水线由 Redis Streams 驱动，文档上传后自动分块向量化入库。\n"
                   "流式问答通过 SSE 协议推送，前端以打字机效果展示。\n") * 20
        code, r = post("/ai/ingest", {"documentId": DOC_ID, "kbId": "kb-qa", "filename": "问答测试.md",
                                      "fileType": "md", "content": content}, key=api_key)
        record("前置 ingest 成功", code == 200 and r.get("chunkCount", 0) > 0, str(r)[:120])

        # 1. 有 key 流式：事件序列 meta→content×n→sources→done
        status, text = get_stream(f"/ai/chat/stream?sessionId=s1&kbId=kb-qa&message="
                                  + urllib.parse.quote("文档处理流水线是怎么工作的？"),
                                  key=api_key)
        events = [l.split(":", 1)[1].strip() for l in text.splitlines() if l.startswith("event:")]
        data_lines = [l[5:].strip() for l in text.splitlines() if l.startswith("data:")]
        record("SSE HTTP 200 + text/event-stream", status == 200, f"status={status}")
        record("事件序列契约（meta→content*→sources→done）",
               events[0] == "meta" and "content" in events and events[-2] == "sources" and events[-1] == "done",
               str(events))
        # 解析 sources 事件
        sources, confidence = [], None
        for ev, dl in zip(events, data_lines):
            if ev == "sources":
                d = json.loads(dl)
                sources, confidence = d.get("sources", []), d.get("confidence")
        record("sources 非空（引用检索结果）", len(sources) > 0, f"sources={len(sources)}")
        record("confidence 已计算", confidence is not None and 0 <= confidence <= 100, f"confidence={confidence}")
        # content 拼接非空（真实 AI 输出）
        content_joined = "".join(json.loads(dl).get("delta", "") for ev, dl in zip(events, data_lines) if ev == "content")
        record("AI 流式内容非空", len(content_joined) > 5, f"内容长度={len(content_joined)}")
        print("      AI 回答预览:", content_joined[:120].replace("\n", " "))

        # 2. 有 key 同步 /ai/chat：Message 契约
        code, r = post("/ai/chat", {"sessionId": "s1", "kbId": "kb-qa", "message": "什么是语义检索？",
                                    "history": []}, key=api_key)
        contract = {"id", "role", "content", "sources", "confidence", "rating", "createdAt"}
        record("同步 /ai/chat 契约完整", code == 200 and isinstance(r, dict) and contract <= set(r.keys()),
               str(r)[:150] if not (code == 200 and isinstance(r, dict) and contract <= set(r.keys())) else f"content 长度={len(r.get('content',''))}")

        # 3. 清理 ingest 文档
        import urllib.parse as up
        delete_body = json.dumps({"filter": {"must": [{"key": "documentId", "match": {"value": DOC_ID}}]}}).encode()
        rr = urllib.request.Request("http://localhost:6333/collections/knowledge_segment/points/delete",
                                    data=delete_body, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(rr, timeout=30):
            pass

    # 无 key 模式（8001）
    if mode in ("--nokey", "--all"):
        code, body = get_stream("/ai/chat/stream?sessionId=s1&kbId=kb-qa&message=hi", base=AI_NOKEY)
        record("无 key：stream 明确报错「请配置 API Key」", code == 400 and "API Key" in str(body), f"HTTP {code} {str(body)[:100]}")
        code, body = post("/ai/chat", {"sessionId": "s1", "kbId": "kb-qa", "message": "hi"}, base=AI_NOKEY)
        record("无 key：chat 明确报错「请配置 API Key」", code == 400 and "API Key" in str(body), f"HTTP {code} {str(body)[:100]}")

    passed = sum(1 for ok in results if ok)
    print(f"\n===== 结果汇总：通过 {passed}/{len(results)} =====")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
