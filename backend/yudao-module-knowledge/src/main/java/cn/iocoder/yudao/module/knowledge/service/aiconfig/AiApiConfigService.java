package cn.iocoder.yudao.module.knowledge.service.aiconfig;

import cn.iocoder.yudao.module.knowledge.controller.admin.aiconfig.vo.AiConfigRespVO;
import cn.iocoder.yudao.module.knowledge.controller.admin.aiconfig.vo.AiConfigSaveReqVO;

/**
 * AI 配置 Service（T7：API Key 管理）
 *
 * 保存的 Key 以 AES 加密存储，读取时解密注入转发层（DB 优先于环境变量）。
 */
public interface AiApiConfigService {

    /**
     * 获取配置（key 明文解密；无记录返回 null）
     */
    String getConfigValue(String configKey);

    /**
     * 保存/更新配置（apiKey 为空 = 清除 Key，保留 baseUrl/model）
     */
    void saveConfig(AiConfigSaveReqVO saveReqVO);

    /**
     * 获取掩码视图（key 永不明文返回）
     */
    AiConfigRespVO getConfig(String configKey);

}
