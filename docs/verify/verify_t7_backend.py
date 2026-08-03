# -*- coding: utf-8 -*-
"""T7 后端 API Key 管理验收脚本（留档，可复跑）

前置：backend 运行中（:48080，含 T7 代码）；ai-service 运行中且**无环境变量 LLM_API_KEY**
      （模拟开源部署：只靠界面配置注入，deploy/.env 已清空 LLM_API_KEY）
验收点：
  1. GET /ai-config 初始 hasKey=false
  2. PUT 保存真实 Key → GET 返回 hasKey=true + maskedKey（sk-****xxxx，不回显明文）
  3. 保存后 /api/chat 真实问答通（X-API-Key 注入链路生效）
  4. PUT apiKey="" 清除 → GET hasKey=false → /api/chat 报「请配置 API Key」
用法：python verify_t7_backend.py
"""
import json
import sys
import urllib.parse
import urllib.request
import urllib.error

BASE = "http://localhost:48080/admin-api"


def read_env_key():
    with open(r"D:\The World\KnowledgeFlow-AI\ai-service\.env", encoding="utf-8") as f:
        for line in f:
            if line.startswith("LLM_API_KEY="):
                return line.strip().split("=", 1)[1]
    return None


def req(method, path, body=None, token=None, timeout=180):
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


results = []
def record(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


def chat_stream(token, kb_id, message, timeout=180):
    q = urllib.parse.quote(message)
    r = urllib.request.Request(f"{BASE}/api/chat/stream?sessionId=t7-verify&kbId={kb_id}&message={q}",
                               headers={"tenant-id": "1", "Authorization": "Bearer " + token}, method="GET")
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def main():
    api_key = read_env_key()
    assert api_key, "ai-service/.env 缺少 LLM_API_KEY，无法验证保存链路"
    code, body = req("POST", "/system/auth/login", {"username": "admin", "password": "admin123"})
    assert body.get("code") == 0, f"登录失败 {body}"
    token = body["data"]["accessToken"]

    # 1. 初始无 key
    _, r = req("GET", "/knowledge/ai-config", token=token)
    record("初始 hasKey=false", r.get("code") == 0 and r["data"]["hasKey"] is False, str(r["data"]))

    # 2. 保存 Key → 掩码
    _, r = req("PUT", "/knowledge/ai-config",
               {"apiKey": api_key, "baseUrl": "https://api.deepseek.com", "model": "deepseek-v4-flash"},
               token=token)
    record("PUT 保存 Key", r.get("code") == 0, str(r))
    _, r = req("GET", "/knowledge/ai-config", token=token)
    d = r["data"]
    masked = d.get("maskedKey", "")
    record("GET hasKey=true", d["hasKey"] is True, str(d))
    record("掩码不回显明文", masked and api_key not in masked and "****" in masked, f"maskedKey={masked}")
    record("baseUrl/model 保存", d.get("baseUrl") == "https://api.deepseek.com" and d.get("model") == "deepseek-v4-flash",
           f"{d.get('baseUrl')} / {d.get('model')}")

    # 3. 保存后真实问答（X-API-Key 注入链路）
    code, text = chat_stream(token, 1, "开发环境怎么搭建？")
    events = [l.split(":", 1)[1].strip() for l in text.splitlines() if l.startswith("event:")]
    content = "".join(json.loads(l[5:].strip()).get("delta", "") for l in text.splitlines()
                      if l.startswith("data:") and '"content"' in l)
    record("保存后问答通（X-API-Key 注入生效）", code == 200 and len(content) > 20 and events[-1] == "done",
           f"回答 {len(content)} 字")

    # 4. 清除 Key → 问答报「请配置 API Key」
    _, r = req("PUT", "/knowledge/ai-config", {"apiKey": ""}, token=token)
    record("清除 Key", r.get("code") == 0, str(r))
    _, r = req("GET", "/knowledge/ai-config", token=token)
    record("清除后 hasKey=false", r["data"]["hasKey"] is False, str(r["data"]))
    code, text = chat_stream(token, 1, "开发环境怎么搭建？")
    record("清除后问答报「请配置 API Key」", code == 400 and "API Key" in text, f"HTTP {code} {text[:100]}")

    passed = sum(1 for ok in results if ok)
    print(f"\n===== 结果汇总：通过 {passed}/{len(results)} =====")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
