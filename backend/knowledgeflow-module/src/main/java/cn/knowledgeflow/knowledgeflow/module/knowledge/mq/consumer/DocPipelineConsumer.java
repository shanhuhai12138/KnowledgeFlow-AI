package cn.knowledgeflow.module.knowledge.mq.consumer;

import cn.knowledgeflow.framework.tenant.core.aop.TenantIgnore;
import cn.knowledgeflow.module.knowledge.dal.dataobject.document.DocumentDO;
import cn.knowledgeflow.module.knowledge.dal.mysql.document.DocumentMapper;
import cn.knowledgeflow.module.knowledge.enums.document.DocumentStatusEnum;
import cn.knowledgeflow.module.knowledge.framework.ai.AiServiceProperties;
import cn.knowledgeflow.module.knowledge.framework.minio.MinioProperties;
import cn.knowledgeflow.module.knowledge.service.document.parser.DocumentContentParser;
import io.minio.GetObjectArgs;
import io.minio.GetObjectResponse;
import io.minio.MinioClient;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Lazy;
import org.springframework.data.redis.connection.stream.MapRecord;
import org.springframework.data.redis.connection.stream.RecordId;
import org.springframework.data.redis.connection.stream.StreamRecords;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.stream.StreamListener;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import javax.annotation.Resource;
import java.util.HashMap;
import java.util.Map;

/**
 * doc-pipeline 消费者（任务书 T2.5）
 *
 * 流程：XREADGROUP 消费 → 文档不存在幂等跳过(XACK) → 状态置 processing → 解析文本 →
 *       POST /ai/ingest → 成功 processed + chunkCount 回填(XACK)；失败 attempt+1 重新入队，
 *       attempt > 3 置 failed + error(XACK 死信)。
 *
 * 后台消费者无登录租户上下文，onMessage 方法级 @TenantIgnore（AOP 切点仅匹配方法注解），
 * 按 documentId（全局主键）精确回写，安全。
 */
@Slf4j
@Component
public class DocPipelineConsumer implements StreamListener<String, MapRecord<String, String, String>> {

    public static final String STREAM = "doc-pipeline";
    public static final String GROUP = "doc-pipeline-group";
    public static final String CONSUMER = "ingest-consumer";
    /**
     * 最大尝试次数（失败重试 3 次）
     */
    public static final int MAX_ATTEMPT = 3;

    @Resource
    private DocumentMapper documentMapper;
    @Resource
    private MinioClient minioClient;
    @Resource
    private MinioProperties minioProperties;
    @Resource
    private RestTemplate aiServiceRestTemplate;
    @Resource
    private AiServiceProperties aiServiceProperties;
    @Resource
    private DocumentContentParser contentParser;
    @Resource
    private StringRedisTemplate stringRedisTemplate;

    @Override
    @TenantIgnore // 后台消费者：忽略租户过滤（documentId 全局主键精确回写）
    public void onMessage(MapRecord<String, String, String> message) {
        RecordId recordId = message.getId();
        Map<String, String> fields = message.getValue();
        Long documentId = Long.valueOf(fields.get("documentId"));
        Long kbId = Long.valueOf(fields.get("kbId"));
        String objectName = fields.get("objectName");
        String filename = fields.get("filename");
        int attempt = Integer.parseInt(fields.getOrDefault("attempt", "1"));
        try {
            process(documentId, kbId, objectName, filename);
            ack(recordId); // 成功：确认出队
            log.info("[onMessage][文档({}) 处理成功 kbId({}) attempt({})]", documentId, kbId, attempt);
        } catch (Exception e) {
            if (attempt >= MAX_ATTEMPT) {
                // 死信：置 failed + 记录 error + XACK（不再重试）
                markFailed(documentId, e.getMessage());
                ack(recordId);
                log.error("[onMessage][文档({}) 重试 {} 次仍失败，置 failed 死信]", documentId, attempt, e);
            } else {
                // 重试：XACK 出队后重新入队 attempt+1
                ack(recordId);
                requeue(documentId, kbId, objectName, filename, attempt + 1);
                log.warn("[onMessage][文档({}) 处理失败，重试第 {}/{} 次]", documentId, attempt, MAX_ATTEMPT, e);
            }
        }
    }

    // ==================== 处理逻辑 ====================

    private void process(Long documentId, Long kbId, String objectName, String filename) throws Exception {
        // 1. 幂等：文档不存在（已删除）→ 跳过
        DocumentDO document = documentMapper.selectById(documentId);
        if (document == null) {
            log.warn("[process][文档({}) 不存在（可能已删除），幂等跳过]", documentId);
            return;
        }
        // 2. 幂等：已处理完成或已死信 → 跳过（防止重复向量化；pending/processing 继续处理，支持重试）
        String status = document.getStatus();
        if (DocumentStatusEnum.PROCESSED.getStatus().equals(status)
                || DocumentStatusEnum.FAILED.getStatus().equals(status)) {
            log.info("[process][文档({}) 状态为 {}，已终态，跳过]", documentId, status);
            return;
        }
        // 3. 置 processing（处理中允许查询处理状态）
        updateStatus(documentId, DocumentStatusEnum.PROCESSING.getStatus(), null, null);
        // 4. 从 MinIO 读取并解析全文
        String content;
        try (GetObjectResponse object = minioClient.getObject(GetObjectArgs.builder()
                .bucket(minioProperties.getBucket()).object(objectName).build())) {
            content = contentParser.parse(object, document.getFileType());
        }
        if (content == null || content.trim().isEmpty()) {
            throw new IllegalArgumentException("文档内容为空，无法处理");
        }
        // 5. 调 Python /ai/ingest（T4.0 契约，documentId 幂等）
        Map<String, Object> payload = new HashMap<>();
        payload.put("documentId", String.valueOf(documentId));
        payload.put("kbId", String.valueOf(kbId));
        payload.put("filename", filename);
        payload.put("fileType", document.getFileType());
        payload.put("content", content);
        ResponseEntity<Map> resp = aiServiceRestTemplate.postForEntity(
                aiServiceProperties.getBaseUrl() + "/ai/ingest", payload, Map.class);
        if (!resp.getStatusCode().is2xxSuccessful()) {
            throw new RuntimeException("ai-service /ai/ingest 返回 HTTP " + resp.getStatusCode().value());
        }
        // 6. 回写 processed + chunkCount
        Map body = resp.getBody();
        int chunkCount = body == null ? 0
                : body.get("chunkCount") instanceof Number ? ((Number) body.get("chunkCount")).intValue() : 0;
        updateStatus(documentId, DocumentStatusEnum.PROCESSED.getStatus(), null, chunkCount);
    }

    // ==================== 状态回写 ====================

    private void updateStatus(Long documentId, String status, String error, Integer chunkCount) {
        DocumentDO updateObj = new DocumentDO();
        updateObj.setId(documentId);
        updateObj.setStatus(status);
        updateObj.setError(error);
        updateObj.setChunkCount(chunkCount);
        documentMapper.updateById(updateObj);
    }

    private void markFailed(Long documentId, String errorMsg) {
        String error = errorMsg == null ? "未知错误" : errorMsg.substring(0, Math.min(errorMsg.length(), 500));
        updateStatus(documentId, DocumentStatusEnum.FAILED.getStatus(), error, null);
        log.warn("[markFailed][文档({}) 标记 failed：{}]", documentId, error);
    }

    // ==================== Stream 操作 ====================

    private void ack(RecordId recordId) {
        stringRedisTemplate.opsForStream().acknowledge(STREAM, GROUP, recordId);
    }

    private void requeue(Long documentId, Long kbId, String objectName, String filename, int attempt) {
        Map<String, String> fields = new HashMap<>();
        fields.put("documentId", String.valueOf(documentId));
        fields.put("kbId", String.valueOf(kbId));
        fields.put("objectName", objectName);
        fields.put("filename", filename);
        fields.put("attempt", String.valueOf(attempt));
        stringRedisTemplate.opsForStream().add(
                StreamRecords.newRecord().ofMap(fields).withStreamKey(STREAM));
    }

}
