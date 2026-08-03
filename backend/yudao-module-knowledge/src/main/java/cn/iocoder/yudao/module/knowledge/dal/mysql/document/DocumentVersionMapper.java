package cn.iocoder.yudao.module.knowledge.dal.mysql.document;

import cn.iocoder.yudao.framework.mybatis.core.mapper.BaseMapperX;
import cn.iocoder.yudao.module.knowledge.dal.dataobject.document.DocumentVersionDO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface DocumentVersionMapper extends BaseMapperX<DocumentVersionDO> {

    /**
     * T6.4：查询每个文档超过 keep 个版本的旧版本 id（id 大的为较新版本），分批删
     */
    @Select("SELECT v.id FROM kb_document_version v "
            + "WHERE v.deleted = 0 AND (SELECT COUNT(*) FROM kb_document_version v2 "
            + "WHERE v2.document_id = v.document_id AND v2.deleted = 0 AND v2.id > v.id) >= #{keep} "
            + "ORDER BY v.id LIMIT #{limit}")
    List<Long> selectIdsExceedLimit(@Param("keep") int keep, @Param("limit") int limit);

}
