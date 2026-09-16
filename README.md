# KnowledgeFlow-AI

全栈 RAG 知识库与 Agent 工作流系统 · 智能问答 · 检索质量评测

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.x-green.svg)](https://vuejs.org/)
[![Java](https://img.shields.io/badge/Java-17+-red.svg)](https://java.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-black.svg)](https://www.docker.com/)

---

## 功能特性

- **智能问答**：基于 RAG 的语义检索，支持多轮对话和来源引用
- **Agent 工作流**：LangGraph 多节点图（检索 → 摘要 → 分类 → 人工确认 → 报告，检索无结果走直接回答分支），步骤级可观测（SSE 事件流 + 每步耗时）
- **混合检索**：Dense + BM25(jieba) 双路召回、RRF 融合；意图识别自动推荐检索模式
- **文档管理**：PDF/DOCX/TXT/MD 解析分块，Redis Streams 异步管道（ack / 重试 / 死信 / 幂等）
- **知识库管理**：多知识库隔离（kbId 过滤 + 框架级租户字段），成员角色管理（ADMIN/EDITOR/VIEWER）
- **检索质量评测**：20+2 条标注集，Recall@5 / MRR@5 / 延迟 / 负样本误触四指标，一键重跑
- **监控**：轻量业务指标（/metrics 请求计数）+ Prometheus + Grafana
- **CI**：GitHub Actions（Python 单测 + 评测指标自检 + 前端测试 + 后端构建）

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
- Grafana：http://localhost:3000（admin/admin）

### 默认账号

- 管理员：`admin` / `admin123`

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

### 检索质量评测（可复现）

所有对外指标数字均有存档出处，可一键重跑：

```bash
cd ai-service
# 在线评测（docker compose up + seed 灌入后）
python tests/eval_retrieval.py --output tests/eval_results/my_run.json
# 离线重放 BM25（无需服务）：--tokenizer regex 为 jieba 升级前基线
python tests/eval_retrieval.py --offline --tokenizer regex
```

最近一次存档（2026-09-16，local hash 嵌入，详见 `ai-service/tests/eval_results/README.md`）：

| 模式 | Recall@5 | MRR@5 |
|------|---------|-------|
| Dense | 94.4% | 0.801 |
| BM25 | 94.4% | 0.650 |
| Hybrid（RRF） | **100%** | 0.574 |

jieba 分词升级收益（离线基线重放对比）：MRR@5 0.618 → 0.648，负样本误触 2/2 → 1/2。

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
- Grafana：http://localhost:3000
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

## 能力边界与 Roadmap

本项目是个人独立开发的全栈演示系统，诚实标注当前边界：

- **租户与权限**：租户隔离依赖脚手架框架层（TenantLineHandler 自动过滤）；知识库级成员角色尚未在 service 层强制校验（当前仅全局 Key 配置有 super_admin 校验）→ Roadmap：成员角色 service 层强制
- **Agent 运行时**：run 状态为进程内存存储，重启丢失；HITL 为线程轮询而非 checkpointer → Roadmap：MemorySaver → SqliteSaver 持久化（见 docs/interview-langgraph-hitl.md）
- **监控深度**：仅请求计数与 uptime，无延迟直方图/业务维度 → Roadmap：prometheus-client 直方图
- **评测规模**：20+2 条标注集，小而可复现；不宣称大规模基准
- **Java 测试**：后端 CI 仅构建不跑单测（现有 3 个枚举测试）→ Roadmap：领域层单测补齐

## 与脚手架的关系

后端基于芋道（ruoyi/yudao 系）开源脚手架二次开发，品牌已全面替换；知识库领域模块（56 个 Java 类）为二次开发产出，其中 CRUD 骨架来自代码生成器，文档管道 / 成员 / 统计 / AI 转发为自研逻辑。

---

## 许可证

[MIT License](LICENSE)

---

## 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)
