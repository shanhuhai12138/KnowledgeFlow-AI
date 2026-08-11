package cn.knowledgeflow.module.knowledge.controller.admin.aiconfig.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * AI 配置 Response VO（T7：key 永不明文返回）
 */
@Schema(description = "管理后台 - AI 配置 Response VO")
@Data
public class AiConfigRespVO {

    @Schema(description = "是否已配置 Key", example = "true")
    private Boolean hasKey;

    @Schema(description = "掩码 Key（sk-****xxxx）", example = "sk-****1234")
    private String maskedKey;

    @Schema(description = "API 地址", example = "https://api.deepseek.com")
    private String baseUrl;

    @Schema(description = "模型名", example = "deepseek-v4-flash")
    private String model;

}
