-- ============================================================
-- KnowledgeFlow AI — 文档模块表（任务 T2.3）
-- 在项目书 §6 表结构基础上补充若依多租户支撑列（延续 01-kb-tables.sql 规范）
-- ============================================================

CREATE TABLE IF NOT EXISTS `kb_document` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '文档编号',
  `kb_id` BIGINT NOT NULL COMMENT '知识库编号',
  `uploader_id` BIGINT NOT NULL COMMENT '上传者用户编号',
  `filename` VARCHAR(500) NOT NULL COMMENT '文件名',
  `object_name` VARCHAR(1000) NOT NULL COMMENT 'MinIO 对象键',
  `file_type` VARCHAR(10) NOT NULL COMMENT '文件类型：pdf/docx/txt/md',
  `file_size` BIGINT COMMENT '文件大小（字节）',
  `page_count` INT COMMENT '页数（解析后回填）',
  `status` VARCHAR(20) DEFAULT 'pending' COMMENT '状态：pending/processing/processed/failed',
  `tags` VARCHAR(1000) COMMENT '标签（逗号分隔）',
  `chunk_count` INT DEFAULT 0 COMMENT '分块数量（处理后回填）',
  `error` VARCHAR(1000) DEFAULT NULL COMMENT '处理失败原因（T2.5 死信记录）',
  `version` INT DEFAULT 1 COMMENT '版本号',
  `tenant_id` BIGINT NOT NULL DEFAULT 0 COMMENT '多租户编号',
  `creator` VARCHAR(64) DEFAULT '' COMMENT '创建者',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` VARCHAR(64) DEFAULT '' COMMENT '更新者',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` BIT(1) DEFAULT b'0' COMMENT '是否删除',
  KEY `idx_kb_id` (`kb_id`),
  KEY `idx_status` (`status`),
  KEY `idx_tenant_id` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库文档';

CREATE TABLE IF NOT EXISTS `kb_document_version` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '版本记录编号',
  `document_id` BIGINT NOT NULL COMMENT '文档编号',
  `object_name` VARCHAR(1000) NOT NULL COMMENT 'MinIO 对象键',
  `file_size` BIGINT COMMENT '文件大小',
  `content_hash` VARCHAR(64) COMMENT '内容哈希',
  `version` INT NOT NULL COMMENT '版本号',
  `created_by` BIGINT COMMENT '创建者用户编号',
  `tenant_id` BIGINT NOT NULL DEFAULT 0 COMMENT '多租户编号',
  `creator` VARCHAR(64) DEFAULT '' COMMENT '创建者',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` VARCHAR(64) DEFAULT '' COMMENT '更新者',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` BIT(1) DEFAULT b'0' COMMENT '是否删除',
  KEY `idx_document_id` (`document_id`),
  KEY `idx_tenant_id` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库文档版本历史';
