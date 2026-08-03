import request from './request'
import type { KnowledgeBase, PageResult } from '@/types'

/** 知识库分页：GET /admin-api/knowledge/kb/page（若依分页参数 pageNo/pageSize） */
export function getKbPageApi(params: { pageNo?: number; pageSize?: number; name?: string }) {
  return request.get<unknown, PageResult<KnowledgeBase>>('/admin-api/knowledge/kb/page', { params })
}

/** 创建知识库：POST /admin-api/knowledge/kb/create */
export function createKbApi(data: { name: string; description: string; isPrivate: boolean }) {
  return request.post<unknown, number>('/admin-api/knowledge/kb/create', data)
}

/** 更新知识库：PUT /admin-api/knowledge/kb/update */
export function updateKbApi(data: { id: number; name?: string; description?: string; isPrivate?: boolean }) {
  return request.put<unknown, boolean>('/admin-api/knowledge/kb/update', data)
}

/** 删除知识库：DELETE /admin-api/knowledge/kb/delete?id= */
export function deleteKbApi(id: number) {
  return request.delete<unknown, boolean>('/admin-api/knowledge/kb/delete', { params: { id } })
}

/** 知识库成员（后端真实契约 /knowledge/kb-member） */
export interface KbMember {
  id: number
  kbId: number
  userId: number
  role: 'ADMIN' | 'EDITOR' | 'VIEWER'
  createdAt: string
}

/** 成员分页：GET /admin-api/knowledge/kb-member/page?kbId= */
export function listKbMembersApi(kbId: number) {
  return request.get<unknown, PageResult<KbMember>>('/admin-api/knowledge/kb-member/page', {
    params: { kbId, pageNo: 1, pageSize: 100 },
  })
}

/** 添加成员：POST /admin-api/knowledge/kb-member/create（role: ADMIN/EDITOR/VIEWER） */
export function addKbMemberApi(data: { kbId: number; userId: number; role: string }) {
  return request.post<unknown, number>('/admin-api/knowledge/kb-member/create', data)
}

/** 移除成员：DELETE /admin-api/knowledge/kb-member/delete?id=（成员记录 id） */
export function removeKbMemberApi(id: number) {
  return request.delete<unknown, boolean>('/admin-api/knowledge/kb-member/delete', { params: { id } })
}

/** 系统用户分页（添加成员时选人）：GET /admin-api/system/user/page */
export function getSystemUserPageApi(params: { pageNo?: number; pageSize?: number; username?: string }) {
  return request.get<unknown, PageResult<{ id: number; username: string; nickname: string }>>(
    '/admin-api/system/user/page',
    { params },
  )
}
