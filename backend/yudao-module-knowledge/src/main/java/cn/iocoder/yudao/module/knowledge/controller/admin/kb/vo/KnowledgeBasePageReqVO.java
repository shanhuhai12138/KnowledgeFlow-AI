package cn.iocoder.yudao.module.knowledge.controller.admin.kb.vo;

import cn.iocoder.yudao.framework.common.pojo.PageParam;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Schema(description = "管理后台 - 知识库分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
public class KnowledgeBasePageReqVO extends PageParam {

    @Schema(description = "知识库名称，模糊匹配", example = "软件开发")
    private String name;

    @Schema(description = "是否私有", example = "true")
    private Boolean isPrivate;

}
