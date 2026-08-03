package cn.iocoder.yudao.module.knowledge.service.kb;

import cn.iocoder.yudao.framework.common.pojo.PageResult;
import cn.iocoder.yudao.framework.common.util.object.BeanUtils;
import cn.iocoder.yudao.framework.mybatis.core.query.LambdaQueryWrapperX;
import cn.iocoder.yudao.framework.security.core.util.SecurityFrameworkUtils;
import cn.iocoder.yudao.module.knowledge.controller.admin.kb.vo.KnowledgeBasePageReqVO;
import cn.iocoder.yudao.module.knowledge.controller.admin.kb.vo.KnowledgeBaseSaveReqVO;
import cn.iocoder.yudao.module.knowledge.dal.dataobject.kb.KnowledgeBaseDO;
import cn.iocoder.yudao.module.knowledge.dal.dataobject.kb.KnowledgeBaseMemberDO;
import cn.iocoder.yudao.module.knowledge.dal.mysql.kb.KnowledgeBaseMapper;
import cn.iocoder.yudao.module.knowledge.dal.mysql.kb.KnowledgeBaseMemberMapper;
import cn.iocoder.yudao.module.knowledge.enums.kb.KnowledgeBaseMemberRoleEnum;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.List;

import static cn.iocoder.yudao.framework.common.exception.util.ServiceExceptionUtil.exception;
import static cn.iocoder.yudao.module.knowledge.enums.ErrorCodeConstants.KNOWLEDGE_BASE_ACCESS_DENIED;
import static cn.iocoder.yudao.module.knowledge.enums.ErrorCodeConstants.KNOWLEDGE_BASE_NAME_DUPLICATE;
import static cn.iocoder.yudao.module.knowledge.enums.ErrorCodeConstants.KNOWLEDGE_BASE_NOT_EXISTS;
import static cn.iocoder.yudao.module.knowledge.enums.ErrorCodeConstants.KNOWLEDGE_BASE_UPDATE_DENIED;
import static cn.iocoder.yudao.module.knowledge.enums.ErrorCodeConstants.KNOWLEDGE_BASE_UPLOAD_DENIED;

/**
 * 知识库 Service 实现类
 *
 * 可见性：共享库租户内可见；私有库仅所有者/成员可见。
 * 管理权限：所有者（owner）或 ADMIN 成员可更新/删除/管理成员。
 * 多租户隔离：表带 tenant_id，框架 TenantLineInnerInterceptor 自动追加条件。
 */
@Service
public class KnowledgeBaseServiceImpl implements KnowledgeBaseService {

    @Resource
    private KnowledgeBaseMapper knowledgeBaseMapper;
    @Resource
    private KnowledgeBaseMemberMapper knowledgeBaseMemberMapper;

    @Override
    public Long createKnowledgeBase(KnowledgeBaseSaveReqVO createReqVO) {
        validateNameUnique(null, createReqVO.getName());
        // 创建者即所有者
        KnowledgeBaseDO knowledgeBase = BeanUtils.toBean(createReqVO, KnowledgeBaseDO.class);
        knowledgeBase.setOwnerId(SecurityFrameworkUtils.getLoginUserId());
        knowledgeBase.setDocumentCount(0);
        knowledgeBase.setMemberCount(0);
        knowledgeBaseMapper.insert(knowledgeBase);
        return knowledgeBase.getId();
    }

    @Override
    public void updateKnowledgeBase(KnowledgeBaseSaveReqVO updateReqVO) {
        validateKnowledgeBaseExists(updateReqVO.getId());
        validateManagePermission(updateReqVO.getId());
        validateNameUnique(updateReqVO.getId(), updateReqVO.getName());
        KnowledgeBaseDO updateObj = BeanUtils.toBean(updateReqVO, KnowledgeBaseDO.class);
        knowledgeBaseMapper.updateById(updateObj);
    }

    @Override
    public void deleteKnowledgeBase(Long id) {
        validateKnowledgeBaseExists(id);
        validateManagePermission(id);
        knowledgeBaseMapper.deleteById(id);
        // 级联删除成员记录
        knowledgeBaseMemberMapper.delete(new LambdaQueryWrapperX<KnowledgeBaseMemberDO>()
                .eq(KnowledgeBaseMemberDO::getKbId, id));
    }

    @Override
    public KnowledgeBaseDO getKnowledgeBase(Long id) {
        KnowledgeBaseDO knowledgeBase = knowledgeBaseMapper.selectById(id);
        if (knowledgeBase == null) {
            throw exception(KNOWLEDGE_BASE_NOT_EXISTS);
        }
        validateViewPermission(knowledgeBase.getId());
        return knowledgeBase;
    }

    @Override
    public PageResult<KnowledgeBaseDO> getKnowledgeBasePage(KnowledgeBasePageReqVO pageReqVO) {
        return knowledgeBaseMapper.selectVisiblePage(pageReqVO, SecurityFrameworkUtils.getLoginUserId());
    }

    @Override
    public List<KnowledgeBaseDO> getKnowledgeBaseList() {
        return knowledgeBaseMapper.selectVisibleList(SecurityFrameworkUtils.getLoginUserId());
    }

    @Override
    public void validateKnowledgeBaseExists(Long id) {
        if (id == null || knowledgeBaseMapper.selectById(id) == null) {
            throw exception(KNOWLEDGE_BASE_NOT_EXISTS);
        }
    }

    // ==================== 内部方法：权限校验 ====================

    /**
     * 校验知识库名称唯一（同一租户内，框架自动 tenant 过滤）
     */
    private void validateNameUnique(Long id, String name) {
        KnowledgeBaseDO knowledgeBase = knowledgeBaseMapper.selectByName(name);
        if (knowledgeBase != null && !knowledgeBase.getId().equals(id)) {
            throw exception(KNOWLEDGE_BASE_NAME_DUPLICATE, name);
        }
    }

    /**
     * 校验可见性：共享库 或 所有者 或 成员
     */
    public void validateViewPermission(Long kbId) {
        KnowledgeBaseDO knowledgeBase = knowledgeBaseMapper.selectById(kbId);
        if (knowledgeBase == null) {
            throw exception(KNOWLEDGE_BASE_NOT_EXISTS);
        }
        Long userId = SecurityFrameworkUtils.getLoginUserId();
        boolean visible = !knowledgeBase.getIsPrivate()
                || isOwner(knowledgeBase, userId)
                || getMemberRole(knowledgeBase.getId(), userId) != null;
        if (!visible) {
            throw exception(KNOWLEDGE_BASE_ACCESS_DENIED);
        }
    }

    /**
     * 校验管理权限：所有者 或 ADMIN 成员
     */
    public void validateManagePermission(Long kbId) {
        KnowledgeBaseDO knowledgeBase = knowledgeBaseMapper.selectById(kbId);
        Long userId = SecurityFrameworkUtils.getLoginUserId();
        boolean manage = isOwner(knowledgeBase, userId)
                || KnowledgeBaseMemberRoleEnum.ADMIN.getRole().equals(getMemberRole(kbId, userId));
        if (!manage) {
            throw exception(KNOWLEDGE_BASE_UPDATE_DENIED);
        }
    }

    /**
     * 校验编辑权限：所有者 或 ADMIN/EDITOR 成员
     */
    public void validateEditPermission(Long kbId) {
        KnowledgeBaseDO knowledgeBase = knowledgeBaseMapper.selectById(kbId);
        Long userId = SecurityFrameworkUtils.getLoginUserId();
        String role = getMemberRole(kbId, userId);
        boolean edit = isOwner(knowledgeBase, userId)
                || KnowledgeBaseMemberRoleEnum.ADMIN.getRole().equals(role)
                || KnowledgeBaseMemberRoleEnum.EDITOR.getRole().equals(role);
        if (!edit) {
            throw exception(KNOWLEDGE_BASE_UPLOAD_DENIED);
        }
    }

    /**
     * 是否所有者
     */
    public boolean isOwner(KnowledgeBaseDO knowledgeBase, Long userId) {
        return knowledgeBase.getOwnerId().equals(userId);
    }

    /**
     * 获取用户在某知识库的角色：所有者→ADMIN；成员→其角色；否则 null
     */
    public String getMemberRole(Long kbId, Long userId) {
        if (kbId == null || userId == null) {
            return null;
        }
        KnowledgeBaseMemberDO member = knowledgeBaseMemberMapper.selectByKbIdAndUserId(kbId, userId);
        return member == null ? null : member.getRole();
    }

}
