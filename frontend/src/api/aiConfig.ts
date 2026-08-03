import { requestRaw, getToken } from './request'

/**
 * AI 配置（FR-11 / DR-13）：key 永不明文回显
 * GET /admin-api/knowledge/ai-config → { hasKey, maskedKey, baseUrl, model }
 * PUT /admin-api/knowledge/ai-config（apiKey 空串 = 清除）
 * 权限：super_admin（普通用户 403）——403 静默返回 forbidden，页面隐藏/提示，不弹全局错
 */

export interface AiConfig {
  hasKey: boolean
  maskedKey: string
  baseUrl: string
  model: string
}

export interface AiConfigResult {
  ok: boolean
  forbidden: boolean
  data: AiConfig | null
}

interface RawRes<T> {
  code: number
  data: T
  message?: string
  msg?: string
}

function isForbidden(err: unknown): boolean {
  const e = err as { response?: { status?: number } }
  return e?.response?.status === 403
}

export async function getAiConfig(): Promise<AiConfigResult> {
  try {
    const res = await requestRaw<RawRes<AiConfig>>({
      url: '/admin-api/knowledge/ai-config',
      method: 'get',
      headers: { 'tenant-id': '1', Authorization: `Bearer ${getToken()}` },
      timeout: 8000,
    })
    if (res && typeof res === 'object' && 'code' in res && res.code === 0) {
      return { ok: true, forbidden: false, data: res.data ?? null }
    }
    return { ok: false, forbidden: false, data: null }
  } catch (err) {
    if (isForbidden(err)) return { ok: false, forbidden: true, data: null }
    return { ok: false, forbidden: false, data: null }
  }
}

export async function saveAiConfig(body: {
  apiKey?: string
  baseUrl?: string
  model?: string
}): Promise<{ ok: boolean; forbidden: boolean; message: string }> {
  try {
    const res = await requestRaw<RawRes<boolean>>({
      url: '/admin-api/knowledge/ai-config',
      method: 'put',
      data: { configKey: 'llm', ...body },
      headers: { 'tenant-id': '1', Authorization: `Bearer ${getToken()}` },
      timeout: 8000,
    })
    if (res && typeof res === 'object' && 'code' in res && res.code === 0) {
      return { ok: true, forbidden: false, message: '' }
    }
    return { ok: false, forbidden: false, message: (res as RawRes<boolean>)?.message || (res as RawRes<boolean>)?.msg || '保存失败' }
  } catch (err) {
    if (isForbidden(err)) return { ok: false, forbidden: true, message: '无权限' }
    const e = err as { response?: { data?: { message?: string; msg?: string } } }
    const msg = e?.response?.data?.message || e?.response?.data?.msg || '网络异常'
    return { ok: false, forbidden: false, message: msg }
  }
}
