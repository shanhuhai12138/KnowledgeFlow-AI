package cn.iocoder.yudao.module.knowledge.controller.admin.kb.vo;

import cn.iocoder.yudao.framework.common.pojo.PageParam;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Schema(description = "管理后台 - 知识库成员分页 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
public class KnowledgeBaseMemberPageReqVO extends PageParam {

    @Schema(description = "知识库编号", example = "1")
    private Long kbId;

    @Schema(description = "用户编号", example = "1")
    private Long userId;

}
