package cn.iocoder.yudao.module.knowledge.dal.mysql.kb;

import cn.iocoder.yudao.framework.common.pojo.PageResult;
import cn.iocoder.yudao.framework.mybatis.core.mapper.BaseMapperX;
import cn.iocoder.yudao.framework.mybatis.core.query.LambdaQueryWrapperX;
import cn.iocoder.yudao.module.knowledge.controller.admin.kb.vo.KnowledgeBaseMemberPageReqVO;
import cn.iocoder.yudao.module.knowledge.dal.dataobject.kb.KnowledgeBaseMemberDO;
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
