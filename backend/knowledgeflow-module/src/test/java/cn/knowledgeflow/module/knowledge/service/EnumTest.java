package cn.knowledgeflow.module.knowledge.service;

import cn.knowledgeflow.module.knowledge.enums.document.DocumentStatusEnum;
import cn.knowledgeflow.module.knowledge.enums.kb.KnowledgeBaseMemberRoleEnum;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 枚举类综合测试
 *
 * @author KnowledgeFlow
 */
class EnumTest {

    @Test
    void testDocumentStatusEnum() {
        assertEquals(4, DocumentStatusEnum.values().length);
        assertTrue(DocumentStatusEnum.isValid("pending"));
        assertFalse(DocumentStatusEnum.isValid("invalid"));
    }

    @Test
    void testMemberRoleEnum() {
        assertEquals(3, KnowledgeBaseMemberRoleEnum.values().length);
        assertTrue(KnowledgeBaseMemberRoleEnum.isValid("ADMIN"));
        assertFalse(KnowledgeBaseMemberRoleEnum.isValid("invalid"));
    }
}
