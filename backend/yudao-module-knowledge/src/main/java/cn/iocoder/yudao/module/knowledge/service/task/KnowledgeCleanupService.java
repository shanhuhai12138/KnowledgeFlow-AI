package cn.iocoder.yudao.module.knowledge.service.task;

/**
 * 运行时治理与资源清理（T6）
 *
 * 集中管理定时清理任务（@Scheduled cron，每日低频）：
 *   T6.1 trimDocPipeline      — Redis Stream doc-pipeline 修剪（MAXLEN ~2000）
 *   T6.2 cleanQueryLog        — 查询日志清理（30 天前，分批删）
 *   T6.4 cleanDocumentVersions— 文档版本保留最近 5 个
 *   T6.5 cleanOrphanVectors   — Qdrant 孤儿向量兜底（低频每日）
 *
 * 全部幂等、可重复执行；方法同时提供手动触发（POST /knowledge/cleanup/run）。
 */
public interface KnowledgeCleanupService {

    /**
     * T6.1 修剪 doc-pipeline（XTRIM MAXLEN ~2000）
     *
     * @return 删除的消息数
     */
    Long trimDocPipeline();

    /**
     * T6.2 清理 30 天前的查询日志（分批 1000，防锁大表）
     *
     * @return 删除条数
     */
    int cleanQueryLog();

    /**
     * T6.4 每个文档只保留最近 5 个版本（分批删）
     *
     * @return 删除条数
     */
    int cleanDocumentVersions();

    /**
     * T6.5 清理 Qdrant 孤儿向量（DB 中已删除文档的残留点，低频每日）
     *
     * @return 清理的文档数
     */
    int cleanOrphanVectors();

}
