import request, { API_BASE } from './request'
import type { ChatMessage, Source } from '@/types'

/** 检索（无 LLM）：POST /admin-api/api/search */
export function searchApi(data: { query: string; kbId?: number; topK?: number; threshold?: number; mode?: string }) {
  return request.post<unknown, { results: Source[]; tookMs: number }>('/admin-api/api/search', data)
}

/** 完整问答（一次性）：POST /admin-api/api/chat */
export function chatApi(data: { sessionId: string; kbId?: number; message: string; mode?: string }) {
  return request.post<unknown, ChatMessage>('/admin-api/api/chat', data)
}

/** 会话列表（原型 s1/s2/s3，前端本地管理，若后端无此接口则返回空） */
export function listSessionsApi() {
  return request.get<unknown, Array<{ id: string; title: string; kbId: number; kbName: string; createdAt: number; updatedAt: number }>>(
    '/admin-api/knowledge/chat/session/page',
    { params: { page: 1, size: 100 } },
  ).catch(() => [])
}

/** 消息记录 */
export function listMessagesApi(sessionId: string) {
  return request
    .get<unknown, Array<{ id: string; role: string; content: string; sources?: Source[]; confidence?: number; rating?: string; createdAt: number }>>(
      '/admin-api/knowledge/chat/message/page',
      { params: { sessionId, page: 1, size: 200 } },
    )
    .catch(() => [])
}

/**
 * 流式问答（SSE，fetch 实现以携带 Authorization 头）：
 * GET /admin-api/api/chat/stream?sessionId=&kbId=&message=
 * 事件：meta → content×n → sources → done / error
 */
export async function chatStream(
  params: { sessionId: string; kbId?: number; message: string; mode?: string },
  handlers: {
    onMeta?: (data: { type: string; sessionId?: string; message?: string }) => void
    onContent: (delta: string) => void
    onSources: (sources: Source[], confidence?: number) => void
    onDone: (messageId?: string) => void
    onError: (message: string) => void
  },
  signal?: AbortSignal,
) {
  const token = localStorage.getItem('kf_access_token') || ''
  const qs = new URLSearchParams({
    sessionId: params.sessionId,
    message: params.message,
  })
  if (params.kbId) qs.set('kbId', String(params.kbId))
  if (params.mode) qs.set('mode', params.mode)

  const res = await fetch(`${API_BASE}/admin-api/api/chat/stream?${qs.toString()}`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
      'tenant-id': '1',
      Accept: 'text/event-stream',
    },
    signal,
  })

  if (!res.ok || !res.body) {
    let msg = `请求失败 (${res.status})`
    try {
      const body = await res.json()
      msg = body?.message || body?.detail || msg
    } catch {
      /* ignore */
    }
    handlers.onError(msg)
    return
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  // SSE 按空行分割事件块
  const dispatchBlock = (block: string) => {
    let event = 'message'
    let data = ''
    for (const line of block.split('\n')) {
      if (line.startsWith('event:')) event = line.slice(6).trim()
      else if (line.startsWith('data:')) data += line.slice(5).trim()
    }
    if (!data) return
    let parsed: Record<string, unknown>
    try {
      parsed = JSON.parse(data)
    } catch {
      parsed = { type: event, data }
    }
    const type = (parsed.type as string) || event
    switch (type) {
      case 'meta':
        handlers.onMeta?.(parsed as { type: string; sessionId?: string; message?: string })
        break
      case 'content':
        handlers.onContent(String(parsed.delta ?? parsed.content ?? ''))
        break
      case 'sources':
        handlers.onSources((parsed.sources as Source[]) || [], parsed.confidence as number | undefined)
        break
      case 'done':
        handlers.onDone(parsed.messageId as string | undefined)
        break
      case 'error':
        handlers.onError(String(parsed.message || 'AI 服务出错'))
        break
      default:
        break
    }
  }

  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    let idx: number
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const block = buffer.slice(0, idx)
      buffer = buffer.slice(idx + 2)
      if (block.trim()) dispatchBlock(block)
    }
  }
  // 尾部残留
  if (buffer.trim()) dispatchBlock(buffer)
}
