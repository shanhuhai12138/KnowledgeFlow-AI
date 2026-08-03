# 开发环境搭建 SOP

> 适用于团队新成员入职第一天，快速搭建本地开发环境。本文档覆盖 JDK、Maven、MySQL、Redis、Docker、后端与 AI 服务的完整安装配置步骤。

## 1. 安装 JDK 21

1. 下载 JDK 21 LTS（Oracle 或 Eclipse Temurin 发行版均可），选择 Windows x64 安装包。
2. 安装完成后配置环境变量：
   - 新建系统变量 `JAVA_HOME`，值为 JDK 安装目录（例如 `D:\Program Files\Java\jdk-21.0.10`）。
   - 编辑 `Path` 变量，追加 `%JAVA_HOME%\bin`。
3. 打开新的命令行窗口验证：`java -version`，应输出 `java version "21.0.10"` 之类的信息。
4. 常见问题：如果 `java` 命令提示"不是内部或外部命令"，说明 `Path` 配置错误或未重开终端；如果同时安装了多个 JDK，请检查 `JAVA_HOME` 是否指向 21 版本。

## 2. 安装 Maven

1. 下载 Apache Maven 3.9.x 二进制包，解压到本地目录（例如 `C:\Program Files (x86)\apache-maven-3.9.16`）。
2. 配置环境变量：
   - 新建 `MAVEN_HOME` 指向解压目录。
   - `Path` 追加 `%MAVEN_HOME%\bin`。
3. 验证：`mvn -version`，应显示 Maven 版本与 Java 版本。
4. 配置阿里云镜像加速依赖下载：在 `conf/settings.xml` 的 `<mirrors>` 节点添加镜像，或使用默认的 aliyunmaven 镜像。
5. 首次构建项目时 Maven 会下载大量依赖，请保持网络畅通，耐心等待即可。

## 3. 安装并配置 MySQL

1. 本机若已安装 MySQL 并占用 3306 端口，**无需卸载**——项目通过 Docker 运行独立 MySQL 实例。
2. 使用 Docker 启动 MySQL 8：
   ```bash
   docker run -d --name knowledgeflow-mysql -p 3307:3306 \
     -e MYSQL_ROOT_PASSWORD=knowledgeflow -e MYSQL_DATABASE=knowledgeflow \
     mysql:8
   ```
3. 说明：宿主端口映射为 `3307`，是因为本机 3306 已被本机 MySQL 占用；容器内端口保持 3306 不变。
4. 后端数据源连接串为 `jdbc:mysql://localhost:3307/knowledgeflow`，账号 `knowledgeflow`，密码 `knowledgeflow`（开发默认值，可在 `deploy/.env` 中修改）。

## 4. 安装并配置 Redis

1. 若本机 6379 已被占用，同样通过 Docker 启动独立 Redis：
   ```bash
   docker run -d --name knowledgeflow-redis -p 6380:6379 redis:7-alpine
   ```
2. 验证连通性：`redis-cli -p 6380 ping` 应返回 `PONG`。
3. 后端与前端统一使用 `localhost:6380` 作为 Redis 连接地址。
4. Redis 在本项目中的用途：缓存、以及文档处理流水线的 Streams 消息队列（`doc-pipeline`）。

## 5. 启动基础设施

1. 项目根目录 `deploy/` 下执行：
   ```bash
   cp .env.example .env
   docker compose up -d
   ```
2. 该命令会启动 MySQL、Redis、MinIO（对象存储）、Qdrant（向量数据库）四个服务。
3. 验证四个服务均 healthy：`docker compose ps`，状态列应全部为 `healthy`。
4. MinIO 控制台地址 `http://localhost:9001`（默认账号 minioadmin/minioadmin），Qdrant 控制台 `http://localhost:6333/dashboard`。

## 6. 启动后端服务

```bash
cd backend
mvn install -DskipTests -pl yudao-server -am   # 首次构建依赖模块
java -jar yudao-server/target/yudao-server.jar # 启动，监听 48080
```

1. 后端默认账号 `admin / admin123`，登录需携带请求头 `tenant-id: 1`。
2. 接口文档（Knife4j）：浏览器打开 `http://localhost:48080/doc.html`。
3. 数据源与 Redis 已在 `application-local.yaml` 中指向 compose 服务，无需额外配置。

## 7. 启动 AI 服务

```bash
cd ai-service
python -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

1. AI 服务提供文档向量化（`/ai/ingest`）、语义检索（`/ai/search`）、流式问答（`/ai/chat/stream`）与 Agent 工作流（`/ai/agent`）。
2. API 文档：`http://localhost:8000/docs`。
3. LLM 配置在 `ai-service/.env`：`LLM_API_KEY` 与 `LLM_MODEL`（默认 DeepSeek）。

## 8. 启动前端

```bash
cd frontend
npm install
npm run dev
```

1. 前端开发服务器默认 `http://localhost:5173`，通过 Vite 代理转发 `/admin-api` 到后端 48080、`/ai` 到 8000。
2. 登录后即可上传文档、提问与查看看板。

## 9. 自检清单

- [ ] `docker compose ps` 四个服务 healthy
- [ ] `http://localhost:48080/doc.html` 可打开 Knife4j
- [ ] `http://localhost:8000/docs` 可打开 FastAPI 文档
- [ ] 前端 `http://localhost:5173` 可登录并进入系统
- [ ] 上传一篇 PDF 后，文档状态能从 pending 自动流转到 processed

> 遇到任何一步失败，先查看对应服务的日志：后端日志在 `yudao-server/server.log`，AI 服务日志在 `ai-service/server.log`；端口占用问题参考《故障排查 FAQ》。
