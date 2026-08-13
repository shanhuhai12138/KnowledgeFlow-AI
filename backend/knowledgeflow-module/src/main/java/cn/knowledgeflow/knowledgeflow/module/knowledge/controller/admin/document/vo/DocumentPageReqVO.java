package cn.knowledgeflow.module.knowledge.controller.admin.document.vo;

import cn.knowledgeflow.framework.common.pojo.PageParam;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Schema(description = "管理后台 - 文档分页 Request VO（筛选：KB/格式/状态/文件名）")
@Data
@EqualsAndHashCode(callSuper = true)
public class DocumentPageReqVO extends PageParam {

    @Schema(description = "知识库编号", example = "1")
    private Long kbId;

    @Schema(description = "文件类型：pdf/docx/txt/md", example = "pdf")
    private String fileType;

    @Schema(description = "状态：pending/processing/processed/failed", example = "processed")
    private String status;

    @Schema(description = "文件名，模糊匹配", example = "SOP")
    private String filename;

}
