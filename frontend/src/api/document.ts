import request, { requestRaw, API_BASE } from './request'
import type { DocumentItem, PageResult } from '@/types'

/** 文档分页：GET /admin-api/knowledge/document/page（若依分页参数 pageNo/pageSize） */
export function getDocumentPageApi(params: {
  pageNo?: number
  pageSize?: number
  kbId?: number
  fileType?: string
  status?: string
  filename?: string
}) {
  return request.get<unknown, PageResult<DocumentItem>>('/admin-api/knowledge/document/page', { params })
}

/** 文档详情：GET /admin-api/knowledge/document/get?id= */
export function getDocumentApi(id: number) {
  return request.get<unknown, DocumentItem>('/admin-api/knowledge/document/get', { params: { id } })
}

/** 上传文档：POST /admin-api/knowledge/document/upload（multipart: kbId + file + tags） */
export function uploadDocumentApi(
  kbId: number,
  file: File,
  tags: string,
  onProgress?: (percent: number) => void,
) {
  const form = new FormData()
  form.append('kbId', String(kbId))
  form.append('file', file)
  form.append('tags', tags)
  return requestRaw<{ code: number; data: unknown; message: string }>({
    method: 'post',
    url: '/admin-api/knowledge/document/upload',
    data: form,
    headers: {
      'tenant-id': '1',
      Authorization: `Bearer ${localStorage.getItem('kf_access_token') || ''}`,
    },
    onUploadProgress: (e) => {
      if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100))
    },
  })
}

/** 删除文档：DELETE /admin-api/knowledge/document/delete?ids=1,2 */
export function deleteDocumentsApi(ids: number[]) {
  return request.delete<unknown, boolean>('/admin-api/knowledge/document/delete', {
    params: { ids: ids.join(',') },
  })
}

/** 下载文档：GET /admin-api/knowledge/document/download?id= */
export function downloadUrl(id: number) {
  const token = localStorage.getItem('kf_access_token') || ''
  // API_BASE：dev 直连 48080；容器版为相对路径由 nginx 反代（部署到任意机器可用）
  return `${API_BASE}/admin-api/knowledge/document/download?id=${id}&token=${token}`
}

/** 获取文档内容（预览）：GET /admin-api/knowledge/document/content?id= */
export function getContentApi(id: number) {
  return request.get<unknown, string>('/admin-api/knowledge/document/content', { params: { id } })
}
