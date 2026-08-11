package cn.knowledgeflow.module.knowledge.enums;

import cn.knowledgeflow.framework.common.exception.ErrorCode;

/**
 * Knowledge 知识库模块错误码枚举类
 *
 * knowledge 模块，使用 1-011-000-000 段
 */
public interface ErrorCodeConstants {

    // ========== 知识库 1-011-000-000 ==========
    ErrorCode KNOWLEDGE_BASE_NOT_EXISTS = new ErrorCode(1_011_000_000, "知识库不存在");
    ErrorCode KNOWLEDGE_BASE_NAME_DUPLICATE = new ErrorCode(1_011_000_001, "知识库名称【{}】已存在");
    ErrorCode KNOWLEDGE_BASE_ACCESS_DENIED = new ErrorCode(1_011_000_002, "无权访问该知识库（非所有者或成员）");
    ErrorCode KNOWLEDGE_BASE_UPDATE_DENIED = new ErrorCode(1_011_000_003, "无权操作该知识库（仅所有者或管理员）");
    ErrorCode KNOWLEDGE_BASE_UPLOAD_DENIED = new ErrorCode(1_011_000_004, "无权上传文档（仅所有者/管理员/编辑者）");

    // ========== 知识库成员 1-011-001-000 ==========
    ErrorCode KNOWLEDGE_BASE_MEMBER_EXISTS = new ErrorCode(1_011_001_000, "该用户已是知识库成员");
    ErrorCode KNOWLEDGE_BASE_MEMBER_NOT_EXISTS = new ErrorCode(1_011_001_001, "该成员记录不存在");
    ErrorCode KNOWLEDGE_BASE_MEMBER_USER_NOT_EXISTS = new ErrorCode(1_011_001_002, "用户【{}】不存在");
    ErrorCode KNOWLEDGE_BASE_MEMBER_CANNOT_REMOVE_OWNER = new ErrorCode(1_011_001_003, "不能移除知识库所有者");
    ErrorCode KNOWLEDGE_BASE_MEMBER_ROLE_ERROR = new ErrorCode(1_011_001_004, "非法角色【{}】");

    // ========== 文档模块 1-011-002-000 ==========
    ErrorCode KNOWLEDGE_DOCUMENT_NOT_EXISTS = new ErrorCode(1_011_002_000, "文档不存在");
    ErrorCode KNOWLEDGE_DOCUMENT_FILE_TYPE_NOT_SUPPORT = new ErrorCode(1_011_002_001, "不支持的文件类型【{}】，仅支持 pdf/docx/txt/md");
    ErrorCode KNOWLEDGE_DOCUMENT_EMPTY = new ErrorCode(1_011_002_002, "上传文件不能为空");
    ErrorCode KNOWLEDGE_DOCUMENT_UPLOAD_FAIL = new ErrorCode(1_011_002_003, "文件上传 MinIO 失败：{}");
    ErrorCode KNOWLEDGE_DOCUMENT_PIPELINE_PUSH_FAIL = new ErrorCode(1_011_002_004, "文档已保存但处理消息投递失败，请稍后重试");

    // ========== 搜索问答模块 1-011-003-000 ==========
    ErrorCode AI_SERVICE_UNAVAILABLE = new ErrorCode(1_011_003_000, "AI 服务不可用（请确认 ai-service 已启动）：{}");
    ErrorCode AI_SERVICE_ERROR = new ErrorCode(1_011_003_001, "AI 服务调用失败（HTTP {}）：{}");

    // ========== 运行时治理 1-011-004-000 ==========
    ErrorCode KNOWLEDGE_CLEANUP_TYPE_ERROR = new ErrorCode(1_011_004_000, "未知的清理类型【{}】，可选：stream/querylog/version/orphan");

}
