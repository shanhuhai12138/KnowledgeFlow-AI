package cn.iocoder.yudao.module.knowledge.controller.admin.kb.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Size;

@Schema(description = "管理后台 - 知识库创建/修改 Request VO")
@Data
public class KnowledgeBaseSaveReqVO {

    @Schema(description = "知识库编号（修改时必传）", example = "1")
    private Long id;

    @Schema(description = "知识库名称", requiredMode = Schema.RequiredMode.REQUIRED, example = "软件开发团队知识库")
    @NotBlank(message = "知识库名称不能为空")
    @Size(max = 255, message = "知识库名称不能超过 255 个字符")
    private String name;

    @Schema(description = "知识库描述", example = "团队共享的研发资料")
    private String description;

    @Schema(description = "是否私有：true=私有（仅所有者/成员可见），false=共享", requiredMode = Schema.RequiredMode.REQUIRED, example = "true")
    @NotNull(message = "是否私有不能为空")
    private Boolean isPrivate;

}
