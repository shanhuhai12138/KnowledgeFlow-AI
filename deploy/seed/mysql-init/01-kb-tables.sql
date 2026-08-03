-- ============================================================
-- KnowledgeFlow AI — 知识库模块表（任务 T2.2）
-- 说明：在项目书 §6 表结构基础上补充若依多租户支撑列
--   tenant_id  : 多租户隔离（框架 TenantLineHandler 自动过滤，登录需带 tenant-id header）
--   creator/updater/deleted : 若依 BaseDO 标准列（逻辑删除 + 审计）
-- ============================================================

CREATE TABLE IF NOT EXISTS `kb_knowledge_base` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '知识库编号',
  `name` VARCHAR(255) NOT NULL COMMENT '知识库名称',
  `description` TEXT COMMENT '知识库描述',
  `is_private` TINYINT(1) DEFAULT 1 COMMENT '是否私有：1=私有（仅所有者/成员可见），0=共享（租户内可见）',
  `owner_id` BIGINT NOT NULL COMMENT '所有者用户编号',
  `document_count` INT DEFAULT 0 COMMENT '文档数量（冗余计数）',
  `member_count` INT DEFAULT 0 COMMENT '成员数量（冗余计数）',
  `tenant_id` BIGINT NOT NULL DEFAULT 0 COMMENT '多租户编号',
  `creator` VARCHAR(64) DEFAULT '' COMMENT '创建者',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` VARCHAR(64) DEFAULT '' COMMENT '更新者',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` BIT(1) DEFAULT b'0' COMMENT '是否删除',
  KEY `idx_tenant_id` (`tenant_id`),
  KEY `idx_owner_id` (`owner_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库';

CREATE TABLE IF NOT EXISTS `kb_member` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '成员记录编号',
  `kb_id` BIGINT NOT NULL COMMENT '知识库编号',
  `user_id` BIGINT NOT NULL COMMENT '用户编号',
  `role` VARCHAR(20) NOT NULL COMMENT '角色：ADMIN/EDITOR/VIEWER',
  `tenant_id` BIGINT NOT NULL DEFAULT 0 COMMENT '多租户编号',
  `creator` VARCHAR(64) DEFAULT '' COMMENT '创建者',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` VARCHAR(64) DEFAULT '' COMMENT '更新者',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` BIT(1) DEFAULT b'0' COMMENT '是否删除',
  UNIQUE KEY `uk_kb_user` (`kb_id`, `user_id`),
  KEY `idx_tenant_id` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库成员';
