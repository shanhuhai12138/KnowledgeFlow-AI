package cn.iocoder.yudao.module.knowledge.service.kb;

import cn.iocoder.yudao.framework.common.pojo.PageResult;
import cn.iocoder.yudao.module.knowledge.controller.admin.kb.vo.KnowledgeBaseMemberPageReqVO;
import cn.iocoder.yudao.module.knowledge.controller.admin.kb.vo.KnowledgeBaseMemberSaveReqVO;
import cn.iocoder.yudao.module.knowledge.dal.dataobject.kb.KnowledgeBaseMemberDO;

/**
 * 知识库成员 Service
 *
 * 成员管理仅所有者/ADMIN 可操作；所有者不写入成员表（隐式 ADMIN）。
 */
public interface KnowledgeBaseMemberService {

    /**
     * 添加成员（同步更新知识库 memberCount）
     */
    Long createMember(KnowledgeBaseMemberSaveReqVO createReqVO);

    /**
     * 移除成员（同步更新知识库 memberCount）
     */
    void deleteMember(Long id);

    /**
     * 分页查询成员
     */
    PageResult<KnowledgeBaseMemberDO> getMemberPage(KnowledgeBaseMemberPageReqVO pageReqVO);

    /**
     * 查询成员记录
     */
    KnowledgeBaseMemberDO getMember(Long id);

}
