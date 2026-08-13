package cn.knowledgeflow.module.knowledge.dal.dataobject.kb;

import cn.knowledgeflow.framework.tenant.core.db.TenantBaseDO;
import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 知识库 DO
 *
 * 字段与项目书 §6 kb_knowledge_base 对应；tenant_id 由 TenantBaseDO 提供，框架自动多租户过滤。
 */
@TableName("kb_knowledge_base")
@KeySequence("kb_knowledge_base_seq")
@Data
@EqualsAndHashCode(callSuper = true)
public class KnowledgeBaseDO extends TenantBaseDO {

    /**
     * 知识库编号
     */
    private Long id;
    /**
     * 知识库名称
     */
    private String name;
    /**
     * 知识库描述
     */
    private String description;
    /**
     * 是否私有：true=私有（仅所有者/成员可见），false=共享（租户内可见）
     */
    private Boolean isPrivate;
    /**
     * 所有者用户编号
     */
    private Long ownerId;
    /**
     * 文档数量（冗余计数，T2.3 更新）
     */
    private Integer documentCount;
    /**
     * 成员数量（冗余计数）
     */
    private Integer memberCount;

}
