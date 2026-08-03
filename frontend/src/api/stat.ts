import { requestRaw, getToken } from './request'

/**
 * 看板统计接口（后端 Agent A 开发中，契约：
 * GET /admin-api/knowledge/stat/overview|trend|doc-types|hot）
 * 全部走 requestRaw 裸 axios（不带全局拦截器），失败静默返回 null，
 * 由页面降级为占位 + 重试——避免 404 时全局弹错 toast。
 */

export interface StatOverview {
  documentCount: number
  queryCount: number
  llmCallCount: number
  kbCount: number
}

export interface StatTrendItem {
  date: string
  count: number
}

export interface StatDocType {
  type: string
  count: number
}

export interface StatHotItem {
  query: string
  count: number
}

interface RawRes<T> {
  code: number
  data: T
  message?: string
  msg?: string
}

async function getRaw<T>(url: string): Promise<T | null> {
  try {
    const res = await requestRaw<RawRes<T>>({
      url,
      method: 'get',
      headers: {
        'tenant-id': '1',
        Authorization: `Bearer ${getToken()}`,
      },
      timeout: 8000,
    })
    if (res && typeof res === 'object' && 'code' in res && res.code === 0) return res.data ?? null
    return null
  } catch {
    return null
  }
}

export function getOverviewApi() {
  return getRaw<StatOverview>('/admin-api/knowledge/stat/overview')
}

export function getTrendApi(days = 7) {
  return getRaw<StatTrendItem[]>(`/admin-api/knowledge/stat/trend?days=${days}`)
}

export function getDocTypesApi() {
  return getRaw<StatDocType[]>('/admin-api/knowledge/stat/doc-types')
}

export function getHotApi(limit = 5) {
  return getRaw<StatHotItem[]>(`/admin-api/knowledge/stat/hot?limit=${limit}`)
}
