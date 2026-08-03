-- ============================================================
-- KnowledgeFlow AI — 搜索问答日志表（任务 T2.4）
-- 项目书 §6 kb_query_log + 多租户支撑列（延续 01/02 规范）
-- ============================================================

CREATE TABLE IF NOT EXISTS `kb_query_log` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '日志编号',
  `user_id` BIGINT COMMENT '用户编号',
  `kb_id` BIGINT COMMENT '知识库编号',
  `query_text` VARCHAR(500) COMMENT '查询内容',
  `took_ms` INT COMMENT '耗时（毫秒）',
  `hit_count` INT COMMENT '命中数量',
  `tenant_id` BIGINT NOT NULL DEFAULT 0 COMMENT '多租户编号',
  `creator` VARCHAR(64) DEFAULT '' COMMENT '创建者',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` VARCHAR(64) DEFAULT '' COMMENT '更新者',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` BIT(1) DEFAULT b'0' COMMENT '是否删除',
  KEY `idx_user_id` (`user_id`),
  KEY `idx_kb_id` (`kb_id`),
  KEY `idx_tenant_id` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='搜索问答日志';
