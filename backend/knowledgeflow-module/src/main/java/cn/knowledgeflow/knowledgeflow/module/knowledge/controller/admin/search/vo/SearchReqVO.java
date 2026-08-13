package cn.knowledgeflow.module.knowledge.controller.admin.search.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import java.math.BigDecimal;

/**
 * 搜索 Request VO（转发契约：POST /ai/search）
 */
@Schema(description = "管理后台 - 语义搜索 Request VO")
@Data
public class SearchReqVO {

    @Schema(description = "查询内容", requiredMode = Schema.RequiredMode.REQUIRED, example = "开发环境怎么搭建")
    @NotBlank(message = "查询内容不能为空")
    private String query;

    @Schema(description = "知识库编号", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    @NotNull(message = "知识库编号不能为空")
    private Long kbId;

    @Schema(description = "返回条数 Top-K", example = "5")
    private Integer topK;

    @Schema(description = "相似度阈值", example = "0.6")
    private BigDecimal threshold;

    @Schema(description = "是否混合检索（dense + sparse RRF）", example = "true")
    private Boolean useHybrid;

}
