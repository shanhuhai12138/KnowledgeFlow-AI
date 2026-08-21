<template>
  <div class="agent-page">
    <!-- 头部 -->
    <header class="agent-header">
      <div>
        <h1 class="serif page-title">Agent 工作流</h1>
        <p class="page-subtitle">基于 LangGraph 的智能文档分析，含人工确认节点</p>
      </div>
      <el-tag v-if="currentRun" :type="statusTagType" class="status-tag">{{ statusText }}</el-tag>
    </header>

    <!-- 主内容 -->
    <div class="agent-layout">
      <!-- 左侧：输入区 -->
      <aside class="agent-sidebar">
        <div class="card">
          <h3 class="card-title">分析问题</h3>
          
          <!-- 知识库选择 -->
          <div class="form-group">
            <label class="form-label">知识库</label>
            <el-select v-model="selectedKbId" placeholder="选择知识库" class="full-width" @change="onKbChange">
              <el-option v-for="kb in kbs" :key="kb.id" :label="kb.name" :value="kb.id" />
            </el-select>
          </div>

          <!-- 问题输入 -->
          <div class="form-group">
            <label class="form-label">分析问题</label>
            <textarea
              v-model="query"
              class="form-textarea"
              placeholder="请输入您要分析的问题，例如：Q3 销售目标达成情况如何？"
              rows="4"
            ></textarea>
          </div>

          <!-- 快捷问题 -->
          <div class="form-group">
            <label class="form-label">快捷问题</label>
            <div class="quick-questions">
              <button
                v-for="q in QUICK_QUESTIONS"
                :key="q"
                class="quick-btn"
                @click="query = q"
              >{{ q }}</button>
            </div>
          </div>

          <!-- 启动按钮 -->
          <button
            class="btn btn-primary btn-block"
            :disabled="!canStart || isRunning"
            @click="startAgent"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
            </svg>
            {{ isRunning ? '运行中...' : '启动 Agent 工作流' }}
          </button>

          <!-- 运行信息 -->
          <div v-if="currentRun" class="run-info">
            <div class="run-info-item">
              <span class="run-info-label">运行 ID</span>
              <code>{{ currentRun.runId }}</code>
            </div>
            <div class="run-info-item">
              <span class="run-info-label">开始时间</span>
              <span>{{ formatTime(currentRun.startTime) }}</span>
            </div>
          </div>
        </div>

        <!-- 人工确认区 -->
        <div v-if="needsApproval" class="card approval-card">
          <div class="card-title">
            <el-tag type="warning" size="small" class="mr-8">待确认</el-tag>
            人工确认
          </div>
          <p class="approval-hint">报告生成前需要您的确认</p>
          
          <!-- 摘要预览 -->
          <div class="approval-section">
            <div class="section-label">检索摘要</div>
            <div class="section-content">{{ currentRun?.summary || '暂无' }}</div>
          </div>

          <!-- 分类预览 -->
          <div class="approval-section">
            <div class="section-label">主题分类</div>
            <div class="section-content">{{ currentRun?.classification || '暂无' }}</div>
          </div>

          <!-- 倒计时 -->
          <div class="approval-timer">
            <el-progress
              :percentage="approvalProgress"
              :color="approvalProgress === 100 ? 'var(--error)' : 'var(--vermillion)'"
              :show-text="false"
            />
            <span class="timer-text">剩余时间: {{ approvalRemainingText }}</span>
          </div>

          <!-- 确认按钮 -->
          <div class="approval-actions">
            <button class="btn btn-danger" @click="handleApprove('reject')">拒绝</button>
            <button class="btn btn-success" @click="handleApprove('approve')">批准生成报告</button>
          </div>
        </div>
      </aside>

      <!-- 右侧：工作流展示 -->
      <main class="agent-main">
        <!-- 工作流步骤 -->
        <div class="card workflow-card">
          <h3 class="card-title">工作流状态</h3>
          
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
              <div v-if="step.durationMs" class="step-duration">{{ step.durationMs }}ms</div>
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
        <div v-if="finalReport" class="card report-card">
          <div class="card-title">
            分析报告
            <el-tag v-if="isApproved" type="success" size="small" class="ml-8">已批准</el-tag>
            <el-tag v-else-if="isRejected" type="danger" size="small" class="ml-8">已拒绝</el-tag>
          </div>
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
        <div v-if="error" class="card error-card">
          <h3 class="card-title error-title">运行错误</h3>
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
  } catch {
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
      { name: 'direct_answer', label: '直接回答', status: 'waiting', output: '' },
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
    direct_answer: '直接回答',
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
          { name: 'direct_answer', label: '直接回答', status: 'waiting', output: '' },
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
/* ========== 页面布局 ========== */
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
  border-bottom: 1px solid var(--line);
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: var(--ink);
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-muted);
  margin: 0;
}

.status-tag {
  font-size: 12px;
  padding: 4px 12px;
}

.agent-layout {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 24px;
  align-items: start;
}

/* ========== 卡片样式 ========== */
.card {
  background: var(--card);
  border-radius: var(--card-radius);
  padding: 20px;
  border: 1px solid var(--line);
  box-shadow: var(--shadow-card);
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 16px 0;
  color: var(--ink);
  display: flex;
  align-items: center;
  gap: 8px;
}

/* ========== 表单样式 ========== */
.form-group {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 6px;
}

.form-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: var(--input-radius);
  background: var(--paper);
  color: var(--ink);
  font-size: 14px;
  resize: vertical;
  min-height: 80px;
  transition: border-color 0.2s;
}

.form-textarea:focus {
  outline: none;
  border-color: var(--vermillion);
}

/* ========== 快捷问题 ========== */
.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.quick-btn {
  padding: 6px 12px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--paper-2);
  color: var(--text-muted);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.quick-btn:hover {
  border-color: var(--vermillion);
  color: var(--vermillion);
  background: var(--card);
}

/* ========== 按钮样式 ========== */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 20px;
  border: 1px solid transparent;
  border-radius: var(--btn-radius);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-block {
  width: 100%;
}

.btn-primary {
  background: var(--btn-solid);
  color: white;
  border-color: var(--btn-solid);
}

.btn-primary:hover:not(:disabled) {
  background: var(--btn-solid-2);
  border-color: var(--btn-solid-2);
}

.btn-secondary {
  background: var(--card);
  color: var(--ink);
  border-color: var(--line);
}

.btn-secondary:hover {
  border-color: var(--vermillion);
  color: var(--vermillion);
}

.btn-danger {
  background: var(--paper);
  color: var(--error);
  border-color: var(--line);
}

.btn-danger:hover {
  background: var(--error);
  color: white;
  border-color: var(--error);
}

.btn-success {
  background: var(--paper);
  color: var(--success);
  border-color: var(--line);
}

.btn-success:hover {
  background: var(--success);
  color: white;
  border-color: var(--success);
}

/* ========== 运行信息 ========== */
.run-info {
  margin-top: 16px;
  padding: 12px;
  background: var(--paper);
  border-radius: var(--input-radius);
  border: 1px solid var(--line);
}

.run-info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  margin-bottom: 4px;
}

.run-info-item:last-child {
  margin-bottom: 0;
}

.run-info-label {
  color: var(--text-muted);
}

.run-info code {
  font-family: 'Consolas', 'Monaco', monospace;
  color: var(--vermillion);
  font-size: 11px;
}

/* ========== 人工确认区 ========== */
.approval-card {
  margin-top: 16px;
  border-color: var(--warning);
}

.approval-hint {
  font-size: 13px;
  color: var(--text-muted);
  margin: 0 0 12px 0;
}

.approval-section {
  margin-bottom: 12px;
}

.section-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.section-content {
  font-size: 13px;
  color: var(--ink);
  padding: 8px 12px;
  background: var(--paper);
  border-radius: var(--input-radius);
  border: 1px solid var(--line);
}

.approval-timer {
  margin: 16px 0;
}

.timer-text {
  font-size: 12px;
  color: var(--text-muted);
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

/* ========== 工作流步骤 ========== */
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
  background: var(--paper);
  border-radius: var(--input-radius);
  border: 1px solid var(--line);
  transition: all 0.2s;
}

.workflow-step.step-completed {
  border-color: var(--success);
  background: rgba(31, 122, 77, 0.05);
}

.workflow-step.step-running {
  border-color: var(--vermillion);
  background: rgba(33, 49, 56, 0.05);
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
  background: var(--card);
  border: 2px solid var(--line);
  flex-shrink: 0;
}

.step-num {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-muted);
}

.step-icon {
  font-size: 16px;
}

.step-icon.success {
  color: var(--success);
}

.step-icon.running {
  color: var(--vermillion);
  animation: spin 1s linear infinite;
}

.step-icon.skipped,
.step-icon.error {
  color: var(--text-muted);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.step-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--line);
}

.step-info {
  flex: 1;
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
  font-size: 11px;
  color: var(--text-muted);
}

.human-tag {
  font-size: 11px;
  padding: 2px 8px;
}

/* ========== 步骤详情 ========== */
.step-detail {
  margin-top: 16px;
  padding: 16px;
  background: var(--paper);
  border-radius: var(--input-radius);
  border: 1px solid var(--line);
}

.step-detail h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: var(--ink);
}

.detail-content {
  font-size: 13px;
  color: var(--text-muted);
  white-space: pre-wrap;
}

/* ========== 报告卡片 ========== */
.report-card {
  border-color: var(--success);
}

.report-content {
  font-size: 14px;
  line-height: 1.6;
  color: var(--ink);
  margin-bottom: 16px;
  padding: 16px;
  background: var(--paper);
  border-radius: var(--input-radius);
  border: 1px solid var(--line);
}

.report-actions {
  display: flex;
  gap: 12px;
}

.report-actions .btn {
  flex: 1;
}

/* ========== 错误卡片 ========== */
.error-card {
  border-color: var(--error);
}

.error-title {
  color: var(--error);
}

.error-message {
  color: var(--text-muted);
  font-size: 14px;
  margin: 8px 0 16px;
}

/* ========== 工具类 ========== */
.mr-8 {
  margin-right: 8px;
}

.ml-8 {
  margin-left: 8px;
}

.full-width {
  width: 100%;
}

/* ========== 响应式 ========== */
@media (max-width: 768px) {
  .agent-layout {
    grid-template-columns: 1fr;
  }
  
  .agent-header {
    flex-direction: column;
    gap: 12px;
  }
}
</style>
