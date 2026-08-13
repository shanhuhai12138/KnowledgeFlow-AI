package cn.knowledgeflow.module.knowledge.controller.admin.aiconfig.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import jakarta.validation.constraints.Size;

/**
 * AI 配置保存 Request VO（T7）
 */
@Schema(description = "管理后台 - AI 配置保存 Request VO")
@Data
public class AiConfigSaveReqVO {

    @Schema(description = "配置键（默认 llm）", example = "llm")
    private String configKey = "llm";

    @Schema(description = "API Key（为空 = 清除已有 Key）", example = "sk-xxx")
    @Size(max = 2000, message = "API Key 不能超过 2000 字符")
    private String apiKey;

    @Schema(description = "API 地址", example = "https://api.deepseek.com")
    private String baseUrl;

    @Schema(description = "模型名", example = "deepseek-v4-flash")
    private String model;

}
