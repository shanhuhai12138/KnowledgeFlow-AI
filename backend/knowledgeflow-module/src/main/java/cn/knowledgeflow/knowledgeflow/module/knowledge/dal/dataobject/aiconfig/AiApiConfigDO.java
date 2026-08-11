package cn.knowledgeflow.module.knowledge.dal.dataobject.aiconfig;

import cn.knowledgeflow.framework.tenant.core.db.TenantBaseDO;
import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * AI 配置 DO（T7：API Key 管理，DR-13 开源化）
 *
 * config_value 为 AES 加密后的 Key，永不返回明文。
 */
@TableName("ai_api_config")
@KeySequence("ai_api_config_seq")
@Data
@EqualsAndHashCode(callSuper = true)
public class AiApiConfigDO extends TenantBaseDO {

    /**
     * 配置编号
     */
    private Long id;
    /**
     * 配置键（llm）
     */
    private String configKey;
    /**
     * AES 加密的 API Key
     */
    private String configValue;
    /**
     * API 地址
     */
    private String baseUrl;
    /**
     * 模型名
     */
    private String model;

}
