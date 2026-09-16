package cn.knowledgeflow.module.knowledge.service.kb;

import cn.knowledgeflow.framework.security.core.util.SecurityFrameworkUtils;
import cn.knowledgeflow.module.knowledge.dal.dataobject.kb.KnowledgeBaseDO;
import cn.knowledgeflow.module.knowledge.dal.dataobject.kb.KnowledgeBaseMemberDO;
import cn.knowledgeflow.module.knowledge.dal.mysql.kb.KnowledgeBaseMapper;
import cn.knowledgeflow.module.knowledge.dal.mysql.kb.KnowledgeBaseMemberMapper;
import cn.knowledgeflow.framework.common.exception.ServiceException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.MockedStatic;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * 知识库权限校验单元测试（service 层三级权限：view / edit / manage）
 *
 * 覆盖矩阵：
 *  - view：公开库任何人可读；私有库仅所有者/成员
 *  - edit：所有者/ADMIN/EDITOR 可写；VIEWER 与非成员不可上传
 *  - manage：仅所有者/ADMIN 可更新/删除；EDITOR/VIEWER 不可
 */
class KnowledgeBasePermissionTest {

    private KnowledgeBaseMapper knowledgeBaseMapper;
    private KnowledgeBaseMemberMapper memberMapper;
    private KnowledgeBaseServiceImpl service;

    private static final Long OWNER_ID = 1L;
    private static final Long ADMIN_ID = 2L;
    private static final Long EDITOR_ID = 3L;
    private static final Long VIEWER_ID = 4L;
    private static final Long STRANGER_ID = 5L;
    private static final Long KB_ID = 100L;

    @BeforeEach
    void setUp() {
        knowledgeBaseMapper = mock(KnowledgeBaseMapper.class);
        memberMapper = mock(KnowledgeBaseMemberMapper.class);
        service = new KnowledgeBaseServiceImpl();
        inject("knowledgeBaseMapper", knowledgeBaseMapper);
        inject("knowledgeBaseMemberMapper", memberMapper);
    }

    private KnowledgeBaseDO sharedKb() {
        KnowledgeBaseDO kb = new KnowledgeBaseDO();
        kb.setId(KB_ID);
        kb.setIsPrivate(false);
        kb.setOwnerId(OWNER_ID);
        return kb;
    }

    private KnowledgeBaseDO privateKb() {
        KnowledgeBaseDO kb = sharedKb();
        kb.setIsPrivate(true);
        return kb;
    }

    private MockedStatic<SecurityFrameworkUtils> loginAs(Long userId) {
        MockedStatic<SecurityFrameworkUtils> ms = mockStatic(SecurityFrameworkUtils.class);
        ms.when(SecurityFrameworkUtils::getLoginUserId).thenReturn(userId);
        return ms;
    }

    private void memberRole(Long userId, String role) {
        if (role == null) {
            when(memberMapper.selectByKbIdAndUserId(KB_ID, userId)).thenReturn(null);
            return;
        }
        KnowledgeBaseMemberDO m = new KnowledgeBaseMemberDO();
        m.setKbId(KB_ID);
        m.setUserId(userId);
        m.setRole(role);
        when(memberMapper.selectByKbIdAndUserId(KB_ID, userId)).thenReturn(m);
    }

    // ==================== view：公开库人人可读；私有库仅所有者/成员 ====================

    @Test
    void view_publicKb_strangerAllowed() {
        when(knowledgeBaseMapper.selectById(KB_ID)).thenReturn(sharedKb());
        try (MockedStatic<SecurityFrameworkUtils> ms = loginAs(STRANGER_ID)) {
            memberRole(STRANGER_ID, null);
            assertDoesNotThrow(() -> service.validateViewPermission(KB_ID));
        }
    }

    @Test
    void view_privateKb_strangerDenied() {
        when(knowledgeBaseMapper.selectById(KB_ID)).thenReturn(privateKb());
        try (MockedStatic<SecurityFrameworkUtils> ms = loginAs(STRANGER_ID)) {
            memberRole(STRANGER_ID, null);
            ServiceException e = assertThrows(ServiceException.class,
                    () -> service.validateViewPermission(KB_ID));
            assertEquals(1_011_000_002, e.getCode());
        }
    }

    @Test
    void view_privateKb_memberAllowed() {
        when(knowledgeBaseMapper.selectById(KB_ID)).thenReturn(privateKb());
        try (MockedStatic<SecurityFrameworkUtils> ms = loginAs(VIEWER_ID)) {
            memberRole(VIEWER_ID, "VIEWER");
            assertDoesNotThrow(() -> service.validateViewPermission(KB_ID));
        }
    }

    // ==================== edit：所有者/ADMIN/EDITOR 可写；VIEWER/路人不可 ====================

    @Test
    void edit_ownerAllowed() {
        when(knowledgeBaseMapper.selectById(KB_ID)).thenReturn(sharedKb());
        try (MockedStatic<SecurityFrameworkUtils> ms = loginAs(OWNER_ID)) {
            assertDoesNotThrow(() -> service.validateEditPermission(KB_ID));
        }
    }

    @Test
    void edit_adminMemberAllowed() {
        when(knowledgeBaseMapper.selectById(KB_ID)).thenReturn(sharedKb());
        try (MockedStatic<SecurityFrameworkUtils> ms = loginAs(ADMIN_ID)) {
            memberRole(ADMIN_ID, "ADMIN");
            assertDoesNotThrow(() -> service.validateEditPermission(KB_ID));
        }
    }

    @Test
    void edit_editorMemberAllowed() {
        when(knowledgeBaseMapper.selectById(KB_ID)).thenReturn(sharedKb());
        try (MockedStatic<SecurityFrameworkUtils> ms = loginAs(EDITOR_ID)) {
            memberRole(EDITOR_ID, "EDITOR");
            assertDoesNotThrow(() -> service.validateEditPermission(KB_ID));
        }
    }

    @Test
    void edit_viewerMemberDenied() {
        when(knowledgeBaseMapper.selectById(KB_ID)).thenReturn(sharedKb());
        try (MockedStatic<SecurityFrameworkUtils> ms = loginAs(VIEWER_ID)) {
            memberRole(VIEWER_ID, "VIEWER");
            ServiceException e = assertThrows(ServiceException.class,
                    () -> service.validateEditPermission(KB_ID));
            assertEquals(1_011_000_004, e.getCode());
        }
    }

    @Test
    void edit_strangerDenied() {
        when(knowledgeBaseMapper.selectById(KB_ID)).thenReturn(sharedKb());
        try (MockedStatic<SecurityFrameworkUtils> ms = loginAs(STRANGER_ID)) {
            memberRole(STRANGER_ID, null);
            ServiceException e = assertThrows(ServiceException.class,
                    () -> service.validateEditPermission(KB_ID));
            assertEquals(1_011_000_004, e.getCode());
        }
    }

    // ==================== manage：仅所有者/ADMIN；EDITOR 也不行 ====================

    @Test
    void manage_editorMemberDenied() {
        when(knowledgeBaseMapper.selectById(KB_ID)).thenReturn(sharedKb());
        try (MockedStatic<SecurityFrameworkUtils> ms = loginAs(EDITOR_ID)) {
            memberRole(EDITOR_ID, "EDITOR");
            ServiceException e = assertThrows(ServiceException.class,
                    () -> service.validateManagePermission(KB_ID));
            assertEquals(1_011_000_003, e.getCode());
        }
    }

    @Test
    void manage_adminMemberAllowed() {
        when(knowledgeBaseMapper.selectById(KB_ID)).thenReturn(sharedKb());
        try (MockedStatic<SecurityFrameworkUtils> ms = loginAs(ADMIN_ID)) {
            memberRole(ADMIN_ID, "ADMIN");
            assertDoesNotThrow(() -> service.validateManagePermission(KB_ID));
        }
    }

    @Test
    void manage_ownerAllowed() {
        when(knowledgeBaseMapper.selectById(KB_ID)).thenReturn(sharedKb());
        try (MockedStatic<SecurityFrameworkUtils> ms = loginAs(OWNER_ID)) {
            assertDoesNotThrow(() -> service.validateManagePermission(KB_ID));
        }
    }

    // ==================== 工具 ====================

    /** @Resource 字段注入（无 setter），反射直填。 */
    private void inject(String field, Object value) {
        try {
            java.lang.reflect.Field f = KnowledgeBaseServiceImpl.class.getDeclaredField(field);
            f.setAccessible(true);
            f.set(service, value);
        } catch (ReflectiveOperationException e) {
            throw new IllegalStateException("inject failed: " + field, e);
        }
    }
}
