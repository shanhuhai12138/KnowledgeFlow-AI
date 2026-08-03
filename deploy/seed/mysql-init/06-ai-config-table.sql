-- ============================================================
-- KnowledgeFlow AI — T7 API Key 管理表（DR-13 开源化前置）
-- 部署者在界面填模型 API Key（AES 加密存储），不改配置文件
-- ============================================================

CREATE TABLE IF NOT EXISTS `ai_api_config` (
  `id` BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '配置编号',
  `config_key` VARCHAR(50) NOT NULL COMMENT '配置键（llm）',
  `config_value` VARCHAR(2000) COMMENT 'AES 加密的 API Key',
  `base_url` VARCHAR(500) COMMENT 'API 地址（如 https://api.deepseek.com）',
  `model` VARCHAR(100) COMMENT '模型名',
  `tenant_id` BIGINT NOT NULL DEFAULT 0 COMMENT '多租户编号',
  `creator` VARCHAR(64) DEFAULT '' COMMENT '创建者',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updater` VARCHAR(64) DEFAULT '' COMMENT '更新者',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` BIT(1) DEFAULT b'0' COMMENT '是否删除',
  UNIQUE KEY `uk_config_key_tenant` (`config_key`, `tenant_id`, `deleted`),
  KEY `idx_tenant_id` (`tenant_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI 配置（API Key 管理）';
