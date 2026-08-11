package cn.knowledgeflow.module.knowledge.service.kb;

import cn.knowledgeflow.framework.common.pojo.PageResult;
import cn.knowledgeflow.framework.common.util.object.BeanUtils;
import cn.knowledgeflow.module.knowledge.controller.admin.kb.vo.KnowledgeBaseMemberPageReqVO;
import cn.knowledgeflow.module.knowledge.controller.admin.kb.vo.KnowledgeBaseMemberSaveReqVO;
import cn.knowledgeflow.module.knowledge.dal.dataobject.kb.KnowledgeBaseDO;
import cn.knowledgeflow.module.knowledge.dal.dataobject.kb.KnowledgeBaseMemberDO;
import cn.knowledgeflow.module.knowledge.dal.mysql.kb.KnowledgeBaseMapper;
import cn.knowledgeflow.module.knowledge.dal.mysql.kb.KnowledgeBaseMemberMapper;
import cn.knowledgeflow.module.knowledge.enums.kb.KnowledgeBaseMemberRoleEnum;
import cn.knowledgeflow.module.system.api.user.AdminUserApi;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;

import static cn.knowledgeflow.framework.common.exception.util.ServiceExceptionUtil.exception;
import static cn.knowledgeflow.module.knowledge.enums.ErrorCodeConstants.KNOWLEDGE_BASE_MEMBER_CANNOT_REMOVE_OWNER;
import static cn.knowledgeflow.module.knowledge.enums.ErrorCodeConstants.KNOWLEDGE_BASE_MEMBER_EXISTS;
import static cn.knowledgeflow.module.knowledge.enums.ErrorCodeConstants.KNOWLEDGE_BASE_MEMBER_NOT_EXISTS;
import static cn.knowledgeflow.module.knowledge.enums.ErrorCodeConstants.KNOWLEDGE_BASE_MEMBER_ROLE_ERROR;
import static cn.knowledgeflow.module.knowledge.enums.ErrorCodeConstants.KNOWLEDGE_BASE_MEMBER_USER_NOT_EXISTS;

/**
 * 知识库成员 Service 实现类
 */
@Service
public class KnowledgeBaseMemberServiceImpl implements KnowledgeBaseMemberService {

    @Resource
    private KnowledgeBaseMemberMapper knowledgeBaseMemberMapper;
    @Resource
    private KnowledgeBaseMapper knowledgeBaseMapper;
    @Resource
    private KnowledgeBaseService knowledgeBaseService;
    @Resource
    private AdminUserApi adminUserApi;

    @Override
    public Long createMember(KnowledgeBaseMemberSaveReqVO createReqVO) {
        // 1. 校验知识库存在 + 管理权限
        knowledgeBaseService.validateKnowledgeBaseExists(createReqVO.getKbId());
        knowledgeBaseService.validateManagePermission(createReqVO.getKbId());
        // 2. 校验角色合法
        if (!KnowledgeBaseMemberRoleEnum.isValid(createReqVO.getRole())) {
            throw exception(KNOWLEDGE_BASE_MEMBER_ROLE_ERROR, createReqVO.getRole());
        }
        // 3. 校验用户存在
        if (adminUserApi.getUser(createReqVO.getUserId()) == null) {
            throw exception(KNOWLEDGE_BASE_MEMBER_USER_NOT_EXISTS, createReqVO.getUserId());
        }
        // 4. 校验不能是所有者（所有者隐式 ADMIN）
        KnowledgeBaseDO knowledgeBase = knowledgeBaseMapper.selectById(createReqVO.getKbId());
        if (knowledgeBase.getOwnerId().equals(createReqVO.getUserId())) {
            throw exception(KNOWLEDGE_BASE_MEMBER_CANNOT_REMOVE_OWNER);
        }
        // 5. 校验不重复
        if (knowledgeBaseMemberMapper.selectByKbIdAndUserId(createReqVO.getKbId(), createReqVO.getUserId()) != null) {
            throw exception(KNOWLEDGE_BASE_MEMBER_EXISTS);
        }
        // 6. 新增成员 + 更新 memberCount
        KnowledgeBaseMemberDO member = BeanUtils.toBean(createReqVO, KnowledgeBaseMemberDO.class);
        knowledgeBaseMemberMapper.insert(member);
        refreshMemberCount(createReqVO.getKbId());
        return member.getId();
    }

    @Override
    public void deleteMember(Long id) {
        KnowledgeBaseMemberDO member = knowledgeBaseMemberMapper.selectById(id);
        if (member == null) {
            throw exception(KNOWLEDGE_BASE_MEMBER_NOT_EXISTS);
        }
        knowledgeBaseService.validateManagePermission(member.getKbId());
        knowledgeBaseMemberMapper.deleteById(id);
        refreshMemberCount(member.getKbId());
    }

    @Override
    public PageResult<KnowledgeBaseMemberDO> getMemberPage(KnowledgeBaseMemberPageReqVO pageReqVO) {
        return knowledgeBaseMemberMapper.selectPage(pageReqVO);
    }

    @Override
    public KnowledgeBaseMemberDO getMember(Long id) {
        return knowledgeBaseMemberMapper.selectById(id);
    }

    // ==================== 内部方法 ====================

    /**
     * 按实际成员数刷新知识库 member_count（冗余计数保持一致）
     */
    private void refreshMemberCount(Long kbId) {
        KnowledgeBaseDO knowledgeBase = knowledgeBaseMapper.selectById(kbId);
        if (knowledgeBase == null) {
            return;
        }
        KnowledgeBaseDO updateObj = new KnowledgeBaseDO();
        updateObj.setId(kbId);
        updateObj.setMemberCount(Math.toIntExact(knowledgeBaseMemberMapper.selectCountByKbId(kbId)));
        knowledgeBaseMapper.updateById(updateObj);
    }

}
