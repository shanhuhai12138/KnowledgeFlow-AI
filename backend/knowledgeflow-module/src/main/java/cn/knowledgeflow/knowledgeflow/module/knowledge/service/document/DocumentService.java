package cn.knowledgeflow.module.knowledge.service.document;

import cn.knowledgeflow.framework.common.pojo.PageResult;
import cn.knowledgeflow.module.knowledge.controller.admin.document.vo.DocumentPageReqVO;
import cn.knowledgeflow.module.knowledge.dal.dataobject.document.DocumentDO;
import io.minio.GetObjectResponse;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

/**
 * 文档 Service
 *
 * 上传流程：校验权限与类型 → 存 MinIO → 落库(pending) → 投递 Redis Stream(doc-pipeline) → 返回。
 * 删除流程：删除 MinIO 对象 → 逻辑删除记录 → 知识库 documentCount 减一。
 */
public interface DocumentService {

    /**
     * Redis Stream key（doc-pipeline），消息契约见代码框架任务书 T2.3/T2.5
     */
    String DOC_PIPELINE_STREAM = "doc-pipeline";

    /**
     * 上传文档：存 MinIO + 落库(status=pending) + 投递 doc-pipeline 消息 + documentCount+1
     *
     * @return 落库后的文档
     */
    DocumentDO uploadDocument(Long kbId, MultipartFile file, String tags);

    /**
     * 分页查询文档（仅当前用户可见知识库下的文档）
     */
    PageResult<DocumentDO> getDocumentPage(DocumentPageReqVO pageReqVO);

    /**
     * 获得文档（校验知识库可见性）
     */
    DocumentDO getDocument(Long id);

    /**
     * 批量删除文档（校验编辑权限，级联删 MinIO 对象 + documentCount 减一）
     */
    void deleteDocuments(List<Long> ids);

    /**
     * 下载文档（返回 MinIO 对象流）
     */
    GetObjectResponse downloadDocument(Long id);

}
