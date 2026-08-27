# KnowledgeFlow-AI 面试追问弹药库

## 检索

**Q: RRF 公式为什么是 1/(k+rank)？k=60 怎么来的？**
A: 按倒数排名融合避免不同检索器分数量纲不可比的问题；k 是平滑常数，越大越弱化头部排名差异。60 出自 TREC-COVID 等评测的经验值，论文(Cormack 2009)中 1%~11% 影响很小，工程上直接取默认。

**Q: 为什么 BM25 分数要 ×100？**
A: BM25 原始分数无上界且量纲和余弦相似度(0~1)不可比。前端展示统一为 0-100 可读性更好；融合排序本身用 RRF 不受影响，这个只影响展示层。——诚实答：这是我当时的一个权衡，更好的做法是分别归一化后再加权。

**Q: dense 命中了但 BM25 也命中的文档谁排前面？**
A: 看 RRF 分数之和。两路都命中说明两种证据一致，天然排前。我的评测里这类 query 基本 rank=1。

**Q: jieba 前后有什么变化？**
A: 原来中文按单字切，召回靠字面重叠运气；jieba 词粒度切分后 MRR@5 从 0.626 提到 0.650，Recall@5 保持 94%。代价是首次加载 ~700ms 初始化词典，稳态毫秒级。

**Q: 没有 rerank 为什么还敢说效果好？**
A: 效果是用 20 条人工标注 query 的 Recall@5/MRR@5 验证的，不是感觉。数据集规模小是局限，但方法论是对的——这也是我下一步加 bge-reranker 时衡量收益的基线。

## 后端工程

**Q: Redis Streams 为什么用 Consumer Group 不用普通 List？**
A: Group 提供 XACK 确认与 PEL 待处理列表，消费者崩溃后消息可重新投递（XAUTOCLAIM），List 的 LPOP 是取出即丢。文档解析是幂等的（documentId 先删旧向量），但"至少一次"仍比"可能丢失"正确。

**Q: 消息重复消费怎么办？**
A: 幂等设计兜底：ingest 前 delete_by_document(documentId)，同一文档重放不产生脏数据。严格 exactly-once 需要 Redis 事务或业务去重表，当前成本收益不划算。

**Q: SSE 和 WebSocket 为什么选 SSE？**
A: 单向推送够用（服务端→客户端流式 token）；SSE 基于 HTTP 天然过网关/反代，自动重连浏览器原生支持；WebSocket 双向能力用不上还要处理心跳、升级协议。

**Q: Nginx 反代 SSE 要注意什么？**
A: proxy_buffering off（否则 nginx 攒缓冲导致前端长时间无输出）、read_timeout 拉长到 300s、HTTP/1.1 + Connection ""。这是我实际踩过的坑。

## 多租户与安全

**Q: 多租户隔离怎么做的？**
A: 两层——脚手架 biz-tenant starter 在 MyBatis 层自动拼 tenant_id 条件；知识库层还有 kb 成员角色（ADMIN/EDITOR/VIEWER）做业务权限。请求头 tenant-id 标识租户。

**Q: API Key 明文存库吗？**
A: 不是。用户在前端"AI 设置"页配置的 LLM Key 用 AES 加密落库，解密只在 AI 服务调用瞬间发生。（framework/aes）

## AI 协同开发（灵魂拷问区）

**Q: 项目大量用了 AI 辅助，你怎么保证代码质量？**
A: 三道闸——①任务拆小：每个模块契约先行（接口 JSON schema 定义好再让 AI 实现）；②测试兜底：核心算法（意图识别/BM25）有 pytest 单测，CI 强制通过；③我自己做 code review：本轮修混合检索 bug 时发现 AI 生成的 hybrid 分支把裸 QdrantClient 当 retriever 传进去，这种"看起来对但不能跑"的问题只有真正读过代码才能抓出来。另外我把排查过程写成了 eval 数据集，用数字说话。

**Q: 你这项目基于芋道脚手架，哪些是你自己写的？**
A: 脚手架提供的是用户/权限/代码生成等基建；知识库领域模块（KB CRUD、文档管道、检索代理、统计分析 56 个类）和整个 Python AI 服务（RAG 三路检索、LangGraph 编排、SSE）是我从设计到实现完成的，包括这次的检索修复和监控接入。架构决策上我能讲清楚每一个自研模块为什么这样分层。
