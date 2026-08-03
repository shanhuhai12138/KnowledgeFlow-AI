# deploy/seed/mysql-init/ — MySQL 首启初始化脚本（占位）

- 本目录挂载到 MySQL 容器的 `/docker-entrypoint-initdb.d/`，**首次启动**自动执行其中所有 `.sql` 文件（按文件名排序）。
- 任务 T5 将在此填充 `init.sql`（预置知识库 + 5 篇示例文档记录）。
- 注意：只有数据卷首次创建时执行；已存在的数据卷不会重复执行。如需重跑，`docker compose down -v` 后重新 `up`。
