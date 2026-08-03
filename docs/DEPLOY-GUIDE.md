# 部署指南（新电脑 / 服务器）

> 小白可照做版：从零环境到系统跑起来，约 20-30 分钟（首次构建下载依赖较久）。

## 第 0 步：硬件与准备

- 内存 **8GB 以上（推荐 16GB）**，磁盘留 **20GB**
- 能上网；Windows / macOS / Linux 均可
- （可选）一个 DeepSeek API Key，用于 AI 问答（第 6 步，可后补）

## 第 1 步：安装环境（只需 2 个软件）

### ① Git

- **检测**：终端输入 `git --version`，有版本号 = 已装
- **未安装**：https://git-scm.com/downloads 下载安装（一路 Next）

### ② Docker

- **检测**：终端输入 `docker --version` 和 `docker info`，正常输出 = 已装
- **Windows 未安装**：
  1. 下载 https://www.docker.com/products/docker-desktop/
  2. 安装勾选 **Use WSL 2**，装完**重启电脑**
  3. 打开 Docker Desktop，等右下角鲸鱼图标**变绿**（提示 WSL 更新就按提示装）
- **macOS 未安装**：同样下载 Docker Desktop for Mac
- **Linux 未安装**：`sudo apt install docker.io docker-compose-plugin` + `sudo systemctl enable docker`

## 第 2 步：克隆项目

```bash
git clone https://github.com/shanhuhai12138/KnowledgeFlow-AI.git
cd KnowledgeFlow-AI
```

> 💡 `git clone` 会自动创建 `KnowledgeFlow-AI` 文件夹并把整个项目（含 `deploy`、`backend`、`frontend` 等）下载进去，**不用手动建任何文件夹**。执行完 `cd KnowledgeFlow-AI` 进入它即可。

## 第 3 步：配置环境变量（默认值即可跑）

```bash
cd deploy
cp .env.example .env      # Windows 用：copy .env.example .env
```

> `.env` 内含 MySQL/Redis/密钥配置。默认端口如与本地冲突，改这里（见第 7 步）。

## 第 4 步：一键启动（首次 5-15 分钟）

```bash
cd deploy
docker compose up -d --build
docker compose ps         # 等 7 个服务全部 (healthy)
```

## 第 5 步：打开系统

- 浏览器访问 **http://localhost:8080**
- 账号 **admin / admin123**（登录页有"一键填入"）
- 登录即有预置「软件开发团队知识库」+ 5 篇演示文档 + 金庸人物成员，开箱即演示

## 第 6 步：配置 AI（可选，问答才需要）

1. https://platform.deepseek.com 注册申请 API Key（新用户送额度）
2. 系统内：右上角头像 → **AI 设置** → 粘贴 Key → 保存 → **测试连接**
3. 不配 Key 不影响：上传文档 / 语义检索 / 看板都正常，仅问答提示"请配置 API Key"

## 第 7 步：常见问题

| 问题 | 解决 |
|------|------|
| 端口被占用（3306/6379 冲突） | 改 `deploy/.env` 端口映射（如 `3307:3306`），并同步改后端配置 |
| Docker Desktop 打不开 | 重启 Docker Desktop；BIOS 开启虚拟化；Windows 装 WSL2 更新包 |
| 首次 build 慢 / 拉镜像失败 | 正常现象；可给 Docker 配置国内镜像加速器 |
| 提问答不上 / 没引用 | 先到「文档管理」上传文档，等状态变「已就绪」再问 |
| 数据会不会丢 | 不会——数据在 Docker 命名卷（MySQL/MinIO/Qdrant/Redis），`docker compose down` 不删；**只有 `down -v` 才清空** |
| 对话清空 | 「清空对话」真实删除（前端内存 + 本地缓存），后端不存对话，长期使用不堆积 |
| 长期运行会不会堆积 | 不会——每日自动清理查询日志（30 天前）、Redis 队列、文档旧版本 |

## 开发模式（可选，改代码时用）

```bash
# 后端（本机需 JDK 21 + Maven）
cd backend && mvn install -DskipTests -pl yudao-server -am && java -jar yudao-server/target/yudao-server.jar

# AI 服务（本机需 Python 3.11）
cd ai-service && pip install -r requirements.txt && uvicorn main:app --port 8000

# 前端
cd frontend && npm install && npm run dev   # 打开 http://localhost:5173
```
