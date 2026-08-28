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

## 七、版本更新与数据安全（git pull 之后怎么办）

### 数据边界：git 里有 Code，没有 Data

| 位置 | 内容 | 会被推送吗 |
|---|---|---|
| git 仓库 | 源码、建表 SQL、演示种子（1 个共享演示库 + 5 篇示例文档）、.env.example | ✅ 会 |
| Docker 数据卷 | mysql_data（知识库/文档/查询日志）、qdrant_data（向量）、minio_data（上传文件）、redis_data、prometheus_data、grafana_data | ❌ 不会，只在本机 |

你上传的真实文档、向量、查询日志全部在本机 Docker 卷里，git 感知不到；
别人克隆拿到的是代码 + 空卷，首次启动自动初始化出他们自己的数据世界。

### 更新操作对照表（upstream 更新后如何跟进）

| 上游改了什么 | 你要执行的命令 | 你的数据 |
|---|---|---|
| 仅文档 / README | `git pull` | 无损 |
| Python / Java / Vue 代码 | `git pull` → `docker compose build ai-service backend frontend` → `docker compose up -d` | 无损，数据照旧 |
| compose / nginx / prometheus 配置 | `git pull` → `docker compose up -d`（自动重建受影响容器） | 无损 |
| SQL 建表脚本（01~06-*.sql） | 先 `git pull`；无破坏性变更时重启即生效；**有新表/新列时**手工执行增量 SQL（进容器 mysql 执行） | ⚠️ 切勿直接 `down -v` |
| `.env` 的 CONFIG_SECRET 变更 | 重启后需在「AI 设置」页重新填一次 LLM Key（旧密文解不开） | 仅 AI Key 需重配 |

### 三条纪律

1. **更新前备份**（可选但推荐）：`docker run --rm -v knowledgeflow_mysql_data:/data -v %cd%:/backup mysql:8 tar czf /backup/mysql-backup.tgz /data`
2. **永远不要在生产数据上 `docker compose down -v`**——它清空全部卷，等于恢复出厂；这是"重置演示环境"用的
3. **保持 `05-demo-kb.sql` 为纯演示内容**——演示知识库（id=1）是给大家的公共起点，个人测试数据请上传到自建知识库，避免误提交真实内容进种子文件
