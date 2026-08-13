package cn.knowledgeflow.module.infra.dal.mysql.demo.demo03.erp;

import cn.knowledgeflow.framework.common.pojo.PageParam;
import cn.knowledgeflow.framework.common.pojo.PageResult;
import cn.knowledgeflow.framework.mybatis.core.mapper.BaseMapperX;
import cn.knowledgeflow.framework.mybatis.core.query.LambdaQueryWrapperX;
import cn.knowledgeflow.module.infra.dal.dataobject.demo.demo03.Demo03GradeDO;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

/**
 * 学生班级 Mapper
 *
 * @author 芋道源码
 */
@Mapper
public interface Demo03GradeErpMapper extends BaseMapperX<Demo03GradeDO> {

    default PageResult<Demo03GradeDO> selectPage(PageParam reqVO, Long studentId) {
        return selectPage(reqVO, new LambdaQueryWrapperX<Demo03GradeDO>()
                .eq(Demo03GradeDO::getStudentId, studentId)
                .orderByDesc(Demo03GradeDO::getId));
    }

    default Demo03GradeDO selectByStudentId(Long studentId) {
        return selectOne(Demo03GradeDO::getStudentId, studentId);
    }

    default int deleteByStudentId(Long studentId) {
        return delete(Demo03GradeDO::getStudentId, studentId);
    }

    default int deleteByStudentIds(List<Long> studentIds) {
        return deleteBatch(Demo03GradeDO::getStudentId, studentIds);
    }

}
