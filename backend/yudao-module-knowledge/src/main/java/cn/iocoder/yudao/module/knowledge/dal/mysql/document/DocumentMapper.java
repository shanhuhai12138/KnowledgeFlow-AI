package cn.iocoder.yudao.module.knowledge.dal.mysql.document;

import cn.iocoder.yudao.framework.common.pojo.PageResult;
import cn.iocoder.yudao.framework.mybatis.core.mapper.BaseMapperX;
import cn.iocoder.yudao.framework.mybatis.core.query.LambdaQueryWrapperX;
import cn.iocoder.yudao.module.knowledge.controller.admin.document.vo.DocumentPageReqVO;
import cn.iocoder.yudao.module.knowledge.dal.dataobject.document.DocumentDO;
import org.apache.ibatis.annotations.Mapper;

import java.util.Collection;

@Mapper
public interface DocumentMapper extends BaseMapperX<DocumentDO> {

    /**
     * 分页查询文档。
     * visibleKbIds 为当前用户可见的知识库集合（kbId 未指定时用于过滤可见范围；指定 kbId 时该集合仅用于兜底校验）。
     * 多租户条件由框架自动追加。
     */
    default PageResult<DocumentDO> selectPage(DocumentPageReqVO reqVO, Collection<Long> visibleKbIds) {
        return selectPage(reqVO, new LambdaQueryWrapperX<DocumentDO>()
                .eqIfPresent(DocumentDO::getKbId, reqVO.getKbId())
                .eqIfPresent(DocumentDO::getStatus, reqVO.getStatus())
                .eqIfPresent(DocumentDO::getFileType, reqVO.getFileType())
                .likeIfPresent(DocumentDO::getFilename, reqVO.getFilename())
                .inIfPresent(DocumentDO::getKbId, visibleKbIds)
                .orderByDesc(DocumentDO::getId));
    }

    default Long selectCountByKbId(Long kbId) {
        return selectCount(DocumentDO::getKbId, kbId);
    }

    /**
     * 文档类型分布（T3.3 看板：按 file_type 分组）
     */
    @org.apache.ibatis.annotations.Select("SELECT file_type AS type, COUNT(*) AS count FROM kb_document "
            + "WHERE deleted = 0 GROUP BY file_type ORDER BY count DESC")
    java.util.List<java.util.Map<String, Object>> selectDocTypes();

}
