# -*- coding: utf-8 -*-
"""演示动线预检脚本：按演示前检查清单逐项自动验证（不修改任何数据）。"""
import json
import subprocess
import sys
import urllib.request

OK, BAD = "[OK]", "[!!]"
results = []


def check(name, fn):
    try:
        detail = fn()
        results.append((OK, name, detail or ""))
    except Exception as e:
        results.append((BAD, name, str(e)[:120]))


def docker_services():
    out = subprocess.run(["docker", "compose", "-f", r"D:\The World\KnowledgeFlow-AI\deploy\docker-compose.yml",
                          "ps", "--format", "{{.Name}} {{.State}}"],
                         capture_output=True, text=True, timeout=30).stdout.strip().splitlines()
    services = [l for l in out if l]
    if len(services) < 9:
        raise ValueError(f"only {len(services)} services: {services}")
    return f"{len(services)} services up"


def ai_health():
    r = json.loads(urllib.request.urlopen("http://localhost:8000/ai/health", timeout=10).read())
    return r["status"]


def frontend_up():
    code = urllib.request.urlopen("http://localhost:8080", timeout=10).getcode()
    return f"HTTP {code}"


def seed_docs():
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    c = QdrantClient(url="http://localhost:6333")
    points, _ = c.scroll(collection_name="knowledge_segment",
                         scroll_filter=Filter(must=[FieldCondition(key="kbId", match=MatchValue(value="1"))]),
                         limit=256, with_payload=False)
    return f"kb1 vectors: {len(points)} chunks"


def llm_key_set():
    env = open(r"D:\The World\KnowledgeFlow-AI\ai-service\.env", encoding="utf-8").read()
    for line in env.splitlines():
        if line.startswith("LLM_API_KEY=") and len(line.split("=", 1)[1].strip()) > 8:
            return "LLM_API_KEY present"
    raise ValueError("LLM_API_KEY missing or too short")


check("docker compose 服务 ≥9", docker_services)
check("ai-service /ai/health", ai_health)
check("前端 8080 可访问", frontend_up)
check("Qdrant 种子向量在位", seed_docs)
check("LLM Key 已配置", llm_key_set)

print("\n演示预检结果：")
for mark, name, detail in results:
    print(f"  {mark} {name}" + (f" — {detail}" if detail else ""))
fails = sum(1 for m, _, _ in results if m == BAD)
print(f"\n{len(results) - fails}/{len(results)} 通过" + ("；全部就绪，可演示" if fails == 0 else f"；{fails} 项未就绪，按演示动线预案处理"))
sys.exit(1 if fails else 0)
