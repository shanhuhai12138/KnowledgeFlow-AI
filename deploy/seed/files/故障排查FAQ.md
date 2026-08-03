# 故障排查 FAQ

> 团队开发与部署过程中常见问题的排查手册。遇到报错先看本文档，按步骤定位，解决后欢迎补充新条目。

## 1. 端口被占用

### 现象

启动服务时报错：`Port 48080 was already in use` 或 `BindException: Address already in use`。

### 排查步骤

1. 查看哪个进程占用了端口：
   ```bash
   netstat -ano | grep ":48080"
   ```
   最后一列为进程 PID。
2. 查看该进程是什么：
   ```bash
   tasklist | findstr <PID>
   ```
3. 若是残留的旧服务进程，结束它：
   ```bash
   taskkill /F /PID <PID>
   ```
4. 若是其他应用占用（如本机 MySQL 占 3306、Redis 占 6379），**不要杀**，改走项目约定的映射端口：MySQL 用 3307、Redis 用 6380。
5. 验证端口已释放：`netstat -ano | grep ":48080"` 无输出即可重启服务。

### 预防

- 改完后端代码重启前，先确认旧进程已 kill，否则 Windows 会锁住 jar 文件导致重新打包失败。

## 2. 数据库连接失败

### 现象

后端启动报错：`Communications link failure` 或 `Access denied for user 'knowledgeflow'`。

### 排查步骤

1. 确认 MySQL 容器在运行：`docker compose ps`，mysql 状态应为 healthy。
2. 确认连接串正确：`jdbc:mysql://localhost:3307/knowledgeflow`（注意端口是 3307，不是 3306）。
3. 确认账号密码：默认 `knowledgeflow / knowledgeflow`，与 `deploy/.env` 一致。
4. 手动验证：`docker exec knowledgeflow-mysql mysql -uknowledgeflow -pknowledgeflow -e "SELECT 1"`。
5. 若报 `Access denied`，检查 `.env` 中 `MYSQL_ROOT_PASSWORD` 是否与首次初始化一致——MySQL 数据卷已存在时修改密码不会生效，需 `docker compose down -v` 重建（会清空数据，慎用）。

## 3. Redis 连接失败

### 现象

后端启动报错：`Unable to connect to Redis` 或 `RedisConnectionFailureException`。

### 排查步骤

1. 确认 Redis 容器运行：`docker compose ps`。
2. 确认端口：连接地址应为 `localhost:6380`（本机 6379 可能被本机 Redis 占用）。
3. 手动验证：`docker exec knowledgeflow-redis redis-cli ping` 应返回 `PONG`。
4. 若 Redis 中有大量堆积的 Stream 消息，查看：`docker exec knowledgeflow-redis redis-cli XLEN doc-pipeline`。

## 4. AI 服务不可用（503）

### 现象

前端提问或搜索时返回 `AI 服务不可用（请确认 ai-service 已启动）`。

### 排查步骤

1. 确认 AI 服务启动：`curl http://localhost:8000/ai/health` 应返回 `{"status":"ok"}`。
2. 查看 AI 服务日志：`ai-service/server.log`，重点看是否有 import 错误或端口冲突。
3. 确认依赖已安装：`cd ai-service && .venv/Scripts/python -c "import fastapi, qdrant_client"`。
4. 若提示「请配置 API Key」：检查 `ai-service/.env` 是否包含 `LLM_API_KEY`，且服务启动时能读到（改 .env 后需重启 uvicorn）。

## 5. 上传文档后状态一直是 pending

### 现象

上传文档后，文档列表状态一直显示 pending，不流转到 processed。

### 排查步骤

1. 查看 doc-pipeline 消息是否投递：`docker exec knowledgeflow-redis redis-cli XRANGE doc-pipeline - +`。
2. 查看消费者是否消费：`docker exec knowledgeflow-redis redis-cli XPENDING doc-pipeline doc-pipeline-group`，若 pending 数持续增长说明消费者未工作。
3. 确认消费者线程在跑：后端日志应出现 `docPipelineContainer][消费者容器已启动`。
4. 确认 AI 服务可达：消费者会调 `POST /ai/ingest`，AI 不可达时文档会重试 3 次后置为 failed，此时查看文档的 error 字段定位原因。
5. 检查文档内容是否为空或类型不支持（仅支持 pdf/docx/txt/md）。

## 6. 中文乱码

### 现象

接口返回或页面显示中文乱码（`???` 或 `锟斤拷`）。

### 排查步骤

1. **命令行发请求乱码**：Windows 终端 curl 传中文默认 GBK 编码，后端按 UTF-8 解析会报 `Invalid UTF-8`。改用 Python 脚本发送（UTF-8 原生），或把 JSON 写入文件后 `curl -d @file.json`。
2. 页面显示乱码：检查前端是否设置了 UTF-8 字符集，Vite 默认 UTF-8。
3. 数据库乱码：确认建表字符集为 utf8mb4（本项目 DDL 已统一）。

## 7. 前端登录失败

### 现象

登录报「租户标识未传递」或「账号密码不正确」。

### 排查步骤

1. 「租户标识未传递」：请求需携带请求头 `tenant-id: 1`，前端封装 axios 时统一注入。
2. 「账号密码不正确」：演示账号为 `admin / admin123`（注意不是 123456）；若修改过密码，确认数据库 `system_users` 表中该用户状态为启用（status=0）。

## 8. MinIO / Qdrant 无法访问

### 现象

MinIO 控制台打不开，或 Qdrant 检索无结果。

### 排查步骤

1. MinIO 控制台：`http://localhost:9001`（账号 minioadmin/minioadmin）；API 端口 9000。
2. Qdrant 控制台：`http://localhost:6333/dashboard`；REST 端口 6333。
3. 容器未启动：`docker compose up -d` 重新拉起。
4. Qdrant 检索无结果但文档已 processed：确认 embedding 维度一致（本地降级 768 维 vs OpenAI 1536 维不兼容，切换模型需重建 collection）。

> 排查原则：先看服务是否活着（docker compose ps）→ 再看日志 → 最后看数据。不要一上来就重启全部服务。
