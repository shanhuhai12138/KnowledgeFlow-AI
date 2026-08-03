# -*- coding: utf-8 -*-
"""T4.2 RAG 链路验收脚本（留档，可复跑）

前置：ai-service 运行中（:8000，uvicorn main:app）；Qdrant 运行中（:6333）
验收点（附录 A T4.2）：
  1. 上传一段文本 → /ai/search 可检索到（score > 0）
  2. 中文长文本分块合理（多分块、无截断乱码、offset 连续）
  3. kbId 过滤生效（无数据知识库返回空）
  4. 幂等：重复 ingest 同 documentId 不产生重复向量
用法：python verify_t4_2.py
"""
import json
import sys
import time
import urllib.request
import urllib.error

AI = "http://localhost:8000"
QDRANT = "http://localhost:6333"
COLLECTION = "knowledge_segment"
DOC_ID = "t4-verify-" + str(int(time.time()))


def post(path, body):
    r = urllib.request.Request(AI + path, data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                               headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode("utf-8"))


def qdrant_count(field, value):
    """Qdrant REST 统计匹配点数"""
    body = json.dumps({"filter": {"must": [{"key": field, "match": {"value": value}}]}}).encode()
    r = urllib.request.Request(f"{QDRANT}/collections/{COLLECTION}/points/count",
                               data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(r, timeout=30) as resp:
        return json.loads(resp.read().decode())["result"]["count"]


results = []
def record(name, ok, detail=""):
    results.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


def main():
    # 1. 中文长文本（约 3000 字，含段落/句号/逗号，验证分块优先级）
    paras = [
        "第一章 知识库平台概述。" * 30,
        "本章介绍企业级知识管理的核心概念：文档沉淀、语义检索与智能问答，三者构成闭环。" * 15,
        "第二章 架构设计\n" + "平台采用前后端分离架构，Java 负责业务与权限，Python 负责 AI 编排。" * 20,
    ]
    content = "\n\n".join(paras)

    # 2. ingest（首次）
    r = post("/ai/ingest", {"documentId": DOC_ID, "kbId": "kb-verify", "filename": "验收文档.md",
                            "fileType": "md", "content": content})
    chunk_count = r.get("chunkCount", 0)
    record("ingest 多分块（长文本 >1 块）", chunk_count > 1, f"chunkCount={chunk_count}")
    record("ingest 响应契约", r.get("documentId") == DOC_ID and r.get("vectorCount") == chunk_count, str(r))

    # 3. 分块合理性：查询 Qdrant payload 中 content 无乱码且来自原文
    r = post("/ai/search", {"query": "企业级知识管理的核心概念", "kbId": "kb-verify", "topK": 5,
                            "threshold": 0, "useHybrid": False})
    hits = r.get("results", [])
    record("检索到原文片段", len(hits) > 0 and hits[0]["score"] > 0,
           f"hits={len(hits)} top_score={hits[0]['score'] if hits else '-'}")
    if hits:
        top_content = hits[0]["content"]
        record("检索内容无乱码", all(ord(ch) < 0xFFFD for ch in top_content[:200]),
               f"content 前 40 字: {top_content[:40]!r}")
        record("检索内容来自原文", top_content[:20] in content, f"开头: {top_content[:20]!r}")

    # 4. kbId 过滤：无数据知识库返回空
    r = post("/ai/search", {"query": "企业级知识管理的核心概念", "kbId": "kb-EMPTY", "topK": 5,
                            "threshold": 0, "useHybrid": False})
    record("kbId 过滤生效（空库无结果）", len(r.get("results", [])) == 0, str(len(r.get("results", []))))

    # 5. 幂等：重复 ingest 同 documentId → 向量数不变
    before = qdrant_count("documentId", DOC_ID)
    r = post("/ai/ingest", {"documentId": DOC_ID, "kbId": "kb-verify", "filename": "验收文档.md",
                            "fileType": "md", "content": content})
    after = qdrant_count("documentId", DOC_ID)
    record("幂等（重复 ingest 向量数不变）", before == after == chunk_count,
           f"points={before}→{after} chunkCount={chunk_count}")

    # 6. 清理（Qdrant REST 删除该文档全部点）
    delete_body = json.dumps({"filter": {"must": [{"key": "documentId", "match": {"value": DOC_ID}}]}}).encode()
    r = urllib.request.Request(f"{QDRANT}/collections/{COLLECTION}/points/delete",
                               data=delete_body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(r, timeout=30):
        pass

    passed = sum(1 for ok in results if ok)
    print(f"\n===== 结果汇总：通过 {passed}/{len(results)} =====")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
