# -*- coding: utf-8 -*-
"""T7c AI 配置接口权限收紧验收（留档，可复跑）

前置：backend 运行中（:48080，@ss.hasRole('super_admin') 版本）
验收点：
  1. test 用户 PUT /knowledge/ai-config → 403
  2. test 用户 GET /knowledge/ai-config → 403
  3. admin GET/PUT 正常（保存后 hasKey=true）
用法：python verify_t7c.py
"""
import json
import sys
import urllib.request
import urllib.error

BASE = "http://localhost:48080/admin-api"


def req(method, path, body=None, token=None):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json", "tenant-id": "1"}
    if token:
        headers["Authorization"] = "Bearer " + token
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except Exception:
            return e.code, str(e)


def login(username):
    code, body = req("POST", "/system/auth/login", {"username": username, "password": "admin123"})
    assert body.get("code") == 0, f"{username} 登录失败 {body}"
    return body["data"]["accessToken"]


results = []
def record(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


def main():
    test_token = login("test")
    admin_token = login("admin")

    # 1. test PUT → 403（yudao 统一响应：HTTP 200 + code 403）
    code, r = req("PUT", "/knowledge/ai-config", {"apiKey": "dummy-key-123"}, test_token)
    record("test PUT 被拒 403", code == 200 and r.get("code") == 403 and "没有该操作权限" in r.get("msg", ""),
           f"HTTP {code} code={r.get('code')} {r.get('msg','')[:30]}")

    # 2. test GET → 403
    code, r = req("GET", "/knowledge/ai-config", token=test_token)
    record("test GET 被拒 403", code == 200 and r.get("code") == 403, f"HTTP {code} code={r.get('code')}")

    # 3. admin GET/PUT 正常
    code, r = req("GET", "/knowledge/ai-config", token=admin_token)
    record("admin GET 正常（200 + hasKey）", code == 200 and r.get("code") == 0 and "hasKey" in r["data"],
           f"HTTP {code} {str(r['data'])[:80]}")
    key = None
    with open(r"D:\The World\KnowledgeFlow-AI\ai-service\.env", encoding="utf-8") as f:
        for line in f:
            if line.startswith("LLM_API_KEY="):
                key = line.strip().split("=", 1)[1]
    code, r = req("PUT", "/knowledge/ai-config",
                  {"apiKey": key, "baseUrl": "https://api.deepseek.com", "model": "deepseek-v4-flash"},
                  admin_token)
    record("admin PUT 保存正常", code == 200 and r.get("code") == 0, f"HTTP {code} {str(r)[:60]}")
    code, r = req("GET", "/knowledge/ai-config", token=admin_token)
    record("admin GET 保存后 hasKey=true", r.get("data", {}).get("hasKey") is True, str(r["data"]))

    passed = sum(1 for ok in results if ok)
    print(f"\n===== 结果汇总：通过 {passed}/{len(results)} =====")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
