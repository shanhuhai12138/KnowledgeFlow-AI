package cn.knowledgeflow.module.knowledge.dal.mysql.kb;

import cn.knowledgeflow.framework.common.pojo.PageResult;
import cn.knowledgeflow.framework.mybatis.core.mapper.BaseMapperX;
import cn.knowledgeflow.framework.mybatis.core.query.LambdaQueryWrapperX;
import cn.knowledgeflow.module.knowledge.controller.admin.kb.vo.KnowledgeBaseMemberPageReqVO;
import cn.knowledgeflow.module.knowledge.dal.dataobject.kb.KnowledgeBaseMemberDO;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface KnowledgeBaseMemberMapper extends BaseMapperX<KnowledgeBaseMemberDO> {

    default PageResult<KnowledgeBaseMemberDO> selectPage(KnowledgeBaseMemberPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<KnowledgeBaseMemberDO>()
                .eqIfPresent(KnowledgeBaseMemberDO::getKbId, reqVO.getKbId())
                .eqIfPresent(KnowledgeBaseMemberDO::getUserId, reqVO.getUserId())
                .orderByAsc(KnowledgeBaseMemberDO::getId));
    }

    default KnowledgeBaseMemberDO selectByKbIdAndUserId(Long kbId, Long userId) {
        return selectOne(new LambdaQueryWrapperX<KnowledgeBaseMemberDO>()
                .eq(KnowledgeBaseMemberDO::getKbId, kbId)
                .eq(KnowledgeBaseMemberDO::getUserId, userId));
    }

    default Long selectCountByKbId(Long kbId) {
        return selectCount(KnowledgeBaseMemberDO::getKbId, kbId);
    }

}
