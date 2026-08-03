# -*- coding: utf-8 -*-
"""T4.4 Agent 工作流验收脚本（留档，可复跑）

前置：ai-service :8000（.env 含 LLM_API_KEY）；Qdrant :6333
验收点：
  1. 无 key：POST /ai/agent 明确报错「请配置 API Key」
  2. 有 key 全流程：检索→摘要→分类→暂停(awaiting_approval)→approve→报告，steps 记录完整
  3. 条件分支：检索结果为空 → not_found 节点，跳过 summarize/classify/report
  4. events SSE 步骤流式推送
用法：python verify_t4_4.py
"""
import json
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

AI = "http://localhost:8000"
DOC_ID = "t4-4-verify-" + str(int(time.time()))


def read_env_key():
    with open(r"D:\The World\KnowledgeFlow-AI\ai-service\.env", encoding="utf-8") as f:
        for line in f:
            if line.startswith("LLM_API_KEY="):
                return line.strip().split("=", 1)[1]
    return None


def req(method, path, body=None, base=AI, key=None, timeout=180):
    headers = {"Content-Type": "application/json"}
    if key:
        headers["X-API-Key"] = key
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    r = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except Exception:
            return e.code, str(e)


def poll_status(run_id, key, want, timeout=120):
    deadline = time.time() + timeout
    while time.time() < deadline:
        _, body = req("GET", f"/ai/agent/status?runId={run_id}", key=key)
        if body.get("status") == want:
            return body
        time.sleep(1.5)
    return body


results = []
def record(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


def main():
    api_key = read_env_key()

    # 1. 无 key 报错（8001 为 LLM_API_KEY= 空启动的无 key 实例；不可达则 SKIP）
    try:
        with urllib.request.urlopen("http://localhost:8001/docs", timeout=3):
            code, body = req("POST", "/ai/agent", {"query": "x", "kbId": "kb-a"}, base="http://localhost:8001", key=None)
            record("无 key 明确报错「请配置 API Key」", code == 400 and "API Key" in str(body),
                   f"HTTP {code} {str(body)[:80]}")
    except Exception:
        print("[SKIP] 无 key 模式（8001 无 key 实例未启动）")

    # 2. 有 key 全流程
    content = ("Agent 工作流测试：企业文档分析流程包括检索、摘要、分类与报告生成四个步骤，"
               "每个步骤由独立的图节点执行，LangGraph 负责状态编排与人工确认挂点。\n" * 25)
    code, r = req("POST", "/ai/ingest", {"documentId": DOC_ID, "kbId": "kb-agent",
                                         "filename": "agent测试.md", "fileType": "md",
                                         "content": content}, key=api_key)
    record("前置 ingest", code == 200 and r.get("chunkCount", 0) > 0, str(r)[:80])

    code, r = req("POST", "/ai/agent", {"query": "文档分析流程包含哪些步骤？", "kbId": "kb-agent",
                                        "sessionId": "agent-s1"}, key=api_key)
    run_id = r.get("runId")
    record("启动工作流返回 runId", code == 200 and run_id, str(r))

    # 轮询到 awaiting_approval（human-in-the-loop 暂停）
    body = poll_status(run_id, api_key, "awaiting_approval")
    record("流程暂停在 awaiting_approval", body.get("status") == "awaiting_approval", f"status={body.get('status')}")
    steps_before = [s["stepName"] for s in body.get("steps", [])]
    record("暂停前步骤（retrieve/summarize/classify）",
           steps_before[:3] == ["retrieve", "summarize", "classify"], str(steps_before))

    # 3. approve 继续 → done（report 异步生成，approve 响应校验 approved 标志即可）
    code, r = req("POST", f"/ai/agent/approve?runId={run_id}&decision=approve", key=api_key)
    record("approve 接口", code == 200 and r.get("approved") is True, str(r))
    body = poll_status(run_id, api_key, "done", timeout=120)
    steps = body.get("steps", [])
    names = [s["stepName"] for s in steps]
    record("全流程步骤（retrieve→summarize→classify→report）",
           names[:3] == ["retrieve", "summarize", "classify"] and "report" in names, str(names))
    record("步骤含状态/耗时/摘要", all(s.get("durationMs", 0) > 0 and s.get("outputSummary") for s in steps
                                     if s["status"] == "success"), str(steps)[:200])
    report = next((s["outputSummary"] for s in steps if s["stepName"] == "report"), "")
    record("报告已生成（非空）", len(report) > 10, f"报告长度={len(report)}")

    # 4. events SSE 步骤推送（SSE 文本，非 JSON，独立读取）
    h = {"X-API-Key": api_key}
    er = urllib.request.Request(f"{AI}/ai/agent/events?runId={run_id}", headers=h, method="GET")
    try:
        with urllib.request.urlopen(er, timeout=30) as resp:
            sse_text = resp.read().decode("utf-8")
        record("events SSE 推送步骤事件", "retrieve" in sse_text and "stepName" in sse_text,
               f"SSE 文本长度={len(sse_text)} 步骤事件数={sse_text.count('stepName')}")
    except Exception as e:
        record("events SSE 推送步骤事件", False, str(e))

    # 5. 条件分支：空结果 → not_found
    code, r = req("POST", "/ai/agent", {"query": "不存在的主题XYZ-不存在", "kbId": "kb-EMPTY",
                                        "sessionId": "agent-s2"}, key=api_key)
    run2 = r.get("runId")
    body = poll_status(run2, api_key, "done", timeout=60)
    names2 = [s["stepName"] for s in body.get("steps", [])]
    record("空结果分支走 not_found（跳过 summarize/classify/report）",
           "not_found" in names2 and "report" not in names2 and "summarize" not in names2, str(names2))
    output = next((s["outputSummary"] for s in body.get("steps", []) if s["stepName"] == "not_found"), "")
    record("空结果输出「未找到相关内容」", "未找到" in output, output[:40])

    # 清理
    delete_body = json.dumps({"filter": {"must": [{"key": "documentId", "match": {"value": DOC_ID}}]}}).encode()
    urllib.request.urlopen(urllib.request.Request(
        "http://localhost:6333/collections/knowledge_segment/points/delete",
        data=delete_body, headers={"Content-Type": "application/json"}, method="POST"), timeout=30)

    passed = sum(1 for ok in results if ok)
    print(f"\n===== 结果汇总：通过 {passed}/{len(results)} =====")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
