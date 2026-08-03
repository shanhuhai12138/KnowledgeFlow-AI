package cn.iocoder.yudao.module.knowledge.dal.mysql.kb;

import cn.iocoder.yudao.framework.common.pojo.PageResult;
import cn.iocoder.yudao.framework.mybatis.core.mapper.BaseMapperX;
import cn.iocoder.yudao.framework.mybatis.core.query.LambdaQueryWrapperX;
import cn.iocoder.yudao.module.knowledge.controller.admin.kb.vo.KnowledgeBasePageReqVO;
import cn.iocoder.yudao.module.knowledge.dal.dataobject.kb.KnowledgeBaseDO;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface KnowledgeBaseMapper extends BaseMapperX<KnowledgeBaseDO> {

    /**
     * 分页查询当前用户可见的知识库：
     * 共享库（is_private=0）｜ 自己所有（owner_id=userId）｜ 自己是成员（kb_member 有记录）
     * 多租户条件由框架 TenantLineInnerInterceptor 自动追加（同一租户内）。
     *
     * @param reqVO  分页筛选
     * @param userId 当前登录用户
     */
    default PageResult<KnowledgeBaseDO> selectVisiblePage(KnowledgeBasePageReqVO reqVO, Long userId) {
        return selectPage(reqVO, new LambdaQueryWrapperX<KnowledgeBaseDO>()
                .likeIfPresent(KnowledgeBaseDO::getName, reqVO.getName())
                .eqIfPresent(KnowledgeBaseDO::getIsPrivate, reqVO.getIsPrivate())
                .and(w -> w.eq(KnowledgeBaseDO::getIsPrivate, false)
                        .or().eq(KnowledgeBaseDO::getOwnerId, userId)
                        .or().inSql(KnowledgeBaseDO::getId,
                                "SELECT kb_id FROM kb_member WHERE user_id = " + userId + " AND deleted = 0"))
                .orderByDesc(KnowledgeBaseDO::getId));
    }

    /**
     * 查询当前用户可见的全部知识库（不分页，前端快捷列表/下拉用）
     */
    default List<KnowledgeBaseDO> selectVisibleList(Long userId) {
        return selectList(new LambdaQueryWrapperX<KnowledgeBaseDO>()
                .and(w -> w.eq(KnowledgeBaseDO::getIsPrivate, false)
                        .or().eq(KnowledgeBaseDO::getOwnerId, userId)
                        .or().inSql(KnowledgeBaseDO::getId,
                                "SELECT kb_id FROM kb_member WHERE user_id = " + userId + " AND deleted = 0"))
                .orderByDesc(KnowledgeBaseDO::getId));
    }

    default KnowledgeBaseDO selectByName(String name) {
        return selectOne(KnowledgeBaseDO::getName, name);
    }

    /**
     * 总数（T3.3 看板）
     */
    default Long selectCountAll() {
        return selectCount(new LambdaQueryWrapperX<>());
    }

}
