package cn.knowledgeflow.module.knowledge.service.aiconfig;

import cn.knowledgeflow.framework.security.core.util.SecurityFrameworkUtils;
import cn.knowledgeflow.module.knowledge.controller.admin.aiconfig.vo.AiConfigRespVO;
import cn.knowledgeflow.module.knowledge.controller.admin.aiconfig.vo.AiConfigSaveReqVO;
import cn.knowledgeflow.module.knowledge.dal.dataobject.aiconfig.AiApiConfigDO;
import cn.knowledgeflow.module.knowledge.dal.mysql.aiconfig.AiApiConfigMapper;
import cn.knowledgeflow.module.knowledge.framework.aes.AesUtil;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.Objects;

/**
 * AI 配置 Service 实现（T7）
 */
@Service
public class AiApiConfigServiceImpl implements AiApiConfigService {

    @Resource
    private AiApiConfigMapper aiApiConfigMapper;

    @Override
    public String getConfigValue(String configKey) {
        AiApiConfigDO config = aiApiConfigMapper.selectByConfigKey(configKey);
        if (config == null || config.getConfigValue() == null || config.getConfigValue().isEmpty()) {
            return null;
        }
        try {
            return AesUtil.decrypt(config.getConfigValue());
        } catch (Exception e) {
            return null; // 解密失败视为未配置，避免阻断转发
        }
    }

    @Override
    public void saveConfig(AiConfigSaveReqVO saveReqVO) {
        String configKey = saveReqVO.getConfigKey() == null ? "llm" : saveReqVO.getConfigKey();
        AiApiConfigDO config = aiApiConfigMapper.selectByConfigKey(configKey);
        if (config == null) {
            config = new AiApiConfigDO();
            config.setConfigKey(configKey);
            config.setCreator(Objects.toString(SecurityFrameworkUtils.getLoginUserId(), "1"));
            applyApiKey(config, saveReqVO.getApiKey());
            config.setBaseUrl(saveReqVO.getBaseUrl());
            config.setModel(saveReqVO.getModel());
            aiApiConfigMapper.insert(config);
        } else {
            // apiKey 为空串 = 清除：显式 set null（updateById 默认忽略 null 字段，需用 UpdateWrapper）
            boolean cleared = saveReqVO.getApiKey() != null && saveReqVO.getApiKey().isEmpty();
            if (cleared) {
                aiApiConfigMapper.update(null, new com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper<AiApiConfigDO>()
                        .eq(AiApiConfigDO::getId, config.getId())
                        .set(AiApiConfigDO::getConfigValue, null));
                config.setConfigValue(null); // 同步内存对象
            } else {
                applyApiKey(config, saveReqVO.getApiKey());
            }
            if (saveReqVO.getBaseUrl() != null) {
                config.setBaseUrl(saveReqVO.getBaseUrl());
            }
            if (saveReqVO.getModel() != null) {
                config.setModel(saveReqVO.getModel());
            }
            aiApiConfigMapper.updateById(config);
        }
    }

    @Override
    public AiConfigRespVO getConfig(String configKey) {
        AiApiConfigDO config = aiApiConfigMapper.selectByConfigKey(configKey);
        AiConfigRespVO respVO = new AiConfigRespVO();
        respVO.setHasKey(config != null && config.getConfigValue() != null && !config.getConfigValue().isEmpty());
        if (respVO.getHasKey()) {
            respVO.setMaskedKey(AesUtil.mask(getConfigValue(configKey)));
        }
        if (config != null) {
            respVO.setBaseUrl(config.getBaseUrl());
            respVO.setModel(config.getModel());
        }
        return respVO;
    }

    /**
     * 应用 apiKey：null=不变，空串=清除，非空=加密保存
     */
    private void applyApiKey(AiApiConfigDO config, String apiKey) {
        if (apiKey == null) {
            return;
        }
        if (apiKey.isEmpty()) {
            config.setConfigValue(null); // 清除
        } else {
            config.setConfigValue(AesUtil.encrypt(apiKey));
        }
    }

}
