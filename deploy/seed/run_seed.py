# -*- coding: utf-8 -*-
"""T5 种子数据灌入脚本 — 复用真实 /ai/ingest 流水线（禁止伪造 Qdrant 点）。

用法：
  python run_seed.py [--ai http://localhost:8000] [--mysql-cmd docker]
  （docker compose up 后执行一次；幂等可重复执行）

流程：
  1. 读取 deploy/seed/files/ 下 5 篇演示文档
  2. 逐篇 POST /ai/ingest（真实分块 + embedding + 写 Qdrant，documentId 幂等）
  3. 回写 kb_document 的 chunk_count / file_size（真实值）
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error

SEED_DIR = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.join(SEED_DIR, "files")

# 文档 id（与 mysql-init/05-demo-kb.sql 一致）
DOCS = [
    (9001, "开发环境搭建SOP.md"),
    (9002, "代码规范与评审流程.md"),
    (9003, "微服务架构设计文档.md"),
    (9004, "故障排查FAQ.md"),
    (9005, "季度技术复盘.md"),
]
KB_ID = "1"


def ingest(ai_url: str, doc_id: int, filename: str, content: str) -> dict:
    body = json.dumps({
        "documentId": str(doc_id), "kbId": KB_ID,
        "filename": filename, "fileType": "md", "content": content,
    }, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(ai_url + "/ai/ingest", data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"ingest {filename} 失败: HTTP {e.code} {e.read().decode('utf-8')[:200]}")


def update_doc_meta(doc_id: int, chunk_count: int, file_size: int) -> None:
    """回写 kb_document 元数据（经 docker exec mysql，开发环境约定）"""
    try:
        sql = (f"UPDATE knowledgeflow.kb_document SET chunk_count={chunk_count}, "
               f"file_size={file_size} WHERE id={doc_id};")
        subprocess.run(
            ["docker", "exec", "knowledgeflow-mysql", "mysql", "-uroot", "-pknowledgeflow", "-e", sql],
            capture_output=True, check=False)
    except Exception as e:
        print(f"      (DB 回写失败已忽略: {e})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ai", default="http://localhost:8000")
    parser.add_argument("--no-db-update", action="store_true",
                        help="跳过 DB 元数据回写（容器内无 docker 命令时使用）")
    args = parser.parse_args()

    print(f"== T5 种子灌入：files 目录 {FILES_DIR} ==")
    total_chunks = 0
    for doc_id, filename in DOCS:
        path = os.path.join(FILES_DIR, filename)
        if not os.path.exists(path):
            print(f"[SKIP] 文件缺失: {filename}")
            continue
        with open(path, encoding="utf-8") as f:
            content = f.read()
        file_size = os.path.getsize(path)
        r = ingest(args.ai, doc_id, filename, content)
        chunk_count = r.get("chunkCount", 0)
        if not args.no_db_update:
            update_doc_meta(doc_id, chunk_count, file_size)
        else:
            print(f"      (跳过 DB 回写：--no-db-update)")
        total_chunks += chunk_count
        print(f"[OK] {filename}: documentId={doc_id} chunkCount={chunk_count} fileSize={file_size}B")

    print(f"== 灌入完成：5 篇文档共 {total_chunks} 个分块（重复执行幂等，不会产生重复向量）==")


if __name__ == "__main__":
    main()
