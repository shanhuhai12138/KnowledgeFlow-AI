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
  report?: string
  summary?: string
  classification?: string
}

export interface AgentRequest {
  query: string
  kbId: number | string
  sessionId: string
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
  return res
}

/**
 * 轮询 Agent 状态
 * @returns 停止轮询的函数
 */
export function pollAgentStatus(
  runId: string,
  onStatus: (status: AgentRun) => void,
  onComplete?: () => void,
): () => void {
  const interval = window.setInterval(async () => {
    try {
      const status = await getAgentStatusApi(runId)
      onStatus(status)
      
      // 完成或错误时停止轮询
      if (['done', 'error', 'rejected'].includes(status.status)) {
        clearInterval(interval)
        onComplete?.()
      }
    } catch (e) {
      // 查询失败，继续轮询
      console.warn('Poll status failed:', e)
    }
  }, 2000)
  
  // 返回停止函数
  return () => clearInterval(interval)
}
