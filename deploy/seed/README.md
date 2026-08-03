# deploy/seed/ — 种子演示数据（T5 已填充）

实现 DR-11「通用空壳 + 内置演示知识库」：登录即有「软件开发团队知识库」+ 5 篇示例文档可提问、有引用来源。

## 目录结构

```
deploy/seed/
├── README.md          # 本文件
├── run_seed.py        # 灌入脚本：走真实 /ai/ingest 流水线（分块+embedding+写 Qdrant），幂等
├── mysql-init/        # MySQL 首启 SQL（挂载到 /docker-entrypoint-initdb.d/）
│   ├── 01-kb-tables.sql          # 知识库表（T2.2）
│   ├── 02-document-tables.sql    # 文档表（T2.3）
│   ├── 03-query-log-table.sql    # 查询日志表（T2.4）
│   └── 05-demo-kb.sql            # 演示知识库 + 5 篇文档记录（T5，幂等）
└── files/             # 5 篇演示文档正文（UTF-8，每篇 800+ 字）
    ├── 开发环境搭建SOP.md        # 答：「开发环境怎么搭建？」
    ├── 代码规范与评审流程.md      # 答：「代码评审流程是什么？」
    ├── 微服务架构设计文档.md      # 答：「微服务怎么划分模块？」
    ├── 故障排查FAQ.md            # 答：「端口被占用怎么排查？」
    └── 季度技术复盘.md
```

## 灌入方式（关键约定）

**Qdrant 向量必须走真实流水线**（`POST /ai/ingest`：分块 + embedding + 写入），禁止手工伪造向量点，
保证与用户上传行为完全一致。

```bash
# 前提：基础设施 + 后端 + ai-service 已启动；MySQL 已执行 mysql-init（全新环境自动执行）
python deploy/seed/run_seed.py
```

- 幂等：`/ai/ingest` 先删 documentId 旧点再写；脚本可重复执行，不产生重复向量。
- 脚本会回写 `kb_document.chunk_count / file_size`（真实值）。

## 扩展性

整体替换 `files/` 与 `05-demo-kb.sql` 即可转向任意垂直行业（换行业种子数据）。
注意：换 embedding 模型（如 OpenAI/BGE）后需重建 Qdrant 索引（`EMBEDDING_DIM` 变化），
删除 collection `knowledge_segment` 后重新 `python run_seed.py`。
