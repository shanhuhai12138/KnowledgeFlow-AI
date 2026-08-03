package cn.iocoder.yudao.module.knowledge.controller.admin.kb.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * 知识库信息 Response VO
 *
 * 字段严格遵循项目书 §9 契约：{ id, name, description, isPrivate, documentCount, memberCount, createdAt, updatedAt }
 * 时间字段输出 ISO-8601 字符串（若依全局序列化 LocalDateTime 为时间戳，此处显式格式化以符合 §9 契约）。
 */
@Schema(description = "管理后台 - 知识库信息 Response VO")
@Data
public class KnowledgeBaseRespVO {

    @Schema(description = "知识库编号", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    private Long id;

    @Schema(description = "知识库名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "软件开发团队知识库")
    private String name;

    @Schema(description = "知识库描述", example = "团队共享的研发资料")
    private String description;

    @Schema(description = "是否私有", requiredMode = Schema.RequiredMode.REQUIRED, example = "true")
    private Boolean isPrivate;

    @Schema(description = "文档数量", requiredMode = Schema.RequiredMode.REQUIRED, example = "5")
    private Integer documentCount;

    @Schema(description = "成员数量", requiredMode = Schema.RequiredMode.REQUIRED, example = "3")
    private Integer memberCount;

    @Schema(description = "创建时间（ISO-8601）", requiredMode = Schema.RequiredMode.REQUIRED, example = "2026-08-01T14:36:35")
    private String createdAt;

    @Schema(description = "更新时间（ISO-8601）", requiredMode = Schema.RequiredMode.REQUIRED, example = "2026-08-01T14:36:35")
    private String updatedAt;

}
