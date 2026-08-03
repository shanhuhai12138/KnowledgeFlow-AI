package cn.iocoder.yudao.module.knowledge.controller.admin.stat.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * 看板总览 Response VO（T3.3）
 */
@Schema(description = "管理后台 - 看板总览 Response VO")
@Data
public class StatOverviewRespVO {

    @Schema(description = "文档数量", example = "5")
    private Integer documentCount;

    @Schema(description = "查询次数", example = "128")
    private Integer queryCount;

    @Schema(description = "LLM 调用次数（暂以查询次数近似）", example = "128")
    private Integer llmCallCount;

    @Schema(description = "知识库数量", example = "2")
    private Integer kbCount;

}
