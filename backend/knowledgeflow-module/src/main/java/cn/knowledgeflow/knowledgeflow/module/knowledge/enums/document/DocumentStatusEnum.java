package cn.knowledgeflow.module.knowledge.enums.document;

import lombok.AllArgsConstructor;
import lombok.Getter;

import java.util.Arrays;

/**
 * 文档处理状态枚举（状态机：pending → processing → processed/failed）
 */
@Getter
@AllArgsConstructor
public enum DocumentStatusEnum {

    PENDING("pending", "待处理"),
    PROCESSING("processing", "处理中"),
    PROCESSED("processed", "处理完成"),
    FAILED("failed", "处理失败");

    private final String status;
    private final String desc;

    public static boolean isValid(String status) {
        return Arrays.stream(values()).anyMatch(e -> e.getStatus().equals(status));
    }

}
