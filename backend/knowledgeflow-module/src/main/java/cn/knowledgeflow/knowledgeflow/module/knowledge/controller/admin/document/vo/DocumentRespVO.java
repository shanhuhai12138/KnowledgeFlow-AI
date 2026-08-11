package cn.knowledgeflow.module.knowledge.controller.admin.document.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 文档信息 Response VO
 *
 * 字段严格遵循任务书 T2.3 契约：{ id, kbId, kbName, filename, fileType, fileSize(Long), pageCount,
 * status, uploader, tags[], createdAt, updatedAt }
 */
@Schema(description = "管理后台 - 文档信息 Response VO")
@Data
public class DocumentRespVO {

    @Schema(description = "文档编号", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    private Long id;

    @Schema(description = "知识库编号", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    private Long kbId;

    @Schema(description = "知识库名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "软件开发团队知识库")
    private String kbName;

    @Schema(description = "文件名", requiredMode = Schema.RequiredMode.REQUIRED, example = "开发环境搭建 SOP.md")
    private String filename;

    @Schema(description = "文件类型：pdf/docx/txt/md", requiredMode = Schema.RequiredMode.REQUIRED, example = "pdf")
    private String fileType;

    @Schema(description = "文件大小（字节）", requiredMode = Schema.RequiredMode.REQUIRED, example = "1048576")
    private Long fileSize;

    @Schema(description = "页数", example = "24")
    private Integer pageCount;

    @Schema(description = "状态：pending/processing/processed/failed", requiredMode = Schema.RequiredMode.REQUIRED, example = "pending")
    private String status;

    @Schema(description = "上传者昵称", requiredMode = Schema.RequiredMode.REQUIRED, example = "芋道源码")
    private String uploader;

    @Schema(description = "标签", example = "[\"运维\",\"SOP\"]")
    private String[] tags;

    @Schema(description = "创建时间（ISO-8601）", requiredMode = Schema.RequiredMode.REQUIRED)
    private LocalDateTime createdAt;

    @Schema(description = "更新时间（ISO-8601）", requiredMode = Schema.RequiredMode.REQUIRED)
    private LocalDateTime updatedAt;

}
