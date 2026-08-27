# Contributing to KnowledgeFlow-AI

感谢你对 KnowledgeFlow-AI 的关注和贡献！

## 开发环境搭建

### 前置要求

- Docker & Docker Compose
- Java 17+
- Node.js 20+
- Python 3.11+

### 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/shanhuhai12138/KnowledgeFlow-AI.git
cd KnowledgeFlow-AI

# 2. 启动基础设施
cd deploy
cp .env.example .env
# 编辑 .env 配置 LLM_API_KEY 等
docker compose up -d

# 3. 后端开发
cd ../backend
mvn spring-boot:run -pl knowledgeflow-server

# 4. 前端开发
cd ../frontend
npm install
npm run dev
```

## 提交代码

### 分支策略

- `main`: 主分支，保持稳定
- `feature/*`: 功能开发分支
- `fix/*`: 修复分支

### 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范:

```
feat: 添加新功能
fix: 修复 bug
docs: 更新文档
style: 代码格式调整
refactor: 重构代码
test: 添加测试
chore: 构建/工具链相关
```

### Pull Request 流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/your-feature`)
3. 提交更改 (`git commit -m 'feat: your change'`)
4. 推送到分支 (`git push origin feature/your-feature`)
5. 创建 Pull Request

## 代码规范

### 后端 (Java)

- 使用 Spring Boot 2.7.18 + Java 17
- 遵循阿里巴巴 Java 开发手册
- 单元测试覆盖率目标: >60%

### 前端 (Vue 3)

- 使用 TypeScript 严格模式
- 组件命名使用 PascalCase
- 使用 Pinia 进行状态管理

### Python (AI 服务)

- 使用 Python 3.11+
- 类型注解必须完整
- 遵循 PEP 8 规范

## 报告问题

请在 [GitHub Issues](https://github.com/shanhuhai12138/KnowledgeFlow-AI/issues) 中报告问题，包含:

- 问题描述
- 复现步骤
- 预期行为
- 实际行为
- 环境信息 (OS, Docker 版本等)

## 联系方式

- GitHub: [@shanhuhai12138](https://github.com/shanhuhai12138)
- Email: 2529602567@qq.com
