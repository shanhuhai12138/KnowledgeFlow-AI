package cn.knowledgeflow.module.knowledge.service.kb;

import cn.knowledgeflow.module.knowledge.enums.kb.KnowledgeBaseMemberRoleEnum;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 知识库成员角色枚举单元测试
 *
 * @author KnowledgeFlow
 */
class KnowledgeBaseMemberRoleEnumTest {

    @Test
    void testEnumValues() {
        assertEquals(3, KnowledgeBaseMemberRoleEnum.values().length);
    }

    @Test
    void testRoleValues() {
        assertEquals("ADMIN", KnowledgeBaseMemberRoleEnum.ADMIN.getRole());
        assertEquals("EDITOR", KnowledgeBaseMemberRoleEnum.EDITOR.getRole());
        assertEquals("VIEWER", KnowledgeBaseMemberRoleEnum.VIEWER.getRole());
    }

    @Test
    void testIsValid() {
        assertTrue(KnowledgeBaseMemberRoleEnum.isValid("ADMIN"));
        assertTrue(KnowledgeBaseMemberRoleEnum.isValid("EDITOR"));
        assertTrue(KnowledgeBaseMemberRoleEnum.isValid("VIEWER"));
        assertFalse(KnowledgeBaseMemberRoleEnum.isValid("invalid"));
        assertFalse(KnowledgeBaseMemberRoleEnum.isValid(null));
    }
}
