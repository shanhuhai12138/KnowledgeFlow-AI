package cn.iocoder.yudao.module.knowledge.service.kb;

import cn.iocoder.yudao.framework.common.pojo.PageResult;
import cn.iocoder.yudao.module.knowledge.controller.admin.kb.vo.KnowledgeBasePageReqVO;
import cn.iocoder.yudao.module.knowledge.controller.admin.kb.vo.KnowledgeBaseSaveReqVO;
import cn.iocoder.yudao.module.knowledge.dal.dataobject.kb.KnowledgeBaseDO;

import java.util.List;

/**
 * 知识库 Service
 *
 * 可见性规则：共享库租户内可见；私有库仅所有者/成员可见；管理操作仅所有者/ADMIN 成员。
 * 多租户隔离由框架 TenantLineInnerInterceptor 自动完成。
 */
public interface KnowledgeBaseService {

    /**
     * 创建知识库（创建者即所有者）
     */
    Long createKnowledgeBase(KnowledgeBaseSaveReqVO createReqVO);

    /**
     * 更新知识库（仅所有者或 ADMIN 成员）
     */
    void updateKnowledgeBase(KnowledgeBaseSaveReqVO updateReqVO);

    /**
     * 删除知识库（仅所有者或 ADMIN 成员；级联删除成员记录）
     */
    void deleteKnowledgeBase(Long id);

    /**
     * 获取知识库（校验可见性：共享 / 所有者 / 成员）
     */
    KnowledgeBaseDO getKnowledgeBase(Long id);

    /**
     * 分页查询当前用户可见的知识库
     */
    PageResult<KnowledgeBaseDO> getKnowledgeBasePage(KnowledgeBasePageReqVO pageReqVO);

    /**
     * 查询当前用户可见的全部知识库（不分页）
     */
    List<KnowledgeBaseDO> getKnowledgeBaseList();

    /**
     * 校验知识库存在
     */
    void validateKnowledgeBaseExists(Long id);

    /**
     * 校验管理权限：所有者 或 ADMIN 成员（供成员管理等内部调用）
     */
    void validateManagePermission(Long kbId);

    /**
     * 校验编辑权限：所有者 / ADMIN / EDITOR 成员（供文档上传、删除等调用）
     */
    void validateEditPermission(Long kbId);

    /**
     * 校验可见性：共享库 或 所有者 或 成员（供文档查询等内部调用）
     */
    void validateViewPermission(Long kbId);

}
