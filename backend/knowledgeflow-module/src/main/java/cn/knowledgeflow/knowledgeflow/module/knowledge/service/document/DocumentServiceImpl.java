package cn.knowledgeflow.module.knowledge.service.document;

import cn.hutool.core.io.FileUtil;
import cn.hutool.core.util.IdUtil;
import cn.knowledgeflow.framework.common.pojo.PageResult;
import cn.knowledgeflow.framework.security.core.util.SecurityFrameworkUtils;
import cn.knowledgeflow.module.knowledge.controller.admin.document.vo.DocumentPageReqVO;
import cn.knowledgeflow.module.knowledge.dal.dataobject.document.DocumentDO;
import cn.knowledgeflow.module.knowledge.dal.dataobject.document.DocumentVersionDO;
import cn.knowledgeflow.module.knowledge.dal.dataobject.kb.KnowledgeBaseDO;
import cn.knowledgeflow.module.knowledge.dal.mysql.document.DocumentMapper;
import cn.knowledgeflow.module.knowledge.dal.mysql.document.DocumentVersionMapper;
import cn.knowledgeflow.module.knowledge.dal.mysql.kb.KnowledgeBaseMapper;
import cn.knowledgeflow.module.knowledge.enums.document.DocumentStatusEnum;
import cn.knowledgeflow.module.knowledge.framework.ai.AiServiceProperties;
import cn.knowledgeflow.module.knowledge.framework.minio.MinioProperties;
import cn.knowledgeflow.module.knowledge.service.kb.KnowledgeBaseService;
import io.minio.GetObjectArgs;
import io.minio.GetObjectResponse;
import io.minio.MinioClient;
import io.minio.PutObjectArgs;
import io.minio.RemoveObjectArgs;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.connection.stream.StreamRecords;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import javax.annotation.Resource;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import static cn.knowledgeflow.framework.common.exception.util.ServiceExceptionUtil.exception;
import static cn.knowledgeflow.module.knowledge.enums.ErrorCodeConstants.KNOWLEDGE_DOCUMENT_EMPTY;
import static cn.knowledgeflow.module.knowledge.enums.ErrorCodeConstants.KNOWLEDGE_DOCUMENT_FILE_TYPE_NOT_SUPPORT;
import static cn.knowledgeflow.module.knowledge.enums.ErrorCodeConstants.KNOWLEDGE_DOCUMENT_NOT_EXISTS;
import static cn.knowledgeflow.module.knowledge.enums.ErrorCodeConstants.KNOWLEDGE_DOCUMENT_PIPELINE_PUSH_FAIL;
import static cn.knowledgeflow.module.knowledge.enums.ErrorCodeConstants.KNOWLEDGE_DOCUMENT_UPLOAD_FAIL;

/**
 * 文档 Service 实现类
 *
 * 上传流程（任务书 T2.3）：multipart → 存 MinIO → 落库(status=pending) → XADD doc-pipeline → 返回。
 * 消息契约（doc-pipeline，field-value 扁平字符串）：
 *   documentId / kbId / objectName / filename / attempt(首次=1)
 */
@Slf4j
@Service
public class DocumentServiceImpl implements DocumentService {

    /**
     * 文件类型白名单（NFR-3）
     */
    private static final Set<String> ALLOWED_FILE_TYPES =
            new HashSet<>(Arrays.asList("pdf", "docx", "txt", "md"));

    @Resource
    private DocumentMapper documentMapper;
    @Resource
    private DocumentVersionMapper documentVersionMapper;
    @Resource
    private KnowledgeBaseMapper knowledgeBaseMapper;
    @Resource
    private KnowledgeBaseService knowledgeBaseService;
    @Resource
    private MinioClient minioClient;
    @Resource
    private MinioProperties minioProperties;
    @Resource
    private RestTemplate aiServiceRestTemplate;
    @Resource
    private AiServiceProperties aiServiceProperties;
    @Resource
    private StringRedisTemplate stringRedisTemplate;

    @Override
    public DocumentDO uploadDocument(Long kbId, MultipartFile file, String tags) {
        // 1. 校验知识库存在 + 编辑权限（owner/ADMIN/EDITOR）
        knowledgeBaseService.validateKnowledgeBaseExists(kbId);
        knowledgeBaseService.validateEditPermission(kbId);
        // 2. 校验文件非空 + 类型白名单
        if (file == null || file.isEmpty()) {
            throw exception(KNOWLEDGE_DOCUMENT_EMPTY);
        }
        String filename = file.getOriginalFilename();
        String fileType = FileUtil.extName(filename);
        if (fileType == null || !ALLOWED_FILE_TYPES.contains(fileType.toLowerCase())) {
            throw exception(KNOWLEDGE_DOCUMENT_FILE_TYPE_NOT_SUPPORT, fileType);
        }
        fileType = fileType.toLowerCase();
        // 3. 上传 MinIO（对象键：{kbId}/{uuid}.{ext}）
        String objectName = kbId + "/" + IdUtil.fastSimpleUUID() + "." + fileType;
        try {
            minioClient.putObject(PutObjectArgs.builder()
                    .bucket(minioProperties.getBucket())
                    .object(objectName)
                    .stream(file.getInputStream(), file.getSize(), -1)
                    .contentType(file.getContentType() == null ? "application/octet-stream" : file.getContentType())
                    .build());
        } catch (Exception e) {
            log.error("[uploadDocument][上传 MinIO 失败 kbId({}) filename({})]", kbId, filename, e);
            throw exception(KNOWLEDGE_DOCUMENT_UPLOAD_FAIL, e.getMessage());
        }
        // 4. 落库 status=pending
        DocumentDO document = new DocumentDO();
        document.setKbId(kbId);
        document.setUploaderId(SecurityFrameworkUtils.getLoginUserId());
        document.setFilename(filename);
        document.setObjectName(objectName);
        document.setFileType(fileType);
        document.setFileSize(file.getSize());
        document.setStatus(DocumentStatusEnum.PENDING.getStatus());
        document.setTags(tags);
        document.setChunkCount(0);
        document.setVersion(1);
        documentMapper.insert(document);
        // 5. 版本历史记录（version=1）
        DocumentVersionDO version = new DocumentVersionDO();
        version.setDocumentId(document.getId());
        version.setObjectName(objectName);
        version.setFileSize(file.getSize());
        version.setVersion(1);
        version.setCreatedBy(SecurityFrameworkUtils.getLoginUserId());
        documentVersionMapper.insert(version);
        // 6. 投递 Redis Stream（doc-pipeline）
        try {
            pushDocPipeline(document.getId(), kbId, objectName, filename);
        } catch (Exception e) {
            log.error("[uploadDocument][消息投递失败，回滚 documentId({})]", document.getId(), e);
            documentMapper.deleteById(document.getId());
            documentVersionMapper.deleteById(version.getId());
            try {
                minioClient.removeObject(RemoveObjectArgs.builder()
                        .bucket(minioProperties.getBucket()).object(objectName).build());
            } catch (Exception ignore) {
            }
            throw exception(KNOWLEDGE_DOCUMENT_PIPELINE_PUSH_FAIL);
        }
        // 7. 知识库 documentCount + 1
        incrementDocumentCount(kbId, 1);
        return document;
    }

    @Override
    public PageResult<DocumentDO> getDocumentPage(DocumentPageReqVO pageReqVO) {
        // 仅返回当前用户可见知识库下的文档
        List<Long> visibleKbIds = knowledgeBaseService.getKnowledgeBaseList().stream()
                .map(KnowledgeBaseDO::getId).collect(Collectors.toList());
        if (visibleKbIds.isEmpty()) {
            return PageResult.empty();
        }
        return documentMapper.selectPage(pageReqVO, visibleKbIds);
    }

    @Override
    public DocumentDO getDocument(Long id) {
        DocumentDO document = documentMapper.selectById(id);
        if (document == null) {
            throw exception(KNOWLEDGE_DOCUMENT_NOT_EXISTS);
        }
        // 校验知识库可见性（共享/所有者/成员）
        knowledgeBaseService.validateViewPermission(document.getKbId());
        return document;
    }

    @Override
    public void deleteDocuments(List<Long> ids) {
        for (Long id : ids) {
            DocumentDO document = documentMapper.selectById(id);
            if (document == null) {
                continue;
            }
            // 校验编辑权限
            knowledgeBaseService.validateEditPermission(document.getKbId());
            // 删除 MinIO 对象（尽力而为，对象不存在不阻断）
            try {
                minioClient.removeObject(RemoveObjectArgs.builder()
                        .bucket(minioProperties.getBucket()).object(document.getObjectName()).build());
            } catch (Exception e) {
                log.warn("[deleteDocuments][删除 MinIO 对象失败 objectName({})]", document.getObjectName(), e);
            }
            // 逻辑删除记录
            documentMapper.deleteById(id);
            // 同步删除 Qdrant 向量（Python /ai/documents/{id}，尽力而为，不阻断删除）
            try {
                aiServiceRestTemplate.delete(
                        aiServiceProperties.getBaseUrl() + "/ai/documents/" + id);
            } catch (Exception e) {
                log.warn("[deleteDocuments][删除 Qdrant 向量失败 documentId({})]", id, e);
            }
            // 知识库 documentCount - 1
            incrementDocumentCount(document.getKbId(), -1);
        }
    }

    @Override
    public GetObjectResponse downloadDocument(Long id) {
        DocumentDO document = getDocument(id);
        try {
            return minioClient.getObject(GetObjectArgs.builder()
                    .bucket(minioProperties.getBucket()).object(document.getObjectName()).build());
        } catch (Exception e) {
            log.error("[downloadDocument][下载失败 documentId({})]", id, e);
            throw exception(KNOWLEDGE_DOCUMENT_NOT_EXISTS);
        }
    }

    // ==================== 内部方法 ====================

    /**
     * 向 Redis Stream doc-pipeline 投递处理消息（字段扁平字符串，attempt=1）
     */
    private void pushDocPipeline(Long documentId, Long kbId, String objectName, String filename) {
        Map<String, String> fields = new HashMap<>();
        fields.put("documentId", String.valueOf(documentId));
        fields.put("kbId", String.valueOf(kbId));
        fields.put("objectName", objectName);
        fields.put("filename", filename);
        fields.put("attempt", "1");
        stringRedisTemplate.opsForStream().add(
                StreamRecords.newRecord().ofMap(fields).withStreamKey(DOC_PIPELINE_STREAM));
        log.info("[pushDocPipeline][已投递 documentId({}) 到 Stream({})]", documentId, DOC_PIPELINE_STREAM);
    }

    /**
     * 更新知识库冗余计数 documentCount
     */
    private void incrementDocumentCount(Long kbId, int delta) {
        KnowledgeBaseDO knowledgeBase = knowledgeBaseMapper.selectById(kbId);
        if (knowledgeBase == null) {
            return;
        }
        KnowledgeBaseDO updateObj = new KnowledgeBaseDO();
        updateObj.setId(kbId);
        updateObj.setDocumentCount(Math.max(0, (knowledgeBase.getDocumentCount() == null ? 0
                : knowledgeBase.getDocumentCount()) + delta));
        knowledgeBaseMapper.updateById(updateObj);
    }

}
