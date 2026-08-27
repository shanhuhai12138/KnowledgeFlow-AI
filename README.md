# KnowledgeFlow-AI

企业级 RAG 知识库系统 · 智能问答 · Agent 工作流

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.x-green.svg)](https://vuejs.org/)
[![Java](https://img.shields.io/badge/Java-17+-red.svg)](https://java.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-black.svg)](https://www.docker.com/)

---

## 功能特性

- **智能问答**：基于 RAG 的语义检索，支持多轮对话和来源引用
- **Agent 工作流**：多步骤分析流程，含人工确认节点
- **混合检索**：Dense + BM25 + Hybrid 三种检索模式，智能推荐
- **文档管理**：支持 PDF/DOCX/TXT/MD 格式，自动分块向量化
- **知识库管理**：多知识库隔离，细粒度权限控制
- **监控**：Prometheus + Grafana 实时监控
- **CI/CD**：GitHub Actions 自动化构建

---

## 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Element Plus |
| 后端 | Spring Boot 2.7 + Java 17 |
| AI 服务 | Python FastAPI + LangGraph |
| 向量库 | Qdrant |
| 对象存储 | MinIO |
| 缓存 | Redis |
| 数据库 | MySQL 8.0 |
| 部署 | Docker Compose |

---

## 快速开始

### 环境要求

- Docker 20.10+
- Docker Compose v2+
- 8GB+ 内存

### 启动服务

```bash
# 克隆项目
git clone https://github.com/shanhuhai12138/KnowledgeFlow-AI.git
cd KnowledgeFlow-AI

# 启动所有服务
cd deploy
docker-compose up -d

# 查看状态
docker-compose ps
```

### 访问地址

- 前端：http://localhost:8080
- 后端 API：http://localhost:48080
- AI 服务：http://localhost:8000
- Swagger：http://localhost:8080/swagger-ui.html
- MinIO：http://localhost:9001（admin/admin123456）
- Grafana：http://localhost:3001（admin/admin）

### 默认账号

- 管理员：`admin` / `[REDACTED]`

---

## 核心功能说明

### 智能问答

支持自然语言查询，自动检索相关知识库文档并生成回答。

```bash
# API 调用示例
curl -X POST http://localhost:8000/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "如何搭建开发环境？",
    "kbId": 1,
    "sessionId": "session_001"
  }'
```

### Agent 工作流

多步骤文档分析流程，支持人工确认节点。

```bash
# 启动 Agent 工作流
curl -X POST http://localhost:8000/ai/agent \
  -H "Content-Type: application/json" \
  -d '{
    "query": "分析 Q3 销售数据",
    "kbId": 1
  }'
```

### 检索模式

系统支持三种检索模式，可根据查询类型自动推荐：

| 模式 | 适用场景 | 示例查询 |
|------|---------|---------|
| Dense（向量） | 自然语言、概念匹配 | "如何搭建开发环境？" |
| BM25（关键词） | 日期、版本、数值查询 | "2026年8月21日的版本号" |
| Hybrid（混合） | 复杂分析任务 | "分析本月销售数据" |

---

## 项目结构

```
KnowledgeFlow-AI/
├── backend/          # Spring Boot 后端
├── frontend/         # Vue 3 前端
├── ai-service/       # Python AI 服务
├── deploy/           # Docker 部署配置
├── docs/             # 项目文档
└── scripts/          # 辅助脚本
```

---

## 开发指南

### 本地开发

```bash
# 后端
cd backend
mvn spring-boot:run

# 前端
cd frontend
npm install
npm run dev

# AI 服务
cd ai-service
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 测试

```bash
# 后端单元测试
cd backend
mvn test

# AI 服务测试
cd ai-service
pytest tests/ -v
```

---

## API 文档

- Swagger UI：http://localhost:8080/swagger-ui.html
- AI 服务 Docs：http://localhost:8000/docs

---

## 监控与告警

- Prometheus：http://localhost:9090
- Grafana：http://localhost:3001
- 监控指标：deploy/prometheus/prometheus.yml

---

## 常见问题

### 1. 服务启动失败

```bash
# 查看日志
docker-compose logs -f <service-name>

# 重启服务
docker-compose restart <service-name>
```

### 2. 文档上传失败

检查 MinIO 存储空间和 AI 服务连接状态。

### 3. 检索结果为空

确认文档已正确分块并向量化，检查 Qdrant 集合状态。

---

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 许可证

[MIT License](LICENSE)

---

## 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)
