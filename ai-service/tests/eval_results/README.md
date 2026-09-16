# 检索评测结果存档

所有对外引用的检索指标数字，必须能对应到本目录下的一份 JSON 存档。存档即出处，无存档的数字不得写进 README / 简历。

## 指标定义

- **Recall@5**：Top-5 结果中至少命中一条 gold 文档的查询比例（gold 见 `tests/eval_dataset.json`）
- **MRR@5**：gold 首次命中位次倒数的平均值（第 1 位=1.0，第 2 位=0.5，…，未命中=0）
- **noise**：2 条负样本（与知识库无关的查询）中，Top-1 命中知识库文档的比例——越低越好
- **avg_ms**：检索请求平均耗时。**口径=本机单发均值，非并发压测、非 P95**，引用时必须带此标注

## 复现方式

```bash
# 在线评测（权威口径；需 docker compose up + seed 灌入 + ai-service 在线）
cd ai-service
python tests/eval_retrieval.py --base-url http://localhost:8000 \
    --output tests/eval_results/<日期>_<标签>.json

# 离线重放（BM25 only；本地语料重建，无需服务）
python tests/eval_retrieval.py --offline --tokenizer jieba
python tests/eval_retrieval.py --offline --tokenizer regex   # jieba 升级前基线

# 指标计算自检（CI 已挂）
python tests/eval_retrieval.py --self-test
```

## 存档清单

| 日期 | commit | 标签 | 实现 | 结果摘要 |
|------|--------|------|------|---------|
| 2026-08（历史档案） | 072de30 前后 | jieba-final（当时实机） | online /ai/search，三模式，**金标为当时实机库 ID 9011-9015** | hybrid Recall@5 **1.0** / MRR 0.606 / 58.8ms；dense Recall@5 0.944 / MRR 0.801 / 25.0ms；bm25 MRR 0.650；noise 2/2。原结果文件曾存于 `D:\神之龙仓\.openclaw\tmp\eval_results.json`（不在仓库，内容已抄录于此） |
| 2026-08（历史档案） | 8a4fed2 之前 | regex-baseline（当时实机） | online /ai/search，bm25 单模式 | bm25 MRR@5 **0.626**（jieba 升级前基线；与上行的 +0.024/约 +4% 即简历口径来源） |
| 2026-09-16 | feat/eval-pipeline | [offline-regex-replay](2026-09-16_offline-regex-baseline.json) | offline BM25，regex 分词（5 篇整文档语料） | Recall@5 1.0 / **MRR@5 0.618** / noise 2/2 |
| 2026-09-16 | feat/eval-pipeline | [offline-jieba-replay](2026-09-16_offline-jieba.json) | offline BM25，jieba 分词（5 篇整文档语料） | Recall@5 1.0 / **MRR@5 0.648** / noise 1/2 |

## 口径说明（重要，面试可讲）

1. **金标契约已对齐仓库种子**：数据集 v2 的 gold 是 9001-9005（与 `deploy/seed/run_seed.py` 和 `05-demo-kb.sql` 一致）。历史档案的 9011-9015 是当时实机数据库的 ID，**clone 仓库按现行种子部署的人无法复现旧 ID**——这正是 v2 数据集存在的原因。
2. **离线重放 ≠ 在线数字**：离线用 5 篇整文档重建 BM25（在线是分块后 scroll 全量），所以 MRR 数值有偏移（0.618/0.648 vs 历史 0.626/0.650），但**方向一致**：jieba 使 MRR 上升约 0.02-0.03，且负样本误触更少。对外引用优先在线口径。
3. **在线 dense/hybrid 的复现依赖 embedding provider**：无 OPENAI_API_KEY 时为 local hash 向量（默认），有 Key 时为 text-embedding-3-small——切换 provider 需重建 Qdrant 集合并重跑。存档时必须在标签中注明 provider。
