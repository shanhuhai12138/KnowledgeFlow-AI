"""T3.1 自检：真实登录接口验证（admin/admin123 → accessToken），UTF-8 安全"""
import json
import urllib.request

req = urllib.request.Request(
    "http://localhost:48080/admin-api/system/auth/login",
    data=json.dumps({"username": "admin", "password": "admin123"}).encode("utf-8"),
    headers={"Content-Type": "application/json", "tenant-id": "1"},
    method="POST",
)
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        body = json.loads(r.read().decode("utf-8"))
        print("code:", body.get("code"))
        token = (body.get("data") or {}).get("accessToken", "")
        print("accessToken 前 20 位:", token[:20] if token else "(空)")
        assert body.get("code") == 0 and token, "登录失败"
        print("LOGIN-OK")
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read().decode("utf-8", "ignore"))
    raise SystemExit(1)
