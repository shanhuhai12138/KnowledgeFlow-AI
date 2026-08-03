package cn.iocoder.yudao.module.knowledge.controller.admin.search.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;
import java.util.List;

/**
 * 对话 Request VO（转发契约：POST /ai/chat）
 */
@Schema(description = "管理后台 - 智能问答 Request VO")
@Data
public class ChatReqVO {

    @Schema(description = "会话编号", example = "s1")
    private String sessionId;

    @Schema(description = "知识库编号", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    @NotNull(message = "知识库编号不能为空")
    private Long kbId;

    @Schema(description = "用户消息", requiredMode = Schema.RequiredMode.REQUIRED, example = "什么是 RAG？")
    @NotBlank(message = "消息不能为空")
    private String message;

    @Schema(description = "多轮历史（最近优先）")
    private List<ChatHistoryItemVO> history;

    @Data
    public static class ChatHistoryItemVO {

        @Schema(description = "角色：user/assistant", example = "user")
        private String role;

        @Schema(description = "内容", example = "你好")
        private String content;

    }

}
