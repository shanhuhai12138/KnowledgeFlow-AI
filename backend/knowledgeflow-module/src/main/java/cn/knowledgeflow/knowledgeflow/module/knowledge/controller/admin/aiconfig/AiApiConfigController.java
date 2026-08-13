package cn.knowledgeflow.module.knowledge.controller.admin.aiconfig;

import cn.knowledgeflow.framework.common.pojo.CommonResult;
import cn.knowledgeflow.module.knowledge.controller.admin.aiconfig.vo.AiConfigRespVO;
import cn.knowledgeflow.module.knowledge.controller.admin.aiconfig.vo.AiConfigSaveReqVO;
import cn.knowledgeflow.module.knowledge.service.aiconfig.AiApiConfigService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import jakarta.validation.Valid;

import static cn.knowledgeflow.framework.common.pojo.CommonResult.success;

/**
 * AI 配置接口（T7：API Key 管理，DR-13 开源化）
 *
 * 部署者在界面填模型 API Key，经 AES 加密落库；key 永不明文返回。
 */
@Tag(name = "管理后台 - AI 配置（API Key）")
@RestController
@RequestMapping("/knowledge/ai-config")
@Validated
public class AiApiConfigController {

    @Resource
    private AiApiConfigService aiApiConfigService;

    @GetMapping
    @Operation(summary = "获取 AI 配置（hasKey + 掩码 Key + baseUrl/model）")
    @PreAuthorize("@ss.hasRole('super_admin')") // 仅超级管理员（T7 安全收紧：普通用户禁止读取全局 Key 配置）
    public CommonResult<AiConfigRespVO> getConfig() {
        return success(aiApiConfigService.getConfig("llm"));
    }

    @PutMapping
    @Operation(summary = "保存/更新 AI 配置（apiKey 为空 = 清除 Key）")
    @PreAuthorize("@ss.hasRole('super_admin')") // 仅超级管理员（T7 安全收紧：普通用户禁止覆盖全局 Key）
    public CommonResult<Boolean> saveConfig(@Valid @RequestBody AiConfigSaveReqVO saveReqVO) {
        aiApiConfigService.saveConfig(saveReqVO);
        return success(true);
    }

}
