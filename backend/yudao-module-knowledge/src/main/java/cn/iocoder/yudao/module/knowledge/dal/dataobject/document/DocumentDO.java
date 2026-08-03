package cn.iocoder.yudao.module.knowledge.dal.dataobject.document;

import cn.iocoder.yudao.framework.tenant.core.db.TenantBaseDO;
import cn.iocoder.yudao.module.knowledge.enums.document.DocumentStatusEnum;
import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 知识库文档 DO
 *
 * 对应项目书 §6 kb_document 表；status 见 {@link DocumentStatusEnum}。
 */
@TableName("kb_document")
@KeySequence("kb_document_seq")
@Data
@EqualsAndHashCode(callSuper = true)
public class DocumentDO extends TenantBaseDO {

    /**
     * 文档编号
     */
    private Long id;
    /**
     * 知识库编号
     */
    private Long kbId;
    /**
     * 上传者用户编号
     */
    private Long uploaderId;
    /**
     * 文件名
     */
    private String filename;
    /**
     * MinIO 对象键
     */
    private String objectName;
    /**
     * 文件类型：pdf/docx/txt/md
     */
    private String fileType;
    /**
     * 文件大小（字节）
     */
    private Long fileSize;
    /**
     * 页数（解析后回填）
     */
    private Integer pageCount;
    /**
     * 状态：pending/processing/processed/failed
     */
    private String status;
    /**
     * 标签（逗号分隔）
     */
    private String tags;
    /**
     * 分块数量（处理后回填）
     */
    private Integer chunkCount;
    /**
     * 处理失败原因（T2.5 死信记录）
     */
    private String error;
    /**
     * 版本号
     */
    private Integer version;

}
