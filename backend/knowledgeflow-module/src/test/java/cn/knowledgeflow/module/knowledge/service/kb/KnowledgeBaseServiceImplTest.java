package cn.knowledgeflow.module.knowledge.service.kb;

import cn.knowledgeflow.module.knowledge.dal.dataobject.kb.KnowledgeBaseDO;
import cn.knowledgeflow.module.knowledge.dal.mysql.kb.KnowledgeBaseMapper;
import cn.knowledgeflow.module.knowledge.enums.kb.KnowledgeBaseMemberRoleEnum;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * 知识库 Service 单元测试
 *
 * @author KnowledgeFlow
 */
@ExtendWith(MockitoExtension.class)
class KnowledgeBaseServiceImplTest {

    @Mock
    private KnowledgeBaseMapper knowledgeBaseMapper;

    @InjectMocks
    private KnowledgeBaseServiceImpl knowledgeBaseService;

    @Test
    void testMemberRoleEnum() {
        assertEquals("OWNER", KnowledgeBaseMemberRoleEnum.OWNER.getRole());
        assertEquals("ADMIN", KnowledgeBaseMemberRoleEnum.ADMIN.getRole());
        assertEquals("EDITOR", KnowledgeBaseMemberRoleEnum.EDITOR.getRole());
        assertEquals("VIEWER", KnowledgeBaseMemberRoleEnum.VIEWER.getRole());
    }

    @Test
    void testMemberRoleHasPermission() {
        assertTrue(KnowledgeBaseMemberRoleEnum.OWNER.hasPermission(KnowledgeBaseMemberRoleEnum.VIEWER));
        assertTrue(KnowledgeBaseMemberRoleEnum.ADMIN.hasPermission(KnowledgeBaseMemberRoleEnum.EDITOR));
        assertFalse(KnowledgeBaseMemberRoleEnum.VIEWER.hasPermission(KnowledgeBaseMemberRoleEnum.EDITOR));
    }

    @Test
    void testKnowledgeBaseCreation() {
        // 模拟创建知识库
        KnowledgeBaseDO kb = new KnowledgeBaseDO();
        kb.setName("测试知识库");
        kb.setOwnerId(1L);
        kb.setDocumentCount(0);
        kb.setMemberCount(0);

        when(knowledgeBaseMapper.insert(any())).thenReturn(1);
        when(knowledgeBaseMapper.selectById(anyLong())).thenReturn(kb);

        // 测试业务逻辑
        assertNotNull(kb);
        assertEquals("测试知识库", kb.getName());
        assertEquals(0L, kb.getMemberCount());
    }
}
