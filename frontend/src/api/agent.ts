import { requestRaw, getToken } from './request'

export interface AgentStartResponse {
  runId: string
  status: string
}

export interface AgentStep {
  stepName: string
  status: string
  durationMs: number
  inputSummary: string
  outputSummary: string
}

export interface AgentRun {
  runId: string
  status: string
  currentStep: string | null
  steps: AgentStep[]
  error: string | null
}

export interface AgentRequest {
  query: string
  kbId: number | string
  sessionId: string
}

export interface AgentEvent {
  type: string
  step?: AgentStep
  status?: string
  runId?: string
}

function buildHeaders() {
  return {
    'Content-Type': 'application/json',
    'tenant-id': '1',
    Authorization: `Bearer ${getToken()}`,
  }
}

/**
 * 启动 Agent 工作流
 */
export async function startAgentApi(req: AgentRequest): Promise<AgentStartResponse> {
  const res = await requestRaw({
    url: '/ai/agent',
    method: 'post',
    headers: buildHeaders(),
    data: req,
    timeout: 10000,
  })
  // AI 服务直接返回 {runId, status}，不需要解包 .data
  return res as AgentStartResponse
}

/**
 * 查询 Agent 工作流状态
 */
export async function getAgentStatusApi(runId: string): Promise<AgentRun> {
  const res = await requestRaw({
    url: `/ai/agent/status?runId=${encodeURIComponent(runId)}`,
    method: 'get',
    headers: buildHeaders(),
    timeout: 8000,
  })
  // AI 服务直接返回响应体，不需要解包 .data
  return res as AgentRun
}

/**
 * 人工确认 (approve / reject)
 */
export async function approveAgentApi(runId: string, decision: 'approve' | 'reject'): Promise<any> {
  const res = await requestRaw({
    url: `/ai/agent/approve?runId=${encodeURIComponent(runId)}&decision=${decision}`,
    method: 'post',
    headers: buildHeaders(),
    timeout: 10000,
  })
  // AI 服务直接返回响应体，不需要解包 .data
  return res
}

/**
 * 订阅 SSE 事件流
 */
export function subscribeAgentEvents(
  runId: string,
  onEvent: (event: AgentEvent) => void,
  onDone?: () => void,
): () => void {
  const url = `${import.meta.env.VITE_API_BASE || '/api'}/ai/agent/events?runId=${encodeURIComponent(runId)}`

  const eventSource = new EventSource(url)

  eventSource.addEventListener('step', (e: MessageEvent) => {
    onEvent(JSON.parse(e.data))
  })

  eventSource.addEventListener('status', (e: MessageEvent) => {
    onEvent(JSON.parse(e.data))
  })

  eventSource.addEventListener('done', (e: MessageEvent) => {
    const data = JSON.parse(e.data)
    // 传递 done 事件数据给 onEvent
    onEvent({ type: 'done', ...data })
    eventSource.close()
    onDone?.()
  })

  eventSource.onerror = () => {
    eventSource.close()
  }

  // 返回关闭函数
  return () => {
    eventSource.close()
  }
}
