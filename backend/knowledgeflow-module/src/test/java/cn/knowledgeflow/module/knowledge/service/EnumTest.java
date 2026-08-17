package cn.knowledgeflow.module.knowledge.service;

import cn.knowledgeflow.module.knowledge.enums.document.DocumentStatusEnum;
import cn.knowledgeflow.module.knowledge.enums.kb.KnowledgeBaseMemberRoleEnum;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 枚举类单元测试
 *
 * @author KnowledgeFlow
 */
class EnumTest {

    @Test
    void testDocumentStatusEnum() {
        assertEquals("pending", DocumentStatusEnum.PENDING.getStatus());
        assertEquals("processing", DocumentStatusEnum.PROCESSING.getStatus());
        assertEquals("processed", DocumentStatusEnum.PROCESSED.getStatus());
        assertEquals("failed", DocumentStatusEnum.FAILED.getStatus());
    }

    @Test
    void testDocumentStatusFromName() {
        assertEquals(DocumentStatusEnum.PENDING, DocumentStatusEnum.fromName("pending"));
        assertEquals(DocumentStatusEnum.PROCESSING, DocumentStatusEnum.fromName("processing"));
        assertEquals(DocumentStatusEnum.PROCESSED, DocumentStatusEnum.fromName("processed"));
        assertEquals(DocumentStatusEnum.FAILED, DocumentStatusEnum.fromName("failed"));
    }

    @Test
    void testDocumentStatusIsTerminal() {
        assertFalse(DocumentStatusEnum.PENDING.isTerminal());
        assertFalse(DocumentStatusEnum.PROCESSING.isTerminal());
        assertTrue(DocumentStatusEnum.PROCESSED.isTerminal());
        assertTrue(DocumentStatusEnum.FAILED.isTerminal());
    }

    @Test
    void testMemberRoleEnum() {
        assertEquals("OWNER", KnowledgeBaseMemberRoleEnum.OWNER.getRole());
        assertEquals("ADMIN", KnowledgeBaseMemberRoleEnum.ADMIN.getRole());
        assertEquals("EDITOR", KnowledgeBaseMemberRoleEnum.EDITOR.getRole());
        assertEquals("VIEWER", KnowledgeBaseMemberRoleEnum.VIEWER.getRole());
    }

    @Test
    void testMemberRoleHasPermission() {
        // OWNER 拥有所有权限
        assertTrue(KnowledgeBaseMemberRoleEnum.OWNER.hasPermission(KnowledgeBaseMemberRoleEnum.VIEWER));
        assertTrue(KnowledgeBaseMemberRoleEnum.OWNER.hasPermission(KnowledgeBaseMemberRoleEnum.ADMIN));
        assertTrue(KnowledgeBaseMemberRoleEnum.OWNER.hasPermission(KnowledgeBaseMemberRoleEnum.OWNER));

        // ADMIN 拥有除 OWNER 外的所有权限
        assertTrue(KnowledgeBaseMemberRoleEnum.ADMIN.hasPermission(KnowledgeBaseMemberRoleEnum.EDITOR));
        assertTrue(KnowledgeBaseMemberRoleEnum.ADMIN.hasPermission(KnowledgeBaseMemberRoleEnum.VIEWER));
        assertFalse(KnowledgeBaseMemberRoleEnum.ADMIN.hasPermission(KnowledgeBaseMemberRoleEnum.OWNER));

        // EDITOR 拥有 VIEWER 权限
        assertTrue(KnowledgeBaseMemberRoleEnum.EDITOR.hasPermission(KnowledgeBaseMemberRoleEnum.VIEWER));
        assertFalse(KnowledgeBaseMemberRoleEnum.EDITOR.hasPermission(KnowledgeBaseMemberRoleEnum.ADMIN));

        // VIEWER 只有查看权限
        assertFalse(KnowledgeBaseMemberRoleEnum.VIEWER.hasPermission(KnowledgeBaseMemberRoleEnum.EDITOR));
        assertFalse(KnowledgeBaseMemberRoleEnum.VIEWER.hasPermission(KnowledgeBaseMemberRoleEnum.ADMIN));
    }
}
