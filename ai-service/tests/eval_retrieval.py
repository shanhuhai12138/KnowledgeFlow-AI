# -*- coding: utf-8 -*-
"""检索质量评测（P0-2 重构版）。

三模式 A/B：dense / bm25 / hybrid（RRF k=60）
指标：Recall@5、MRR@5、平均延迟、负样本命中（noise）
数据集：tests/eval_dataset.json（gold 对齐 deploy/seed 种子契约 9001-9005）

用法：
  # 在线评测（需 ai-service + Qdrant 在线，且种子文档已灌入）
  python tests/eval_retrieval.py --base-url http://localhost:8000
  python tests/eval_retrieval.py --modes dense,bm25 --output tests/eval_results/myrun.json

  # 离线重放（不依赖服务；用本地语料重建 BM25，验证指标计算与分词开关）
  python tests/eval_retrieval.py --offline
  python tests/eval_retrieval.py --offline --tokenizer regex --label baseline-regex

  # 指标计算自检（固定 mock 结果，验证评分器本身，CI 可跑）
  python tests/eval_retrieval.py --self-test

分词开关说明（--tokenizer）：
  jieba  = 现行实现（jieba 精确模式 + 过滤，提交 8a4fed2 升级后）
  regex  = 升级前实现（中文单字切分 + 英文≥3 + 数字≥2），与现行代码的
           未安装 jieba 回退路径逐字一致——用于重放 jieba 升级前 baseline，
           产出 MRR 对比（历史档案值 0.626，见 eval_results/README.md）。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(TESTS_DIR, "eval_dataset.json")
DEFAULT_OUTPUT = os.path.join(TESTS_DIR, "eval_results", "last_run.json")

# ---------------- 数据集 ----------------


def load_dataset(path: str = DATASET_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------- 在线模式：走 /ai/search ----------------


def search_online(base_url: str, query: str, kb_id: str, mode: str, top_k: int):
    body = json.dumps({"query": query, "kbId": kb_id, "mode": mode, "topK": top_k}).encode("utf-8")
    req = urllib.request.Request(base_url + "/ai/search", data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
    t0 = time.perf_counter()
    r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8"))
    ms = int((time.perf_counter() - t0) * 1000)
    return [h["documentId"] for h in r["results"]], ms


# ---------------- 离线模式：本地重建 BM25（dense 需向量库，故离线仅支持 bm25） ----------------


def _regex_tokenize(text: str):
    """jieba 升级前的分词实现（与现行代码未安装 jieba 的回退路径一致）。"""
    import re
    tokens = []
    zh_words = re.findall(r'[\u4e00-\u9fff]{2,}', text)
    for word in zh_words:
        tokens.extend(list(word))
    en_words = re.findall(r'[a-zA-Z]{3,}', text)
    tokens.extend([w.lower() for w in en_words])
    numbers = re.findall(r'\d{2,}', text)
    tokens.extend(numbers)
    return tokens


def _jieba_tokenize(text: str):
    """现行分词实现（jieba 精确模式 + 过滤）。"""
    import re
    import jieba
    tokens = []
    for w in jieba.cut(text):
        w = w.strip()
        if not w:
            continue
        if re.match(r'[\u4e00-\u9fff]+$', w) or re.match(r'[a-zA-Z]{2,}$', w) or re.match(r'\d+$', w):
            if len(w) >= 2 or re.match(r'[\u4e00-\u9fff]', w):
                tokens.append(w.lower() if w.isascii() else w)
    return tokens


def _local_hash_vector(text: str, dim: int = 768):
    """与 rag/embedder.py LocalHashEmbedder 同构的单文本向量（离线 dense 参考实现）。

    注意：离线模式的 dense 结果仅作参考（impl 注明 offline-local-hash），
    对外数字以在线评测（真实 embedder + Qdrant）为准。
    """
    import hashlib
    import math
    import re
    vec = [0.0] * dim
    feats = re.findall(r'[\u4e00-\u9fff]', text) + re.findall(r'[a-zA-Z0-9]+', text)
    bigrams = [text[i:i + 2] for i in range(len(text) - 1)
               if re.match(r'[\u4e00-\u9fff]{2}$', text[i:i + 2])]
    for f in feats + bigrams:
        h = int(hashlib.md5(f.encode("utf-8")).hexdigest(), 16)
        vec[h % dim] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _offline_corpus():
    """从 deploy/seed/files 读种子语料，构造 BM25 文档集（id=种子契约 9001-9005）。"""
    seed_files_dir = os.path.join(TESTS_DIR, "..", "..", "deploy", "seed", "files")
    docs = [
        ("9001", "开发环境搭建SOP.md"),
        ("9002", "代码规范与评审流程.md"),
        ("9003", "微服务架构设计文档.md"),
        ("9004", "故障排查FAQ.md"),
        ("9005", "季度技术复盘.md"),
    ]
    corpus = []
    for doc_id, filename in docs:
        p = os.path.join(seed_files_dir, filename)
        if not os.path.exists(p):
            sys.exit(f"[offline] 种子语料缺失: {p}")
        with open(p, encoding="utf-8") as f:
            corpus.append({"id": doc_id, "content": f.read(), "metadata": {"filename": filename}})
    return corpus


def search_offline(query: str, mode: str, top_k: int, tokenizer: str):
    corpus = _offline_corpus()
    tok = _jieba_tokenize if tokenizer == "jieba" else _regex_tokenize
    from rank_bm25 import BM25Okapi
    bm25 = BM25Okapi([tok(d["content"]) for d in corpus])
    scores = bm25.get_scores(tok(query)) if tok(query) else [0.0] * len(corpus)
    order = sorted(range(len(corpus)), key=lambda i: -scores[i])[:top_k]
    ms = 0
    return [corpus[i]["id"] for i in order if scores[i] > 0], ms


# ---------------- 指标 ----------------


def evaluate(dataset: dict, searcher, modes, tokenizer: str) -> dict:
    results = {}
    for mode in modes:
        recall_hits, rr_sum, lats, noise_fired = 0, 0.0, [], 0
        detail = []
        gold_n = 0
        for q in dataset["queries"]:
            gold = [str(g) for g in q["gold"]]
            if mode == "offline-dense":
                ids, ms = [], 0
            elif mode == "bm25" and searcher is None:
                ids, ms = search_offline(q["query"], mode, dataset["topK"], tokenizer)
            else:
                ids, ms = searcher(q["query"], mode)
            lats.append(ms)
            if not gold:
                gold_n += 0
                if ids and str(ids[0]).startswith("9"):
                    noise_fired += 1
                detail.append({"id": q["id"], "query": q["query"], "tag": "NEG",
                               "top2": ids[:2], "ms": ms})
                continue
            gold_n += 1
            hit_pos = next((i + 1 for i, d in enumerate(ids) if str(d) in gold), None)
            if hit_pos:
                recall_hits += 1
                rr_sum += 1.0 / hit_pos
            detail.append({"id": q["id"], "query": q["query"],
                           "tag": "OK" if hit_pos else "MISS",
                           "hit_pos": hit_pos, "top2": ids[:2], "ms": ms})
        results[mode] = {
            "recall5": round(recall_hits / gold_n, 4) if gold_n else 0.0,
            "mrr5": round(rr_sum / gold_n, 4) if gold_n else 0.0,
            "avg_ms": round(sum(lats) / len(lats), 1) if lats else 0,
            "noise": f"{noise_fired}/{len(dataset['queries']) - gold_n}",
            "detail": detail,
        }
    return results


def summarize(results: dict) -> str:
    lines = ["%-10s %9s %9s %10s %12s" % ("mode", "Recall@5", "MRR@5", "avg_ms", "noise_fired")]
    for m, r in results.items():
        lines.append("%-10s %8.1f%% %9.3f %9dms %12s" % (
            m, r["recall5"] * 100, r["mrr5"], r["avg_ms"], r["noise"]))
    return "\n".join(lines)


# ---------------- 自检：固定 mock 验证评分器 ----------------


def self_test() -> bool:
    ds = {
        "topK": 5,
        "queries": [
            {"id": "a", "scenario": "s", "query": "x", "gold": ["9011"]},
            {"id": "b", "scenario": "s", "query": "y", "gold": ["9012"]},
            {"id": "c", "scenario": "s", "query": "z", "gold": []},
        ],
    }

    class FakeSearcher:
        def __call__(self, query, mode):
            if query == "x":
                return ["9011", "1", "2"], 10      # 命中第 1 位 → rr=1.0
            if query == "y":
                return ["3", "4", "9012"], 20      # 命中第 3 位 → rr=1/3
            return ["5"], 30                        # 负样本但不涉及 gold

    r = evaluate(ds, FakeSearcher(), ["bm25"], "jieba")["bm25"]
    assert abs(r["recall5"] - 1.0) < 1e-9, r
    assert abs(r["mrr5"] - 0.6667) < 1e-4, r
    assert r["noise"] == "0/1", r
    print("self-test ok: recall=1.0 mrr=%.4f noise=%s" % (r["mrr5"], r["noise"]))
    return True


# ---------------- 主入口 ----------------


def main():
    ap = argparse.ArgumentParser(description="KnowledgeFlow 检索评测（P0-2）")
    ap.add_argument("--base-url", default="http://localhost:8000", help="ai-service 地址")
    ap.add_argument("--modes", default="dense,bm25,hybrid", help="逗号分隔：dense,bm25,hybrid")
    ap.add_argument("--dataset", default=DATASET_PATH)
    ap.add_argument("--output", default=DEFAULT_OUTPUT, help="结果 JSON 输出路径")
    ap.add_argument("--offline", action="store_true", help="离线重放：本地语料重建 BM25（无需服务）")
    ap.add_argument("--tokenizer", choices=["jieba", "regex"], default="jieba",
                    help="离线模式分词器：jieba=现行 / regex=jieba 升级前 baseline")
    ap.add_argument("--label", default="", help="结果标签（如 baseline-regex / jieba-final）")
    ap.add_argument("--self-test", action="store_true", help="指标计算自检（CI 可跑）")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(0 if self_test() else 1)

    dataset = load_dataset(args.dataset)
    started = time.strftime("%Y-%m-%dT%H:%M:%S")

    if args.offline:
        print(f"== 离线重放 tokenizer={args.tokenizer}（BM25 only；dense/hybrid 需在线评测）==")
        results = evaluate(dataset, None, ["bm25"], args.tokenizer)
        impl = f"offline-bm25-{args.tokenizer}"
    else:
        modes = [m.strip() for m in args.modes.split(",") if m.strip()]
        print(f"== 在线评测 modes={modes} base={args.base_url} ==")

        def searcher(query, mode):
            return search_online(args.base_url, query, dataset["kbId"], mode, dataset["topK"])

        results = evaluate(dataset, searcher, modes, args.tokenizer)
        impl = "online"

    print("\n" + summarize(results))

    payload = {
        "label": args.label or impl,
        "impl": impl,
        "startedAt": started,
        "datasetVersion": dataset.get("version"),
        "datasetPath": os.path.relpath(args.dataset, os.path.join(TESTS_DIR, "..", "..")),
        "topK": dataset["topK"],
        "results": {m: {k: v for k, v in r.items() if k != "detail"} for m, r in results.items()},
        "detail": {m: r["detail"] for m, r in results.items()},
    }
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"\n[written] {args.output}")


if __name__ == "__main__":
    main()
