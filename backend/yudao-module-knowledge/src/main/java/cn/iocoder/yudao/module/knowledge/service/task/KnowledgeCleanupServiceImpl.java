package cn.iocoder.yudao.module.knowledge.service.task;

import cn.iocoder.yudao.framework.tenant.core.util.TenantUtils;
import cn.iocoder.yudao.module.knowledge.dal.mysql.document.DocumentMapper;
import cn.iocoder.yudao.module.knowledge.dal.mysql.document.DocumentVersionMapper;
import cn.iocoder.yudao.module.knowledge.dal.mysql.querylog.QueryLogMapper;
import cn.iocoder.yudao.module.knowledge.framework.ai.AiServiceProperties;
import cn.iocoder.yudao.module.knowledge.service.document.DocumentService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import javax.annotation.Resource;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * 运行时治理与资源清理实现（T6）
 *
 * 后台定时任务无登录租户上下文：所有 DB 操作包在 TenantUtils.executeIgnore 中
 * （documentId/version id 均为全局主键，按 id 精确操作安全）。
 */
@Slf4j
@Service
public class KnowledgeCleanupServiceImpl implements KnowledgeCleanupService {

    /**
     * 清理批大小（防锁大表）
     */
    private static final int BATCH_SIZE = 1000;
    /**
     * 查询日志保留天数
     */
    private static final int QUERY_LOG_RETENTION_DAYS = 30;
    /**
     * 文档版本保留数
     */
    private static final int VERSION_KEEP = 5;

    @Resource
    private StringRedisTemplate stringRedisTemplate;
    @Resource
    private QueryLogMapper queryLogMapper;
    @Resource
    private DocumentVersionMapper documentVersionMapper;
    @Resource
    private DocumentMapper documentMapper;
    @Resource
    private RestTemplate aiServiceRestTemplate;
    @Resource
    private AiServiceProperties aiServiceProperties;

    // ==================== T6.1 Redis Stream 修剪 ====================

    @Scheduled(cron = "0 30 3 * * ?") // 每日 03:30
    @Override
    public Long trimDocPipeline() {
        Long result = stringRedisTemplate.opsForStream()
                .trim(DocumentService.DOC_PIPELINE_STREAM, 2000, true); // XTRIM key MAXLEN ~ 2000
        log.info("[trimDocPipeline][Stream({}) 修剪完成，删除消息数: {}]",
                DocumentService.DOC_PIPELINE_STREAM, result);
        return result;
    }

    // ==================== T6.2 查询日志清理 ====================

    @Scheduled(cron = "0 0 4 * * ?") // 每日 04:00
    @Override
    public int cleanQueryLog() {
        return TenantUtils.executeIgnore(() -> {
            LocalDateTime before = LocalDateTime.now().minusDays(QUERY_LOG_RETENTION_DAYS);
            int total = 0;
            while (true) {
                List<Long> ids = queryLogMapper.selectIdsBeforeCreateTime(before, BATCH_SIZE);
                if (ids.isEmpty()) {
                    break;
                }
                queryLogMapper.deleteByIds(ids);
                total += ids.size();
                if (ids.size() < BATCH_SIZE) {
                    break;
                }
            }
            log.info("[cleanQueryLog][清理 {} 天前查询日志 {} 条]", QUERY_LOG_RETENTION_DAYS, total);
            return total;
        });
    }

    // ==================== T6.4 文档版本保留 ====================

    @Scheduled(cron = "0 30 4 * * ?") // 每日 04:30
    @Override
    public int cleanDocumentVersions() {
        return TenantUtils.executeIgnore(() -> {
            int total = 0;
            while (true) {
                List<Long> ids = documentVersionMapper.selectIdsExceedLimit(VERSION_KEEP, BATCH_SIZE);
                if (ids.isEmpty()) {
                    break;
                }
                documentVersionMapper.deleteByIds(ids);
                total += ids.size();
                if (ids.size() < BATCH_SIZE) {
                    break;
                }
            }
            log.info("[cleanDocumentVersions][每个文档保留最近 {} 个版本，清理 {} 条]", VERSION_KEEP, total);
            return total;
        });
    }

    // ==================== T6.5 孤儿向量兜底 ====================

    @Scheduled(cron = "0 0 5 * * ?") // 每日 05:00（低频）
    @Override
    public int cleanOrphanVectors() {
        return TenantUtils.executeIgnore(() -> {
            // 1. Qdrant scroll 遍历全部点，收集 documentId 集合
            Set<String> vectorDocIds = new HashSet<>();
            String qdrantUrl = aiServiceProperties.getQdrantUrl();
            Object nextOffset = null;
            do {
                Map<String, Object> body = new HashMap<>();
                body.put("limit", 1000);
                body.put("with_payload", List.of("documentId"));
                if (nextOffset != null) {
                    body.put("offset", nextOffset);
                }
                Map<?, ?> resp = aiServiceRestTemplate.postForObject(
                        qdrantUrl + "/collections/knowledge_segment/points/scroll", body, Map.class);
                if (resp == null) {
                    break;
                }
                Map<?, ?> result = (Map<?, ?>) resp.get("result");
                if (result == null) {
                    break;
                }
                List<?> points = (List<?>) result.get("points");
                if (points != null) {
                    for (Object pointObj : points) {
                        Map<?, ?> point = (Map<?, ?>) pointObj;
                        Map<?, ?> payload = (Map<?, ?>) point.get("payload");
                        if (payload != null && payload.get("documentId") != null) {
                            vectorDocIds.add(String.valueOf(payload.get("documentId")));
                        }
                    }
                }
                Object page = result.get("next_page_offset");
                if (page == null || "null".equals(String.valueOf(page))) {
                    nextOffset = null;
                } else {
                    nextOffset = page;
                }
            } while (nextOffset != null);

            // 2. 对每个 documentId 查 DB 是否存活，不存活则调 Python 删除向量
            int cleaned = 0;
            for (String docId : vectorDocIds) {
                try {
                    if (documentMapper.selectById(Long.valueOf(docId)) == null) {
                        aiServiceRestTemplate.delete(
                                aiServiceProperties.getBaseUrl() + "/ai/documents/" + docId);
                        cleaned++;
                        log.info("[cleanOrphanVectors][删除孤儿向量 documentId={}]", docId);
                    }
                } catch (Exception e) {
                    log.warn("[cleanOrphanVectors][处理 documentId={} 异常]", docId, e);
                }
            }
            log.info("[cleanOrphanVectors][扫描 {} 个向量文档，清理孤儿 {} 个]", vectorDocIds.size(), cleaned);
            return cleaned;
        });
    }

}
