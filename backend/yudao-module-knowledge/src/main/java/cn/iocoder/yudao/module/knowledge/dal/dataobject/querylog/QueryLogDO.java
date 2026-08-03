package cn.iocoder.yudao.module.knowledge.dal.dataobject.querylog;

import cn.iocoder.yudao.framework.tenant.core.db.TenantBaseDO;
import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 搜索问答日志 DO
 *
 * 对应项目书 §6 kb_query_log 表。
 */
@TableName("kb_query_log")
@KeySequence("kb_query_log_seq")
@Data
@EqualsAndHashCode(callSuper = true)
public class QueryLogDO extends TenantBaseDO {

    /**
     * 日志编号
     */
    private Long id;
    /**
     * 用户编号
     */
    private Long userId;
    /**
     * 知识库编号
     */
    private Long kbId;
    /**
     * 查询内容
     */
    private String queryText;
    /**
     * 耗时（毫秒）
     */
    private Integer tookMs;
    /**
     * 命中数量
     */
    private Integer hitCount;

}
