package cn.iocoder.yudao.module.knowledge.enums.kb;

import lombok.AllArgsConstructor;
import lombok.Getter;

import java.util.Arrays;

/**
 * 知识库成员角色枚举
 *
 * ADMIN 管理员（可管理成员/编辑文档）｜ EDITOR 编辑者（可上传/编辑文档）｜ VIEWER 查看者（只读）
 * 知识库所有者（owner）隐式拥有 ADMIN 权限，不写入 kb_member 表。
 */
@Getter
@AllArgsConstructor
public enum KnowledgeBaseMemberRoleEnum {

    ADMIN("ADMIN"),
    EDITOR("EDITOR"),
    VIEWER("VIEWER");

    private final String role;

    public static boolean isValid(String role) {
        return Arrays.stream(values()).anyMatch(e -> e.getRole().equals(role));
    }

}
