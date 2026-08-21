<template>
  <div class="agent-page">
    <!-- 头部 -->
    <header class="agent-header">
      <div class="header-left">
        <h1 class="serif title">Agent 工作流</h1>
        <p class="subtitle">基于 LangGraph 的智能文档分析，含人工确认节点</p>
      </div>
      <div class="header-right">
        <el-tag :type="statusTagType" class="status-tag">
          {{ statusText }}
        </el-tag>
      </div>
    </header>

    <!-- 主内容区 -->
    <div class="agent-main">
      <!-- 左侧：输入区 -->
      <aside class="agent-input-panel">
        <div class="panel-card">
          <h3 class="panel-title">分析问题</h3>
          
          <!-- 知识库选择 -->
          <div class="form-item">
            <label>知识库</label>
            <el-select v-model="selectedKbId" placeholder="选择知识库" class="full-width" @change="onKbChange">
              <el-option v-for="kb in kbs" :key="kb.id" :label="kb.name" :value="kb.id" />
            </el-select>
          </div>

          <!-- 问题输入 -->
          <div class="form-item">
            <label>分析问题</label>
            <textarea
              v-model="query"
              class="form-textarea"
              placeholder="请输入您要分析的问题，例如：Q3 销售目标达成情况如何？"
              rows="4"
            ></textarea>
          </div>

          <!-- 快捷问题 -->
          <div class="form-item">
            <label>快捷问题</label>
            <div class="quick-questions">
              <button
                v-for="q in QUICK_QUESTIONS"
                :key="q"
                class="quick-btn"
                @click="query = q"
              >
                {{ q }}
              </button>
            </div>
          </div>

          <!-- 启动按钮 -->
          <button
            class="btn btn-primary btn-full"
            :disabled="!canStart"
            @click="startAgent"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
            </svg>
            启动 Agent 工作流
          </button>

          <!-- 运行状态 -->
          <div v-if="currentRun" class="run-status">
            <div class="run-id">
              运行 ID: <code>{{ currentRun.runId }}</code>
            </div>
            <div class="run-time">
              开始时间: {{ formatTime(currentRun.startTime) }}
            </div>
          </div>
        </div>

        <!-- 人工确认区 -->
        <div v-if="needsApproval" class="panel-card approval-card">
          <h3 class="panel-title">
            <el-tag type="warning" size="small" class="mr-2">待确认</el-tag>
            人工确认
          </h3>
          <p class="approval-hint">报告生成前需要您的确认</p>
          
          <!-- 摘要预览 -->
          <div class="approval-section">
            <div class="section-label">检索摘要</div>
            <div class="approval-content">{{ currentRun?.summary || '暂无' }}</div>
          </div>

          <!-- 分类预览 -->
          <div class="approval-section">
            <div class="section-label">主题分类</div>
            <div class="approval-content">{{ currentRun?.classification || '暂无' }}</div>
          </div>

          <!-- 倒计时 -->
          <div class="approval-timer">
            <el-progress
              :percentage="approvalProgress"
              :color="approvalProgress === 100 ? '#f56c6c' : '#409eff'"
              :show-text="false"
            />
            <span class="timer-text">剩余时间: {{ approvalRemainingText }}</span>
          </div>

          <!-- 确认按钮 -->
          <div class="approval-actions">
            <button class="btn btn-danger" @click="handleApprove('reject')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
              拒绝
            </button>
            <button class="btn btn-success" @click="handleApprove('approve')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              批准生成报告
            </button>
          </div>
        </div>
      </aside>

      <!-- 右侧：工作流展示 -->
      <main class="agent-workflow-panel">
        <!-- 工作流图 -->
        <div class="panel-card workflow-card">
          <h3 class="panel-title">工作流状态</h3>
          
          <div class="workflow-steps">
            <div
              v-for="(step, index) in workflowSteps"
              :key="step.name"
              class="workflow-step"
              :class="{
                'step-completed': step.status === 'success',
                'step-running': step.status === 'running',
                'step-skipped': step.status === 'skipped',
                'step-error': step.status === 'error',
                'step-waiting': step.status === 'waiting',
              }"
            >
              <div class="step-indicator">
                <span class="step-num">{{ index + 1 }}</span>
                <el-icon v-if="step.status === 'success'" class="step-icon success"><Check /></el-icon>
                <el-icon v-else-if="step.status === 'running'" class="step-icon running"><Loading /></el-icon>
                <el-icon v-else-if="step.status === 'skipped'" class="step-icon skipped"><Close /></el-icon>
                <el-icon v-else-if="step.status === 'error'" class="step-icon error"><Warning /></el-icon>
                <span v-else class="step-dot"></span>
              </div>
              <div class="step-info">
                <div class="step-name">{{ step.label }}</div>
                <div class="step-status">{{ stepStatusText(step.status) }}</div>
              </div>
              <div v-if="step.durationMs" class="step-duration">
                {{ step.durationMs }}ms
              </div>
            </div>

            <!-- 人工确认节点 -->
            <div
              v-if="hasHumanApproval"
              class="workflow-step human-step"
              :class="{ 'step-waiting': isAwaitingApproval, 'step-completed': isApproved }"
            >
              <div class="step-indicator">
                <el-tag size="small" :type="isAwaitingApproval ? 'warning' : 'success'" class="human-tag">
                  人工
                </el-tag>
              </div>
              <div class="step-info">
                <div class="step-name">人工确认</div>
                <div class="step-status">{{ isAwaitingApproval ? '等待确认...' : (isApproved ? '已批准' : '已拒绝') }}</div>
              </div>
            </div>
          </div>

          <!-- 当前步骤详情 -->
          <div v-if="currentStepDetail" class="step-detail">
            <h4>{{ currentStepDetail.label }} - 详情</h4>
            <div class="detail-content">{{ currentStepDetail.output }}</div>
          </div>
        </div>

        <!-- 报告展示 -->
        <div v-if="finalReport" class="panel-card report-card">
          <h3 class="panel-title">
            分析报告
            <el-tag v-if="isApproved" type="success" size="small" class="ml-2">已批准</el-tag>
            <el-tag v-else type="danger" size="small" class="ml-2">已拒绝</el-tag>
          </h3>
          <div class="report-content" v-html="renderMarkdown(finalReport)"></div>
          
          <!-- 报告操作 -->
          <div class="report-actions">
            <button class="btn btn-secondary" @click="copyReport">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
              </svg>
              复制报告
            </button>
            <button class="btn btn-primary" @click="downloadReport">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              下载报告
            </button>
          </div>
        </div>

        <!-- 错误提示 -->
        <div v-if="error" class="panel-card error-card">
          <h3 class="panel-title error-title">运行错误</h3>
          <p class="error-message">{{ error }}</p>
          <button class="btn btn-secondary" @click="error = ''">关闭</button>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Check, Loading, Close, Warning } from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import {
  startAgentApi,
  approveAgentApi,
  subscribeAgentEvents,
  type AgentStep,
} from '@/api/agent'
import { getKbPageApi } from '@/api/kb'
import type { KnowledgeBase } from '@/types'

// ---------- Markdown ----------
const md = new MarkdownIt({ html: false, linkify: true, breaks: true })
function renderMarkdown(content: string) {
  return md.render(content)
}

// ---------- 状态 ----------
const kbs = ref<KnowledgeBase[]>([])
const selectedKbId = ref<number | undefined>()
const query = ref('')
const currentRun = ref<{
  runId: string
  status: string
  currentStep: string | null
  steps: Array<{ stepName: string; status: string; durationMs: number; inputSummary: string; outputSummary: string }>
  error: string | null
  startTime: number
  summary?: string
  classification?: string
  report?: string
  approved?: boolean
  pollInterval?: number
} | null>(null)
const workflowSteps = ref<Array<{ name: string; label: string; status: string; durationMs?: number; output?: string }>>([])
const finalReport = ref('')
const isApproved = ref(false)
const error = ref('')

// 人工确认相关
const isAwaitingApproval = ref(false)
const approvalDeadline = ref(0)
let approvalTimer: ReturnType<typeof setInterval> | null = null
let eventSourceClose: (() => void) | null = null

const QUICK_QUESTIONS = [
  'Q3 销售目标达成情况如何？',
  '最新的产品需求规格是什么？',
  '公司账号密码重置流程',
  '远程办公最新规定',
]

// ---------- 计算属性 ----------
const canStart = computed(() => {
  return query.value.trim() && selectedKbId.value
})

const needsApproval = computed(() => {
  return isAwaitingApproval.value && !currentRun.value?.approved
})

const statusTagType = computed(() => {
  if (!currentRun.value) return 'info'
  const status = currentRun.value.status
  if (status === 'done') return 'success'
  if (status === 'awaiting_approval') return 'warning'
  if (status === 'rejected') return 'danger'
  if (status === 'error') return 'danger'
  return 'info'
})

const statusText = computed(() => {
  if (!currentRun.value) return '等待启动'
  const status = currentRun.value.status
  const map: Record<string, string> = {
    running: '运行中',
    awaiting_approval: '等待人工确认',
    done: '完成',
    rejected: '已拒绝',
    error: '错误',
  }
  return map[status] || status
})

const approvalProgress = computed(() => {
  if (!approvalDeadline.value) return 0
  const remaining = Math.max(0, approvalDeadline.value - Date.now())
  return Math.round((remaining / 600000) * 100) // 10分钟 = 600000ms
})

const approvalRemainingText = computed(() => {
  if (!approvalDeadline.value) return ''
  const remaining = Math.max(0, approvalDeadline.value - Date.now())
  const seconds = Math.ceil(remaining / 1000)
  if (seconds < 60) return `${seconds} 秒`
  return `${Math.floor(seconds / 60)} 分 ${seconds % 60} 秒`
})

const hasHumanApproval = computed(() => {
  return workflowSteps.value.some(s => s.name === 'report_gate') || isAwaitingApproval.value
})

const currentStepDetail = computed(() => {
  const runningStep = workflowSteps.value.find(s => s.status === 'running')
  if (!runningStep) return null
  return {
    label: runningStep.label,
    output: runningStep.output || '',
  }
})

// ---------- 方法 ----------
function stepStatusText(status: string): string {
  const map: Record<string, string> = {
    running: '运行中',
    success: '完成',
    skipped: '已跳过',
    error: '错误',
    waiting: '等待中',
  }
  return map[status] || status
}

function formatTime(timestamp: number): string {
  return new Date(timestamp).toLocaleTimeString('zh-CN')
}

async function loadKbs() {
  try {
    const data = await getKbPageApi({ pageNo: 1, pageSize: 100 })
    kbs.value = data?.list || []
    if (kbs.value.length && !selectedKbId.value) {
      selectedKbId.value = kbs.value[0].id
    }
  } catch (e) {
    kbs.value = []
  }
}

function onKbChange() {
  resetRun()
}

function resetRun() {
  currentRun.value = null
  workflowSteps.value = []
  finalReport.value = ''
  isApproved.value = false
  isAwaitingApproval.value = false
  approvalDeadline.value = 0
  error.value = ''
  if (approvalTimer) {
    clearInterval(approvalTimer)
    approvalTimer = null
  }
  if (eventSourceClose) {
    eventSourceClose()
    eventSourceClose = null
  }
}

async function startAgent() {
  if (!canStart.value) return

  resetRun()

  try {
    const res = await startAgentApi({
      query: query.value,
      kbId: selectedKbId.value!,
      sessionId: `agent_${Date.now()}`,
    })

    currentRun.value = {
      ...res,
      startTime: Date.now(),
      currentStep: null,
      steps: [],
      error: null,
      summary: '',
      classification: '',
      report: '',
      approved: false,
    } as any

    // 只使用 SSE 事件流，不轮询
    eventSourceClose = subscribeAgentEvents(
      res.runId,
      (event) => handleAgentEvent(event),
      () => handleAgentDone(),
    )

    // 初始化空步骤，显示工作流框架
    workflowSteps.value = [
      { name: 'retrieve', label: '检索文档', status: 'waiting', output: '' },
      { name: 'summarize', label: '生成摘要', status: 'waiting', output: '' },
      { name: 'classify', label: '主题分类', status: 'waiting', output: '' },
      { name: 'report_gate', label: '人工确认', status: 'waiting', output: '' },
      { name: 'report', label: '生成报告', status: 'waiting', output: '' },
    ]

  } catch (e: any) {
    error.value = e?.message || '启动失败'
    ElMessage.error(error.value)
  }
}

function updateWorkflowSteps(steps: AgentStep[]) {
  const stepMap: Record<string, { label: string; output?: string }> = {
    retrieve: { label: '检索文档', output: '' },
    summarize: { label: '生成摘要', output: '' },
    classify: { label: '主题分类', output: '' },
    report_gate: { label: '人工确认', output: '' },
    report: { label: '生成报告', output: '' },
    not_found: { label: '未找到相关内容', output: '' },
  }

  workflowSteps.value = steps.map(s => ({
    name: s.stepName,
    label: stepMap[s.stepName]?.label || s.stepName,
    status: s.status,
    durationMs: s.durationMs,
    output: s.outputSummary,
  }))

  const summaryStep = steps.find(s => s.stepName === 'summarize')
  const classifyStep = steps.find(s => s.stepName === 'classify')
  if (summaryStep && currentRun.value) currentRun.value.summary = summaryStep.outputSummary
  if (classifyStep && currentRun.value) currentRun.value.classification = classifyStep.outputSummary
}

function handleAgentEvent(event: any) {
  if (event.type === 'step') {
    updateWorkflowSteps([event.step])
  } else if (event.type === 'status') {
    if (currentRun.value) {
      currentRun.value.status = event.status
      // 等待人工确认
      if (event.status === 'awaiting_approval') {
        isAwaitingApproval.value = true
        approvalDeadline.value = Date.now() + 600000
        startApprovalTimer()
      }
    }
  } else if (event.type === 'done') {
    // done 事件可能包含报告
    if (event.report && currentRun.value) {
      currentRun.value.report = event.report
    }
    // done 时确保步骤已更新（如果后端在 done 事件中包含 steps）
    if (event.steps && event.steps.length > 0) {
      updateWorkflowSteps(event.steps)
    }
  }
}

function handleAgentDone() {
  // 从 currentRun 获取报告
  if (currentRun.value?.status === 'done' && currentRun.value.report) {
    finalReport.value = currentRun.value.report
  }
}

function startApprovalTimer() {
  if (approvalTimer) clearInterval(approvalTimer)
  approvalTimer = setInterval(() => {
    if (Date.now() >= approvalDeadline.value) {
      clearInterval(approvalTimer!)
      approvalTimer = null
      ElMessage.warning('人工确认超时，工作流已取消')
      resetRun()
    }
  }, 1000)
}

async function handleApprove(decision: 'approve' | 'reject') {
  if (!currentRun.value) return
  
  try {
    await approveAgentApi(currentRun.value.runId, decision)
    isApproved.value = decision === 'approve'
    isAwaitingApproval.value = false
    
    if (approvalTimer) {
      clearInterval(approvalTimer)
      approvalTimer = null
    }
    
    if (decision === 'approve') {
      ElMessage.success('已批准，正在生成报告...')
    } else {
      ElMessage.info('已拒绝，报告生成已取消')
      currentRun.value.status = 'rejected'
    }
  } catch (e: any) {
    error.value = e?.message || '确认失败'
    ElMessage.error(error.value)
  }
}

function copyReport() {
  navigator.clipboard.writeText(finalReport.value)
  ElMessage.success('已复制到剪贴板')
}

function downloadReport() {
  const blob = new Blob([finalReport.value], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `agent-report-${Date.now()}.md`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('报告已下载')
}

// ---------- 生命周期 ----------
onMounted(async () => {
  await loadKbs()
})

onUnmounted(() => {
  if (approvalTimer) clearInterval(approvalTimer)
  if (eventSourceClose) eventSourceClose()
})
</script>

<style scoped>
.agent-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--topbar-h));
  overflow: hidden;
}

/* 头部 */
.agent-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px;
  border-bottom: 1px solid var(--line);
  background: var(--card);
  flex-shrink: 0;
}

.header-left .title {
  font-size: 28px;
  margin: 0 0 4px 0;
  color: var(--ink);
}

.header-left .subtitle {
  font-size: 14px;
  color: var(--text-muted);
  margin: 0;
}

.status-tag {
  font-size: 13px;
  padding: 6px 12px;
}

/* 主内容区 */
.agent-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* 左侧输入面板 */
.agent-input-panel {
  width: 360px;
  flex-shrink: 0;
  overflow-y: auto;
  padding: 24px;
  border-right: 1px solid var(--line);
  background: var(--paper);
}

.panel-card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--ink);
  margin: 0 0 16px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-item {
  margin-bottom: 16px;
}

.form-item label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
  margin-bottom: 6px;
}

.form-textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--paper-2);
  color: var(--ink);
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
  font-family: inherit;
}

.form-textarea:focus {
  outline: none;
  border-color: var(--vermillion);
}

.quick-questions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-btn {
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--paper-2);
  color: var(--text);
  font-size: 13px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-btn:hover {
  border-color: var(--vermillion);
  background: var(--card);
  color: var(--vermillion);
}

.btn-full {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 24px;
}

.run-status {
  margin-top: 16px;
  padding: 12px;
  background: var(--paper-2);
  border-radius: 8px;
  font-size: 12px;
  color: var(--text-muted);
}

.run-status code {
  background: var(--line);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'SFMono-Regular', Consolas, monospace;
}

/* 人工确认卡片 */
.approval-card {
  border-color: var(--warning);
  background: linear-gradient(135deg, var(--card) 0%, rgba(237, 137, 54, 0.05) 100%);
}

.approval-hint {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0 0 16px 0;
}

.approval-section {
  margin-bottom: 16px;
}

.section-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 6px;
}

.approval-content {
  padding: 12px;
  background: var(--paper-2);
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text);
  max-height: 120px;
  overflow-y: auto;
}

.approval-timer {
  margin: 16px 0;
}

.timer-text {
  display: block;
  text-align: center;
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 8px;
}

.approval-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.approval-actions .btn {
  flex: 1;
}

/* 右侧工作流面板 */
.agent-workflow-panel {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: var(--paper);
}

.workflow-card {
  margin-bottom: 16px;
}

.workflow-steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.workflow-step {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--paper-2);
  border: 1px solid var(--line);
  border-radius: 8px;
  transition: all 0.2s;
}

.workflow-step.step-completed {
  border-color: var(--success);
  background: rgba(31, 122, 77, 0.05);
}

.workflow-step.step-running {
  border-color: var(--primary);
  background: rgba(33, 49, 56, 0.05);
  animation: pulse 1.5s infinite;
}

.workflow-step.step-skipped {
  opacity: 0.6;
}

.workflow-step.step-error {
  border-color: var(--error);
  background: rgba(229, 62, 62, 0.05);
}

.workflow-step.human-step {
  border-color: var(--warning);
  background: rgba(237, 137, 54, 0.05);
}

.step-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--line);
  flex-shrink: 0;
}

.step-num {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted);
}

.step-icon {
  width: 16px;
  height: 16px;
}

.step-icon.success { color: var(--success); }
.step-icon.running { color: var(--primary); animation: spin 1s linear infinite; }
.step-icon.skipped { color: var(--text-muted); }
.step-icon.error { color: var(--error); }

.step-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
}

.step-info {
  flex: 1;
  min-width: 0;
}

.step-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--ink);
}

.step-status {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}

.step-duration {
  font-size: 12px;
  color: var(--text-muted);
  font-family: 'SFMono-Regular', Consolas, monospace;
}

.human-tag {
  font-size: 11px;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(33, 49, 56, 0.1); }
  50% { box-shadow: 0 0 0 8px rgba(33, 49, 56, 0.05); }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.step-detail {
  margin-top: 16px;
  padding: 16px;
  background: var(--paper-2);
  border-radius: 8px;
  border: 1px solid var(--line);
}

.step-detail h4 {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: var(--ink);
}

.step-detail .detail-content {
  font-size: 13px;
  color: var(--text);
  line-height: 1.6;
  max-height: 200px;
  overflow-y: auto;
}

/* 报告卡片 */
.report-card {
  margin-bottom: 16px;
}

.report-content {
  padding: 20px;
  background: var(--paper-2);
  border-radius: 8px;
  border: 1px solid var(--line);
  font-size: 14px;
  line-height: 1.8;
  color: var(--ink);
}

.report-content :deep(h1),
.report-content :deep(h2),
.report-content :deep(h3) {
  margin-top: 24px;
  margin-bottom: 12px;
  color: var(--ink);
}

.report-content :deep(p) {
  margin-bottom: 12px;
}

.report-content :deep(ul),
.report-content :deep(ol) {
  padding-left: 24px;
  margin-bottom: 12px;
}

.report-content :deep(li) {
  margin-bottom: 4px;
}

.report-content :deep(code) {
  background: var(--line);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.report-content :deep(pre) {
  background: var(--ink);
  color: var(--card);
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 16px 0;
}

.report-content :deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
}

.report-content :deep(blockquote) {
  border-left: 3px solid var(--vermillion);
  padding-left: 16px;
  color: var(--text-muted);
  margin: 16px 0;
}

.report-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
}

.report-content :deep(th),
.report-content :deep(td) {
  border: 1px solid var(--line);
  padding: 8px 12px;
  text-align: left;
}

.report-content :deep(th) {
  background: var(--line);
  font-weight: 600;
}

.report-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

/* 错误卡片 */
.error-card {
  border-color: var(--error);
  background: rgba(229, 62, 62, 0.05);
}

.error-title {
  color: var(--error);
}

.error-message {
  color: var(--error);
  font-size: 14px;
  margin: 12px 0;
  line-height: 1.6;
}

/* 工具类 */
.mr-2 { margin-right: 8px; }
.ml-2 { margin-left: 8px; }

/* 响应式 */
@media (max-width: 1024px) {
  .agent-main {
    flex-direction: column;
  }
  
  .agent-input-panel {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--line);
  }
}
</style>
