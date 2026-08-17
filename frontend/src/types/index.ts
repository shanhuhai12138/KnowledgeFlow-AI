/* ============================================================
   §9 字段契约 —— 与后端 DTO / 原型 MOCK 一致，禁止改名
   时间字段一律毫秒时间戳（Long），展示时由 dayjs 转换
   ============================================================ */

/** 知识库 KnowledgeBase */
export interface KnowledgeBase {
  id: number
  name: string
  description: string
  isPrivate: boolean
  documentCount: number
  memberCount: number
  ownerId?: number  // 所有者 ID（用于检测是否为 owner）
  createdAt: string | number
  updatedAt: string | number
}

/** 文档 Document */
export interface DocumentItem {
  id: number
  kbId: number
  kbName: string
  filename: string
  fileType: string // pdf / docx / txt / md / pptx ...
  fileSize: number
  pageCount: number
  status: 'pending' | 'processing' | 'processed' | 'failed'
  uploader: string
  tags: string[]
  createdAt: number | string
  updatedAt: number | string
}

/** 引用来源 Source */
export interface Source {
  documentId: number | string
  documentName: string
  page: number
  score: number
}

/** 消息 Message */
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  confidence?: number
  rating?: 'up' | 'down' | null
  createdAt: number | string
}

/** 会话 ChatSession */
export interface ChatSession {
  id: string
  title: string
  kbId?: number
  kbName: string
  createdAt: number | string
  updatedAt: number | string
}

/** 通用分页结果（若依 PageResult：list + total） */
export interface PageResult<T> {
  list: T[]
  total: number
}

/** 若依统一响应体 */
export interface ApiResponse<T = unknown> {
  code: number
  data: T
  message: string
}

/** 登录响应 */
export interface LoginResult {
  accessToken: string
  refreshToken: string
  expiresTime: number
  tokenType?: string
}

/** 用户信息（若依 GET /admin-api/system/auth/get-permission-info） */
export interface UserInfo {
  user: {
    id: number
    nickname: string
    avatar?: string
    username: string
    deptId?: number
    [k: string]: unknown
  }
  roles: string[]
  permissions: string[]
}
