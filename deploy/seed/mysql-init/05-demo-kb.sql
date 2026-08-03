SET NAMES utf8mb4;

-- ============================================================
-- KnowledgeFlow AI — T5 演示种子数据（幂等，可重复执行）
-- 演示库：软件开发团队知识库（共享）+ 5 篇示例文档（status=processed 预置）
-- 说明：Qdrant 向量由 deploy/seed/run_seed.py 走真实 /ai/ingest 灌入（禁止伪造向量）
-- ============================================================

-- 1. 演示知识库（id=1：已存在则更新为共享并重置计数，保证幂等）
INSERT INTO `kb_knowledge_base`
  (`id`, `name`, `description`, `is_private`, `owner_id`, `document_count`, `member_count`,
   `tenant_id`, `creator`, `create_time`, `update_time`, `updater`, `deleted`)
VALUES
  (1, '软件开发团队知识库',
   '团队共享的研发资料：开发环境搭建、代码规范与评审、微服务架构设计、故障排查与季度复盘。',
   0, 1, 5, 0, 1, '1', NOW(), NOW(), '1', b'0')
ON DUPLICATE KEY UPDATE
  `name` = VALUES(`name`),
  `description` = VALUES(`description`),
  `is_private` = 0,
  `document_count` = 5,
  `tenant_id` = 1,
  `deleted` = b'0';

-- 2. 演示文档（固定 id 9001-9005 避免与既有数据冲突；重复执行时更新元数据，保证幂等）
INSERT INTO `kb_document`
  (`id`, `kb_id`, `uploader_id`, `filename`, `object_name`, `file_type`, `file_size`,
   `page_count`, `status`, `tags`, `chunk_count`, `version`,
   `tenant_id`, `creator`, `create_time`, `update_time`, `updater`, `deleted`)
VALUES
  (9001, 1, 1, '开发环境搭建SOP.md', '开发环境搭建SOP.md', 'md', 0, 0, 'processed', 'SOP,环境搭建', 0, 1, 1, '1', NOW(), NOW(), '1', b'0'),
  (9002, 1, 1, '代码规范与评审流程.md', '代码规范与评审流程.md', 'md', 0, 0, 'processed', '规范,评审', 0, 1, 1, '1', NOW(), NOW(), '1', b'0'),
  (9003, 1, 1, '微服务架构设计文档.md', '微服务架构设计文档.md', 'md', 0, 0, 'processed', '架构,设计', 0, 1, 1, '1', NOW(), NOW(), '1', b'0'),
  (9004, 1, 1, '故障排查FAQ.md', '故障排查FAQ.md', 'md', 0, 0, 'processed', 'FAQ,排查', 0, 1, 1, '1', NOW(), NOW(), '1', b'0'),
  (9005, 1, 1, '季度技术复盘.md', '季度技术复盘.md', 'md', 0, 0, 'processed', '复盘,总结', 0, 1, 1, '1', NOW(), NOW(), '1', b'0')
ON DUPLICATE KEY UPDATE
  `kb_id` = VALUES(`kb_id`),
  `filename` = VALUES(`filename`),
  `object_name` = VALUES(`object_name`),
  `file_type` = VALUES(`file_type`),
  `status` = 'processed',
  `tags` = VALUES(`tags`),
  `tenant_id` = 1,
  `deleted` = b'0';
