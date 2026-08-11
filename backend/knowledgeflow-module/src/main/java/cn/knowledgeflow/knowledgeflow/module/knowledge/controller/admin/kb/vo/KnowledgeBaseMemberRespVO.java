package cn.knowledgeflow.module.knowledge.controller.admin.kb.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * 知识库成员信息 Response VO
 * 时间字段输出 ISO-8601 字符串（若依全局序列化 LocalDateTime 为时间戳，此处显式格式化以符合 §9 契约）。
 */
@Schema(description = "管理后台 - 知识库成员信息 Response VO")
@Data
public class KnowledgeBaseMemberRespVO {

    @Schema(description = "成员记录编号", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    private Long id;

    @Schema(description = "知识库编号", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    private Long kbId;

    @Schema(description = "用户编号", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    private Long userId;

    @Schema(description = "角色：ADMIN/EDITOR/VIEWER", requiredMode = Schema.RequiredMode.REQUIRED, example = "EDITOR")
    private String role;

    @Schema(description = "创建时间（ISO-8601）", example = "2026-08-01T14:36:35")
    private String createdAt;

}
