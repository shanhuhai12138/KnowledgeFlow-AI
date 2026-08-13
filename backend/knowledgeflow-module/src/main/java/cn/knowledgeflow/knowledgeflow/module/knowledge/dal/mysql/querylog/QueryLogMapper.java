package cn.knowledgeflow.module.knowledge.dal.mysql.querylog;

import cn.knowledgeflow.framework.mybatis.core.mapper.BaseMapperX;
import cn.knowledgeflow.framework.mybatis.core.query.LambdaQueryWrapperX;
import cn.knowledgeflow.module.knowledge.dal.dataobject.querylog.QueryLogDO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Mapper
public interface QueryLogMapper extends BaseMapperX<QueryLogDO> {

    /**
     * 7 日搜索趋势（T3.3 看板：按日计数，日期降序）
     */
    @Select("SELECT DATE_FORMAT(create_time, '%Y-%m-%d') AS date, COUNT(*) AS count "
            + "FROM kb_query_log WHERE deleted = 0 "
            + "GROUP BY DATE_FORMAT(create_time, '%Y-%m-%d') ORDER BY date DESC LIMIT #{days}")
    List<Map<String, Object>> selectTrend(@Param("days") int days);

    /**
     * 热门查询词 Top（T3.3 看板）
     */
    @Select("SELECT query_text AS query, COUNT(*) AS count FROM kb_query_log "
            + "WHERE deleted = 0 AND query_text IS NOT NULL AND query_text <> '' "
            + "GROUP BY query_text ORDER BY count DESC LIMIT #{limit}")
    List<Map<String, Object>> selectHot(@Param("limit") int limit);

    /**
     * T6.2：查询在指定时间之前的日志 id（分批清理，防锁大表）
     */
    @Select("SELECT id FROM kb_query_log WHERE deleted = 0 AND create_time < #{before} "
            + "ORDER BY id LIMIT #{limit}")
    List<Long> selectIdsBeforeCreateTime(@Param("before") LocalDateTime before, @Param("limit") int limit);

    /**
     * 总数
     */
    default Long selectCountAll() {
        return selectCount(new LambdaQueryWrapperX<>());
    }

}
