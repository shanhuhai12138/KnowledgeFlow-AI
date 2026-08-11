# KnowledgeFlow AI — CHANGELOG

## [1.0.0] — 2026-08-04

### 新增
- 企业级知识管理与 RAG 智能问答平台正式上线
- 文档上传 → 分块 → 向量化 → 语义检索 → 流式问答（SSE）完整链路
- LangGraph Agent 工作流（检索 → 摘要 → 分类 → 报告，含 human-in-the-loop）
- 多租户知识库 + 成员角色管理（ADMIN/EDITOR/VIEWER）
- 分析看板（文档统计、搜索趋势、热门文档、LLM Token 消耗）
- Docker Compose 一键部署（8 个服务：MySQL/Redis/MinIO/Qdrant/后端/AI/Nginx/前端）
- 前端「AI 设置」页：在线配置 LLM API Key（AES 加密存储）
- 编辑社论风设计体系（Noto Serif SC + Inter，深墨蓝强调色）

### 修复
- 品牌脱敏：所有 `yudao`/`ruoyi`/`iocoder` 引用替换为 `knowledgeflow`
- 修复 agent_graph.py 类型注解语法错误（`_step` 返回类型修正）
- 修复 CORS 配置：支持环境变量动态配置生产来源
- 补齐 Nginx 反代服务（`/api`/`/ai`/`/` 统一路由）
- 补齐 requirements.txt 缺失依赖（langchain-core、langgraph-checkpoint 等）
- README 重写：去除低俗表达，修正 Spring Boot 版本描述，补充安全提示
- 修复 SSE URL 拼接问题（API_BASE 空串注入）
- 修复 MySQL 初始化中文乱码（SET NAMES utf8mb4）

### 优化
- 版本号统一为 `1.0.0`
- LICENSE 移至仓库根目录
- 删除冗余的 `yudao-ui` 目录（RuoYi 默认后台 UI，与 Vue3 前端重复）
- 清理 pom.xml 中注释掉的未实现模块
- 更新 .gitignore 覆盖构建产物和密钥文件
- 部署指南补充新电脑/服务器小白版说明

---

