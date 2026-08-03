# -*- coding: utf-8 -*-
"""全量 Docker 部署端到端验收脚本（留档，可复跑）

前置：docker compose up -d --build（deploy/）全部 healthy；seed 已灌入
验收点：
  1. http://localhost:8080 前端可访问
  2. 登录 admin/admin123（经 nginx → backend）
  3. 种子知识库「软件开发团队知识库」可见
  4. 提问「代码评审流程是什么？」→ 真实流式回答 + sources 引用（nginx→backend→ai-service→DeepSeek 全容器链路）
用法：python verify_docker.py
"""
import json
import subprocess
import sys
import urllib.parse
import urllib.request
import urllib.error

BASE = "http://localhost:8080"  # nginx 反代入口


def get_raw(path, headers=None, timeout=180):
    r = urllib.request.Request(BASE + path, headers=headers or {}, method="GET")
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return resp.status, resp.read(), resp.headers


def post(path, body, token=None):
    h = {"Content-Type": "application/json", "tenant-id": "1"}
    if token:
        h["Authorization"] = "Bearer " + token
    r = urllib.request.Request(BASE + path, data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                               headers=h, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode("utf-8"))


results = []
def record(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


def main():
    # 0. compose ps 全 healthy
    out = subprocess.run(["docker", "compose", "-f", r"D:\The World\KnowledgeFlow-AI\deploy\docker-compose.yml",
                          "ps", "--format", "{{.Name}} {{.Status}}"], capture_output=True, text=True).stdout
    healthy = sum(1 for line in out.splitlines() if "healthy" in line)
    record("全部服务 Up & healthy", healthy >= 7, f"healthy={healthy}/7\n{out}")

    # 1. 前端
    code, html, _ = get_raw("/", timeout=15)
    record("前端 8080 可访问", code == 200 and "app" in html.decode("utf-8"), f"HTTP {code}")

    # 2. 登录
    r = post("/admin-api/system/auth/login", {"username": "admin", "password": "admin123"})
    token = r.get("data", {}).get("accessToken")
    record("登录 admin/admin123", r.get("code") == 0 and token, f"code={r.get('code')}")

    # 3. 种子知识库
    r = urllib.request.Request(BASE + "/admin-api/knowledge/kb/list",
                               headers={"tenant-id": "1", "Authorization": "Bearer " + token}, method="GET")
    with urllib.request.urlopen(r, timeout=30) as resp:
        names = [kb["name"] for kb in json.loads(resp.read().decode("utf-8"))["data"]]
    record("种子知识库可见", "软件开发团队知识库" in names, str(names))

    # 4. 提问（全容器链路）
    q = urllib.parse.quote("代码评审流程是什么？")
    code, text, headers = get_raw(f"/admin-api/api/chat/stream?sessionId=docker-demo&kbId=1&message={q}",
                                  headers={"tenant-id": "1", "Authorization": "Bearer " + token})
    sse = text.decode("utf-8")
    events = [l.split(":", 1)[1].strip() for l in sse.splitlines() if l.startswith("event:")]
    content = "".join(json.loads(l[5:].strip()).get("delta", "") for l in sse.splitlines()
                      if l.startswith("data:") and '"content"' in l)
    sources_ok = "sources" in events and events[-1] == "done"
    record("真实流式回答（meta→content→sources→done）",
           code == 200 and events[0] == "meta" and sources_ok and len(content) > 30,
           f"事件 {len(events)} 个，回答 {len(content)} 字")
    print("      AI 回答预览:", content[:120].replace("\n", " "))

    passed = sum(1 for ok in results if ok)
    print(f"\n===== 结果汇总：通过 {passed}/{len(results)} =====")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
