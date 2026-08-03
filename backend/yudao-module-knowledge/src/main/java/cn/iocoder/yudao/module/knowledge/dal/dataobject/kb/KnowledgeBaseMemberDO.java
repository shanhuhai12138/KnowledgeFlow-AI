package cn.iocoder.yudao.module.knowledge.dal.dataobject.kb;

import cn.iocoder.yudao.framework.tenant.core.db.TenantBaseDO;
import cn.iocoder.yudao.module.knowledge.enums.kb.KnowledgeBaseMemberRoleEnum;
import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 知识库成员 DO
 *
 * 对应项目书 §6 kb_member 表；所有者不写入本表（隐式 ADMIN）。
 */
@TableName("kb_member")
@KeySequence("kb_member_seq")
@Data
@EqualsAndHashCode(callSuper = true)
public class KnowledgeBaseMemberDO extends TenantBaseDO {

    /**
     * 成员记录编号
     */
    private Long id;
    /**
     * 知识库编号
     */
    private Long kbId;
    /**
     * 用户编号
     */
    private Long userId;
    /**
     * 角色：ADMIN/EDITOR/VIEWER，见 {@link KnowledgeBaseMemberRoleEnum}
     */
    private String role;

}
