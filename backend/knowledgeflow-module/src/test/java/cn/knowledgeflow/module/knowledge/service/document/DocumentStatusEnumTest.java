package cn.knowledgeflow.module.knowledge.service.document;

import cn.knowledgeflow.module.knowledge.enums.document.DocumentStatusEnum;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 文档状态枚举单元测试
 *
 * @author KnowledgeFlow
 */
class DocumentStatusEnumTest {

    @Test
    void testEnumValues() {
        assertEquals(4, DocumentStatusEnum.values().length);
    }

    @Test
    void testStatusValues() {
        assertEquals("pending", DocumentStatusEnum.PENDING.getStatus());
        assertEquals("processing", DocumentStatusEnum.PROCESSING.getStatus());
        assertEquals("processed", DocumentStatusEnum.PROCESSED.getStatus());
        assertEquals("failed", DocumentStatusEnum.FAILED.getStatus());
    }

    @Test
    void testDescValues() {
        assertEquals("待处理", DocumentStatusEnum.PENDING.getDesc());
        assertEquals("处理中", DocumentStatusEnum.PROCESSING.getDesc());
        assertEquals("处理完成", DocumentStatusEnum.PROCESSED.getDesc());
        assertEquals("处理失败", DocumentStatusEnum.FAILED.getDesc());
    }

    @Test
    void testIsValid() {
        assertTrue(DocumentStatusEnum.isValid("pending"));
        assertTrue(DocumentStatusEnum.isValid("processing"));
        assertTrue(DocumentStatusEnum.isValid("processed"));
        assertTrue(DocumentStatusEnum.isValid("failed"));
        assertFalse(DocumentStatusEnum.isValid("invalid"));
        assertFalse(DocumentStatusEnum.isValid(null));
    }
}
