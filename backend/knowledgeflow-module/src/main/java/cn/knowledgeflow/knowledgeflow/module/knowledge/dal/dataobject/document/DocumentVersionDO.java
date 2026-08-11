package cn.knowledgeflow.module.knowledge.dal.dataobject.document;

import cn.knowledgeflow.framework.tenant.core.db.TenantBaseDO;
import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 知识库文档版本历史 DO
 *
 * 对应项目书 §6 kb_document_version 表。
 */
@TableName("kb_document_version")
@KeySequence("kb_document_version_seq")
@Data
@EqualsAndHashCode(callSuper = true)
public class DocumentVersionDO extends TenantBaseDO {

    /**
     * 版本记录编号
     */
    private Long id;
    /**
     * 文档编号
     */
    private Long documentId;
    /**
     * MinIO 对象键
     */
    private String objectName;
    /**
     * 文件大小
     */
    private Long fileSize;
    /**
     * 内容哈希
     */
    private String contentHash;
    /**
     * 版本号
     */
    private Integer version;
    /**
     * 创建者用户编号
     */
    private Long createdBy;

}
