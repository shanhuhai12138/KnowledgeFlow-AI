package cn.knowledgeflow.module.knowledge.controller.admin.kb.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotEmpty;
import javax.validation.constraints.NotNull;

@Schema(description = "管理后台 - 知识库成员创建 Request VO")
@Data
public class KnowledgeBaseMemberSaveReqVO {

    @Schema(description = "知识库编号", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    @NotNull(message = "知识库编号不能为空")
    private Long kbId;

    @Schema(description = "用户编号", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    @NotNull(message = "用户编号不能为空")
    private Long userId;

    @Schema(description = "角色：ADMIN/EDITOR/VIEWER", requiredMode = Schema.RequiredMode.REQUIRED, example = "EDITOR")
    @NotEmpty(message = "角色不能为空")
    private String role;

}
