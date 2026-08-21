<template>
  <div class="agent-page">
    <!-- 头部 -->
    <header class="agent-header">
      <div class="header-left">
        <h1 class="serif title">Agent 工作流</h1>
        <p class="subtitle">基于 LangGraph 的智能文档分析，含人工确认节点</p>
      </div>
      <div class="header-right">
        <el-tag :type="statusTagType" class="status-tag">{{ statusText }}</el-tag>
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
            :disabled="!canStart || isRunning"
            @click="startAgent"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
            </svg>
            {{ isRunning ? '运行中...' : '启动 Agent 工作流' }}
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
              v-if="needsApproval || isApproved || isRejected"
              class="workflow-step human-step"
              :class="{ 
                'step-waiting': needsApproval, 
                'step-completed': isApproved,
                'step-skipped': isRejected 
              }"
            >
              <div class="step-indicator">
                <el-tag size="small" :type="needsApproval ? 'warning' : (isApproved ? 'success' : 'danger')" class="human-tag">
                  人工
                </el-tag>
              </div>
              <div class="step-info">
                <div class="step-name">人工确认</div>
                <div class="step-status">
                  {{ needsApproval ? '等待确认...' : (isApproved ? '已批准' : '已拒绝') }}
                </div>
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
            <el-tag v-else-if="isRejected" type="danger" size="small" class="ml-2">已拒绝</el-tag>
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
  pollAgentStatus,
  type AgentRun,
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
  startTime: number
  summary?: string
  classification?: string
  report?: string
  approved?: boolean
  error?: string
} | null>(null)
const workflowSteps = ref<Array<{ name: string; label: string; status: string; durationMs?: number; output?: string }>>([])
const finalReport = ref('')
const isApproved = ref(false)
const isRejected = ref(false)
const error = ref('')

// 人工确认相关
const needsApproval = computed(() => currentRun.value?.status === 'awaiting_approval')
const approvalDeadline = ref(0)
let approvalTimer: ReturnType<typeof setInterval> | null = null
let pollStop: (() => void) | null = null

const QUICK_QUESTIONS = [
  'Q3 销售目标达成情况如何？',
  '最新的产品需求规格是什么？',
  '公司账号密码重置流程',
  '远程办公最新规定',
]

// ---------- 计算属性 ----------
const canStart = computed(() => {
  return query.value.trim() && selectedKbId.value && !isRunning.value
})

const isRunning = computed(() => {
  return currentRun.value?.status === 'running' || currentRun.value?.status === 'awaiting_approval'
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
  return Math.round((remaining / 600000) * 100)
})

const approvalRemainingText = computed(() => {
  if (!approvalDeadline.value) return ''
  const remaining = Math.max(0, approvalDeadline.value - Date.now())
  const seconds = Math.ceil(remaining / 1000)
  if (seconds < 60) return `${seconds} 秒`
  return `${Math.floor(seconds / 60)} 分 ${seconds % 60} 秒`
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
  if (pollStop) {
    pollStop()
    pollStop = null
  }
  if (approvalTimer) {
    clearInterval(approvalTimer)
    approvalTimer = null
  }
  
  currentRun.value = null
  workflowSteps.value = []
  finalReport.value = ''
  isApproved.value = false
  isRejected.value = false
  approvalDeadline.value = 0
  error.value = ''
  
  // 清除 localStorage
  localStorage.removeItem('agent_last_run_id')
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

    const runId = res.runId
    currentRun.value = {
      runId,
      status: res.status,
      startTime: Date.now(),
      summary: '',
      classification: '',
      report: '',
    }

    // 持久化 runId
    localStorage.setItem('agent_last_run_id', runId)
    localStorage.setItem(`agent_run_${runId}`, JSON.stringify({
      startTime: Date.now(),
      query: query.value,
      kbId: selectedKbId.value,
    }))

    // 开始轮询
    pollStop = pollAgentStatus(runId, onStatusUpdate, onStatusComplete)

    // 初始化步骤
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

function onStatusUpdate(status: AgentRun) {
  if (!currentRun.value) return
  
  currentRun.value.status = status.status
  
  // 更新步骤
  if (status.steps && status.steps.length > 0) {
    workflowSteps.value = status.steps.map(s => ({
      name: s.stepName,
      label: getStepLabel(s.stepName),
      status: s.status,
      durationMs: s.durationMs,
      output: s.outputSummary,
    }))
  }
  
  // 更新报告数据
  if (status.summary) currentRun.value.summary = status.summary
  if (status.classification) currentRun.value.classification = status.classification
  if (status.report) {
    currentRun.value.report = status.report
    finalReport.value = status.report
  }
  
  // 检测到等待确认
  if (status.status === 'awaiting_approval') {
    approvalDeadline.value = Date.now() + 600000 // 10 分钟
    startApprovalTimer()
  }
}

function getStepLabel(stepName: string): string {
  const map: Record<string, string> = {
    retrieve: '检索文档',
    summarize: '生成摘要',
    classify: '主题分类',
    report_gate: '人工确认',
    report: '生成报告',
    not_found: '未找到相关内容',
  }
  return map[stepName] || stepName
}

function onStatusComplete() {
  if (!currentRun.value) return
  
  // 清除持久化
  localStorage.removeItem('agent_last_run_id')
  localStorage.removeItem(`agent_run_${currentRun.value.runId}`)
  
  // 完成或错误
  if (currentRun.value.status === 'done') {
    ElMessage.success('工作流完成')
  } else if (currentRun.value.status === 'rejected') {
    isRejected.value = true
    ElMessage.warning('工作流已拒绝')
  } else if (currentRun.value.status === 'error') {
    error.value = currentRun.value.error || '未知错误'
    ElMessage.error(error.value)
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
    
    if (decision === 'approve') {
      isApproved.value = true
      ElMessage.success('已批准，正在生成报告...')
    } else {
      isRejected.value = true
      ElMessage.info('已拒绝')
    }
    
    // 清除定时器
    if (approvalTimer) {
      clearInterval(approvalTimer)
      approvalTimer = null
    }
    
  } catch (e: any) {
    error.value = e?.message || '操作失败'
    ElMessage.error(error.value)
  }
}

function copyReport() {
  navigator.clipboard.writeText(finalReport.value)
  ElMessage.success('已复制到剪贴板')
}

function downloadReport() {
  const blob = new Blob([finalReport.value], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `report_${currentRun.value?.runId || 'unknown'}.md`
  a.click()
  URL.revokeObjectURL(url)
}

// ---------- 生命周期 ----------
onMounted(() => {
  loadKbs()
  
  // 检查是否有恢复的 runId
  const savedRunId = localStorage.getItem('agent_last_run_id')
  if (savedRunId) {
    const saved = localStorage.getItem(`agent_run_${savedRunId}`)
    if (saved) {
      const info = JSON.parse(saved)
      // 检查是否过期（10 分钟）
      if (Date.now() - info.startTime < 10 * 60 * 1000) {
        // 恢复显示
        currentRun.value = {
          runId: savedRunId,
          status: 'running',
          startTime: info.startTime,
        }
        
        // 继续轮询
        pollStop = pollAgentStatus(savedRunId, onStatusUpdate, onStatusComplete)
        
        // 初始化步骤
        workflowSteps.value = [
          { name: 'retrieve', label: '检索文档', status: 'waiting', output: '' },
          { name: 'summarize', label: '生成摘要', status: 'waiting', output: '' },
          { name: 'classify', label: '主题分类', status: 'waiting', output: '' },
          { name: 'report_gate', label: '人工确认', status: 'waiting', output: '' },
          { name: 'report', label: '生成报告', status: 'waiting', output: '' },
        ]
        
        ElMessage.info('已恢复之前的工作流')
      } else {
        // 已过期，清除
        localStorage.removeItem('agent_last_run_id')
        localStorage.removeItem(`agent_run_${savedRunId}`)
      }
    }
  }
})

onUnmounted(() => {
  if (pollStop) pollStop()
  if (approvalTimer) clearInterval(approvalTimer)
})
</script>

<style scoped>
.agent-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.agent-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.header-left .title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: var(--text-primary);
}

.header-left .subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.status-tag {
  font-size: 12px;
  padding: 4px 12px;
}

.agent-main {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 24px;
}

.agent-input-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-card {
  background: var(--bg-secondary);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid var(--border-color);
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 16px 0;
  color: var(--text-primary);
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
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.form-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  resize: vertical;
  min-height: 80px;
}

.form-textarea:focus {
  outline: none;
  border-color: var(--primary-color);
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.quick-btn {
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--bg-primary);
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-btn:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--primary-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-hover);
}

.btn-full {
  width: 100%;
  justify-content: center;
}

.btn-secondary {
  background: var(--bg-primary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
}

.btn-danger {
  background: #fef0f0;
  color: #f56c6c;
  border: 1px solid #fde2e2;
}

.btn-danger:hover {
  background: #fde2e2;
}

.btn-success {
  background: #f0f9ff;
  color: #409eff;
  border: 1px solid #d9ecff;
}

.btn-success:hover {
  background: #d9ecff;
}

.run-status {
  margin-top: 16px;
  padding: 12px;
  background: var(--bg-primary);
  border-radius: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.run-status code {
  font-family: monospace;
  color: var(--primary-color);
}

.agent-workflow-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
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
  background: var(--bg-primary);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  transition: all 0.2s;
}

.workflow-step.step-completed {
  border-color: #67c23a;
  background: #f0f9ff;
}

.workflow-step.step-running {
  border-color: var(--primary-color);
  background: #ecf5ff;
  animation: pulse 1.5s infinite;
}

.workflow-step.step-waiting {
  opacity: 0.6;
}

.workflow-step.step-skipped {
  opacity: 0.5;
}

.workflow-step.human-step {
  border-style: dashed;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.step-indicator {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--bg-secondary);
  border: 2px solid var(--border-color);
  flex-shrink: 0;
}

.step-num {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
}

.step-icon {
  font-size: 16px;
}

.step-icon.success {
  color: #67c23a;
}

.step-icon.running {
  color: var(--primary-color);
  animation: spin 1s linear infinite;
}

.step-icon.skipped,
.step-icon.error {
  color: #909399;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.step-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--border-color);
}

.step-info {
  flex: 1;
}

.step-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.step-status {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}

.step-duration {
  font-size: 11px;
  color: var(--text-tertiary);
}

.human-tag {
  font-size: 11px;
  padding: 2px 8px;
}

.step-detail {
  margin-top: 16px;
  padding: 16px;
  background: var(--bg-primary);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.step-detail h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: var(--text-primary);
}

.detail-content {
  font-size: 13px;
  color: var(--text-secondary);
  white-space: pre-wrap;
}

.approval-card {
  border-color: #e6a23c;
}

.approval-hint {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0 0 12px 0;
}

.approval-section {
  margin-bottom: 12px;
}

.section-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.approval-content {
  font-size: 13px;
  color: var(--text-primary);
  padding: 8px 12px;
  background: var(--bg-primary);
  border-radius: 6px;
  border: 1px solid var(--border-color);
}

.approval-timer {
  margin: 16px 0;
}

.timer-text {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
  display: block;
}

.approval-actions {
  display: flex;
  gap: 12px;
}

.approval-actions .btn {
  flex: 1;
}

.report-card {
  border-color: #67c23a;
}

.report-content {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.report-actions {
  display: flex;
  gap: 12px;
}

.report-actions .btn {
  flex: 1;
}

.error-card {
  border-color: #f56c6c;
}

.error-title {
  color: #f56c6c;
}

.error-message {
  color: var(--text-secondary);
  font-size: 14px;
  margin: 8px 0 16px;
}

.ml-2 {
  margin-left: 8px;
}

.mr-2 {
  margin-right: 8px;
}

@media (max-width: 768px) {
  .agent-main {
    grid-template-columns: 1fr;
  }
}
</style>
