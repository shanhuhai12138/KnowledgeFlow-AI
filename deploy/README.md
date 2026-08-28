# 新机器部署指引（Fresh Machine Checklist）

> 目标：在一台全新的电脑上，从 clone 到全功能可用。
> 前置要求：Docker Desktop（或 Docker Engine + Compose v2）、网络可访问 Docker Hub / PyPI / Maven Central。
> 内存建议 ≥ 8GB（构建 backend 时 Maven 较吃内存）。

## 一、标准流程（三步）

```bash
# 1. 克隆
git clone https://github.com/shanhuhai12138/KnowledgeFlow-AI.git
cd KnowledgeFlow-AI/deploy

# 2. 准备环境变量（默认值即可跑，无需改任何密码）
cp .env.example .env          # Windows: copy .env.example .env

# 3. 一键构建并启动（首次会构建 3 个镜像，约 10–40 分钟视网络）
docker compose up -d --build

# 查看状态（全部 healthy 即就绪；backend 首次启动约 30–60s）
docker compose ps
```

## 二、首次启动会发生什么

| 阶段 | 行为 | 耗时占比 |
|---|---|---|
| ai-service 镜像 | pip 安装含 torch/sentence-transformers（~2GB 下载） | 最大头 |
| backend 镜像 | 容器内 Maven 全量构建（拉取依赖） | 次之 |
| frontend 镜像 | npm ci + vite build | 较快 |
| MySQL 首启 | 自动执行 seed/mysql-init/*.sql（建表 + admin 账号 + 演示知识库） | 秒级 |
| seed 容器 | 调真实 /ai/ingest 把 5 篇演示文档走完整分块→向量化→Qdrant 入库 | 1–2 分钟 |

## 三、启动后访问入口

- 前端：<http://localhost:8080>（登录 admin / admin123）
- 后端 API：<http://localhost:48080>　Swagger：<http://localhost:48080/doc.html>
- AI 服务：<http://localhost:8000/docs>
- Grafana：<http://localhost:3000>（admin / admin）　Prometheus：<http://localhost:9090>
- MinIO 控制台：<http://localhost:9001>（minioadmin / minioadmin）

## 四、LLM 能力开启（问答/Agent 需要）

默认容器未带大模型 Key，登录后两种方式二选一：

1. **界面配置（推荐）**：登录 → 「AI 设置」页 → 填入 DeepSeek API Key（AES 加密落库，即时生效）
2. **环境变量**：编辑 `deploy/.env` 的 `LLM_API_KEY` / `LLM_MODEL` → `docker compose up -d ai-service` 重建

不配置时：登录/文档管理/检索等全部功能可用，仅"问答生成/Agent 报告"会提示需配置 Key。

## 五、常见问题排查

| 症状 | 原因 | 处理 |
|---|---|---|
| frontend / nginx 反复重启 | 偶发 DNS 竞态（已加 restart 策略兜底） | `docker compose restart frontend nginx`，一般自动恢复 |
| backend 一直 starting | 首启初始化 SQL 未完成 | `docker compose logs backend -f` 等 Started 字样 |
| 登录报"账号未登录" | 请求没带 tenant-id 头（前端已内置） | 确认访问的是 8080 前端而非直连后端 |
| 构建时 pip 超时 | 无代理且直连 PyPI 慢 | Dockerfile 的 pip 行已注释备用阿里云源，按需切换 |
| 上传文档无反应 | MinIO/Redis 未 healthy | `docker compose ps` 看哪个容器异常，看对应 logs |
| 端口冲突（3307/6380/8080 被占） | 本机已有同名服务 | 改 compose 左侧宿主端口映射 |

## 六、数据持久化与重置

- 数据全部在 named volumes（mysql_data / qdrant_data / minio_data / redis_data）
- `docker compose down` 保留数据；`docker compose down -v` **清空全部数据重来**
