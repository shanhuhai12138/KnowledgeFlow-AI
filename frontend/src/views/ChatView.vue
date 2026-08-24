<script setup lang="ts">
// 聊天页（核心）：会话列表 + SSE 流式打字机 + 来源卡片 + 置信度 + 点赞点踩复制 + 快捷提问
import { nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import MarkdownIt from 'markdown-it'
// highlight.js 按需引入（避免全量 1MB chunk，目标 < 500KB）
import hljs from 'highlight.js/lib/core'
import javascript from 'highlight.js/lib/languages/javascript'
import typescript from 'highlight.js/lib/languages/typescript'
import python from 'highlight.js/lib/languages/python'
import java from 'highlight.js/lib/languages/java'
import cpp from 'highlight.js/lib/languages/cpp'
import csharp from 'highlight.js/lib/languages/csharp'
import go from 'highlight.js/lib/languages/go'
import rust from 'highlight.js/lib/languages/rust'
import kotlin from 'highlight.js/lib/languages/kotlin'
import bash from 'highlight.js/lib/languages/bash'
import shell from 'highlight.js/lib/languages/shell'
import json from 'highlight.js/lib/languages/json'
import xml from 'highlight.js/lib/languages/xml'
import markdown from 'highlight.js/lib/languages/markdown'
import yaml from 'highlight.js/lib/languages/yaml'
import sql from 'highlight.js/lib/languages/sql'
import css from 'highlight.js/lib/languages/css'
import php from 'highlight.js/lib/languages/php'
import ruby from 'highlight.js/lib/languages/ruby'
import dockerfile from 'highlight.js/lib/languages/dockerfile'

hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('python', python)
hljs.registerLanguage('java', java)
hljs.registerLanguage('cpp', cpp)
hljs.registerLanguage('csharp', csharp)
hljs.registerLanguage('go', go)
hljs.registerLanguage('rust', rust)
hljs.registerLanguage('kotlin', kotlin)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('shell', shell)
hljs.registerLanguage('json', json)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('markdown', markdown)
hljs.registerLanguage('yaml', yaml)
hljs.registerLanguage('sql', sql)
hljs.registerLanguage('css', css)
hljs.registerLanguage('php', php)
hljs.registerLanguage('ruby', ruby)
hljs.registerLanguage('dockerfile', dockerfile)
import { chatStream } from '@/api/chat'
import { getKbPageApi } from '@/api/kb'
import { uploadDocumentApi } from '@/api/document'
import { API_BASE } from '@/api/request'
import type { ChatMessage, ChatSession, KnowledgeBase } from '@/types'
import { useRouter } from 'vue-router'
import SearchModeSelector from '@/components/SearchModeSelector.vue'
import type { SearchMode } from '@/utils/queryClassifier'

const route = useRoute()

// ---------- markdown ----------
const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  highlight(str: string, lang: string): string {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs"><code>${hljs.highlight(str, { language: lang }).value}</code></pre>`
      } catch {
        /* fallthrough */
      }
    }
    return `<pre class="hljs"><code>${MarkdownIt().utils.escapeHtml(str)}</code></pre>`
  },
})

// ---------- 状态 ----------
const kbs = ref<KnowledgeBase[]>([])
const currentKbId = ref<number | undefined>()
const currentKbName = ref('')

const sessions = ref<ChatSession[]>([])
const currentSessionId = ref('')
const messages = ref<ChatMessage[]>([])
const inputText = ref('')
const isStreaming = ref(false)
const streamingMsgId = ref('')

const QUICK_QUESTIONS = [
  '如何重置公司账号密码？',
  '最新的产品需求规格是什么？',
  'Q3 销售目标达成情况如何？',
  '关于远程办公的最新规定',
]

// ---------- 本地持久化（会话/消息，后端无会话接口时兜底） ----------
const LS_SESSIONS = 'kf_sessions'
const lsMessagesKey = (sid: string) => `kf_messages_${sid}`

function loadSessions(): ChatSession[] {
  try {
    return JSON.parse(localStorage.getItem(LS_SESSIONS) || '[]')
  } catch {
    return []
  }
}
function saveSessions() {
  localStorage.setItem(LS_SESSIONS, JSON.stringify(sessions.value))
}
function loadMessages(sid: string): ChatMessage[] {
  try {
    return JSON.parse(localStorage.getItem(lsMessagesKey(sid)) || '[]')
  } catch {
    return []
  }
}
function saveMessages() {
  localStorage.setItem(lsMessagesKey(currentSessionId.value), JSON.stringify(messages.value))
}

// ---------- 会话 ----------
function nowTs() {
  return Date.now()
}

function newSession() {
  const s: ChatSession = {
    id: `s${nowTs()}`,
    title: `新对话 ${dayjs().format('HH:mm')}`,
    kbId: currentKbId.value,
    kbName: currentKbName.value || '未选择知识库',
    createdAt: nowTs(),
    updatedAt: nowTs(),
  }
  sessions.value.unshift(s)
  saveSessions()
  switchSession(s.id)
}

function switchSession(id: string) {
  currentSessionId.value = id
  messages.value = loadMessages(id)
  const s = sessions.value.find((x) => x.id === id)
  if (s) {
    currentKbId.value = s.kbId
    currentKbName.value = s.kbName
  }
}

async function removeSession(id: string) {
  try {
    await ElMessageBox.confirm('删除后该会话的消息记录将一并清除，确定删除？', '删除会话', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  const idx = sessions.value.findIndex((x) => x.id === id)
  if (idx === -1) return
  sessions.value.splice(idx, 1)
  localStorage.removeItem(lsMessagesKey(id))
  saveSessions()
  if (currentSessionId.value === id) {
    if (sessions.value.length) switchSession(sessions.value[0].id)
    else newSession()
  }
}

// ---------- 知识库 ----------
async function loadKbs() {
  try {
    const data = await getKbPageApi({ pageNo: 1, pageSize: 100 })
    kbs.value = data?.list || []
    if (kbs.value.length) {
      if (!currentKbId.value) {
        currentKbId.value = kbs.value[0].id
        currentKbName.value = kbs.value[0].name
      }
      // 同步当前会话 kb 名
      const s = sessions.value.find((x) => x.id === currentSessionId.value)
      if (s) {
        s.kbId = currentKbId.value
        s.kbName = currentKbName.value
        saveSessions()
      }
    }
  } catch {
    kbs.value = []
  }
}

function onKbChange(id: number) {
  currentKbId.value = id
  const kb = kbs.value.find((x) => x.id === id)
  currentKbName.value = kb?.name || ''
  const s = sessions.value.find((x) => x.id === currentSessionId.value)
  if (s) {
    s.kbId = id
    s.kbName = currentKbName.value
    saveSessions()
  }
}

// ---------- 发送与流式 ----------
const messagesAreaRef = ref<HTMLElement | null>(null)
const searchMode = ref<SearchMode>('auto')

function scrollToBottom() {
  nextTick(() => {
    const el = messagesAreaRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

function sendMessage(text?: string) {
  const content = (text ?? inputText.value).trim()
  if (!content || isStreaming.value) return
  inputText.value = ''

  // 保证有会话
  if (!sessions.value.find((x) => x.id === currentSessionId.value)) newSession()

  const userMsg: ChatMessage = {
    id: `u${nowTs()}`,
    role: 'user',
    content,
    createdAt: nowTs(),
  }
  messages.value.push(userMsg)
  saveMessages()
  scrollToBottom()

  // 占位 assistant 消息
  const aid = `a${nowTs()}`
  const aiMsg: ChatMessage = {
    id: aid,
    role: 'assistant',
    content: '',
    sources: [],
    confidence: undefined,
    rating: null,
    createdAt: nowTs(),
  }
  messages.value.push(aiMsg)
  streamingMsgId.value = aid
  isStreaming.value = true
  saveMessages()
  scrollToBottom()

  chatStream(
    { sessionId: currentSessionId.value, kbId: currentKbId.value, message: content, mode: searchMode.value },
    {
      onMeta: () => {},
      onContent: (delta) => {
        const m = messages.value.find((x) => x.id === aid)
        if (m) {
          m.content += delta
          saveMessages()
          scrollToBottom()
        }
      },
      onSources: (sources, confidence) => {
        const m = messages.value.find((x) => x.id === aid)
        if (m) {
          m.sources = sources
          m.confidence = confidence
          saveMessages()
          scrollToBottom()
        }
      },
      onDone: () => {
        const m = messages.value.find((x) => x.id === aid)
        if (m && !m.content) m.content = '（AI 未返回内容，请重试）'
        isStreaming.value = false
        streamingMsgId.value = ''
        // 会话标题：取首个问题前 18 字
        const s = sessions.value.find((x) => x.id === currentSessionId.value)
        if (s && (s.title.startsWith('新对话') || !s.title)) {
          s.title = content.slice(0, 18) || s.title
          s.updatedAt = nowTs()
          saveSessions()
        }
        saveMessages()
      },
      onError: (msg) => {
        const m = messages.value.find((x) => x.id === aid)
        if (m) m.content = `⚠️ 出错了：${msg}`
        isStreaming.value = false
        streamingMsgId.value = ''
        saveMessages()
        ElMessage.error(msg)
      },
    },
  ).catch((e) => {
    const m = messages.value.find((x) => x.id === aid)
    if (m) m.content = `⚠️ 出错了：${(e as Error).message || '网络异常'}`
    isStreaming.value = false
    streamingMsgId.value = ''
    saveMessages()
  })
}

function onInputKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

// ---------- 消息操作 ----------
function rateMsg(msg: ChatMessage, rating: 'up' | 'down') {
  if (!msg.rating) {
    msg.rating = rating
    saveMessages()
  }
  ElMessage.success(rating === 'up' ? '已点赞' : '已点踩')
}

async function copyMsg(msg: ChatMessage) {
  try {
    await navigator.clipboard.writeText(msg.content)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.warning('复制失败，请手动选择')
  }
}

function renderMarkdown(content: string) {
  return md.render(content)
}

// ---------- 初始化 ----------
onMounted(async () => {
  // 从侧边栏/路由带入 kb
  const qKbId = route.query.kbId ? Number(route.query.kbId) : undefined
  const qKbName = (route.query.kbName as string) || ''

  sessions.value = loadSessions()
  await loadKbs()

  if (qKbId) {
    currentKbId.value = qKbId
    currentKbName.value = qKbName
  }
  if (sessions.value.length) {
    switchSession(sessions.value[0].id)
  } else {
    newSession()
  }
})

watch(
  () => route.query.kbId,
  (v) => {
    if (v) {
      currentKbId.value = Number(v)
      const kb = kbs.value.find((x) => x.id === Number(v))
      currentKbName.value = kb?.name || String(route.query.kbName || '')
    }
  },
)

// ---------- 时间格式化 ----------
function fmtTime(t: number | string) {
  return dayjs(t).format('HH:mm')
}

// ---------- 文档跳转与预览 ----------
function jumpToDocument(source: { documentId: number | string }) {
  const router = useRouter()
  router.push({ path: '/documents', query: { docId: String(source.documentId) } })
}

function viewOriginal(source: { documentId: number | string }) {
  const token = localStorage.getItem('kf_access_token') || ''
  const url = `${API_BASE}/admin-api/knowledge/document/download?id=${source.documentId}&token=${token}`
  window.open(url, '_blank')
}

const fileInputRef = ref<HTMLInputElement | null>(null)
function triggerFileUpload() {
  fileInputRef.value?.click()
}

async function handleFileUpload(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file || !currentKbId.value) {
    ElMessage.warning('请先选择知识库')
    return
  }
  try {
    await uploadDocumentApi(currentKbId.value, file, 'chat-upload')
    ElMessage.success('文件已上传，正在处理…')
  } catch (error: any) {
    ElMessage.error(error?.message || '上传失败')
  }
}
</script>

<template>
  <div id="page-chat" class="chat-page">
    <!-- 会话列表 -->
    <aside class="session-panel">
      <button class="btn new-session-btn" @click="newSession">
        <svg width="16" height="16" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
        </svg>新建会话
      </button>
      <div class="session-list">
        <div
          v-for="s in sessions"
          :key="s.id"
          class="session-item"
          :class="{ active: s.id === currentSessionId }"
          @click="switchSession(s.id)"
        >
          <div class="session-head">
            <span class="session-title">{{ s.title }}</span>
            <button class="session-del" title="删除会话" @click.stop="removeSession(s.id)">
              <svg width="14" height="14" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div class="session-meta">
            <span class="kb-pill">{{ s.kbName }}</span>
            <span class="session-time">{{ fmtTime(s.updatedAt) }}</span>
          </div>
        </div>
      </div>
    </aside>

    <!-- 消息区 -->
    <div class="chat-main">
      <div class="chat-topbar">
        <div class="chat-title-wrap">
          <span class="chat-title">{{ sessions.find((x) => x.id === currentSessionId)?.title || '新对话' }}</span>
          <el-select
            v-model="currentKbId"
            class="kb-select"
            placeholder="选择知识库"
            size="small"
            @change="onKbChange"
          >
            <el-option v-for="kb in kbs" :key="kb.id" :label="kb.name" :value="kb.id" />
          </el-select>
        </div>
        <button class="btn btn-secondary clear-btn" :disabled="!messages.length" @click="messages = []; saveMessages()">
          清空对话
        </button>
      </div>

      <!-- 消息 -->
      <div ref="messagesAreaRef" class="messages-area">
        <!-- 空态 -->
        <div v-if="!messages.length" class="empty-state">
          <div class="empty-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5" fill="none">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h3 class="serif empty-title">下午好，有什么我可以帮您的？</h3>
          <p class="empty-sub">您可以基于知识库提问，或尝试以下热门话题：</p>
          <div class="quick-grid">
            <button v-for="q in QUICK_QUESTIONS" :key="q" class="quick-item" @click="sendMessage(q)">
              {{ q }}
            </button>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-for="m in messages" :key="m.id" class="msg-row" :class="m.role">
          <!-- AI 消息 -->
          <div v-if="m.role === 'assistant'" class="bubble ai-bubble">
            <div class="ai-tag">AI 答复</div>
            <div v-if="m.content" class="ai-content" v-html="renderMarkdown(m.content)"></div>
            <div v-else class="loading-dots">思考中</div>

            <div v-if="m.confidence !== undefined" class="confidence-pill">
              <svg width="12" height="12" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4" />
              </svg>
              置信度 {{ m.confidence }}%
            </div>

            <div v-if="m.sources && m.sources.length" class="sources-block">
              <div class="sources-head">
                <svg width="14" height="14" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                引用来源 ({{ m.sources.length }})
              </div>
              <div class="sources-grid">
                <div
                  v-for="(src, i) in m.sources"
                  :key="i"
                  class="source-card"
                  @click="jumpToDocument(src)"
                >
                  <span class="page-badge">{{ src.page }}</span>
                  <div class="source-name">{{ src.documentName }}</div>
                  <div class="source-meta">
                    <span>第 {{ src.page }} 页</span>
                    <span class="score">相似度 {{ src.score }}%</span>
                  </div>
                  <button class="btn-icon" title="查看原文" @click.stop="viewOriginal(src)">
                    <svg width="14" height="14" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            <div class="msg-actions">
              <button class="btn-icon" title="点赞" :class="{ rated: m.rating === 'up' }" @click="rateMsg(m, 'up')">
                <svg width="16" height="16" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                </svg>
              </button>
              <button class="btn-icon" title="点踩" :class="{ rated: m.rating === 'down' }" @click="rateMsg(m, 'down')">
                <svg width="16" height="16" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018c.163 0 .326.02.485.06L17 4m-7 10v2a2 2 0 002 2h.095c.5 0 .905-.405.905-.905 0-.714.211 1.412-.608 2.006L17 13V4m-7 10h2" />
                </svg>
              </button>
              <button class="btn-icon" title="复制" @click="copyMsg(m)">
                <svg width="16" height="16" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              </button>
            </div>
          </div>

          <!-- 用户消息 -->
          <div v-else class="bubble user-bubble">{{ m.content }}</div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="input-area">
        <div class="input-inner">
          <!-- 检索模式选择器 -->
          <SearchModeSelector
            v-model:query="inputText"
            v-model:selected-mode="searchMode"
            @change="searchMode = $event"
            @query="inputText = $event"
          />
          <textarea
            v-model="inputText"
            class="form-input input-text"
            rows="3"
            placeholder="请输入您的问题… (Enter 发送，Shift+Enter 换行)"
            @keydown="onInputKeydown"
          ></textarea>
          <div class="input-footer">
            <div class="input-tools">
              <button class="btn-icon" title="上传附件" @click="triggerFileUpload">
                <svg width="18" height="18" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </button>
              <!-- 隐藏的文件输入 -->
              <input
                ref="fileInputRef"
                type="file"
                accept=".pdf,.docx,.txt,.md"
                style="display:none"
                @change="handleFileUpload"
              />
              <button class="btn-icon" title="语音输入" style="display:none">
                <svg width="18" height="18" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 11a7 7 0 01-14 0M12 3v8m0 0v8m0-8h4m-4 0H8" />
                </svg>
              </button>
            </div>
            <button class="btn btn-primary send-btn" :disabled="isStreaming || !inputText.trim()" @click="sendMessage()">
              {{ isStreaming ? '思考中...' : '发送问题' }}
              <svg v-if="!isStreaming" width="16" height="16" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  height: calc(100vh - var(--topbar-h) - 64px);
  min-height: 480px;
  overflow: hidden;
}

/* ---- 会话列表 ---- */
.session-panel {
  width: 280px;
  background: var(--paper-2);
  border-right: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  padding: 16px;
}
.new-session-btn {
  width: 100%;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid var(--line);
  background: var(--btn-solid);
  color: #fff;
  cursor: pointer;
  font-weight: 600;
  margin-bottom: 16px;
  transition: background 0.2s;
}
.new-session-btn:hover {
  background: var(--btn-solid-2);
}
.session-list {
  flex: 1;
  overflow-y: auto;
}
.session-item {
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}
.session-item:hover {
  background: color-mix(in oklab, var(--vermillion) 5%, transparent);
}
.session-item.active {
  background: var(--card);
  border-color: var(--line);
}
.session-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}
.session-title {
  font-weight: 600;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.session-del {
  border: none;
  background: none;
  cursor: pointer;
  color: var(--text-muted);
  opacity: 0;
  padding: 2px;
  display: inline-flex;
  transition: opacity 0.2s;
}
.session-item:hover .session-del {
  opacity: 1;
}
.session-del:hover {
  color: var(--error);
}
.session-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
}
.kb-pill {
  font-size: 11px;
  color: var(--vermillion);
  background: rgba(33, 49, 56, 0.08);
  padding: 2px 6px;
  border-radius: 999px;
}
.session-time {
  font-size: 11px;
  color: var(--text-muted);
}

/* ---- 主区 ---- */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.chat-topbar {
  height: 56px;
  border-bottom: 1px solid var(--line);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  flex-shrink: 0;
}
.chat-title-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}
.chat-title {
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.kb-select {
  width: 150px;
}
.clear-btn {
  font-size: 12px;
  padding: 8px 16px;
}

/* ---- 消息区 ---- */
.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 32px;
}
.msg-row {
  display: flex;
  margin-bottom: 32px;
}
.msg-row.user {
  justify-content: flex-end;
}
.msg-row.assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: 75%;
  padding: 24px;
  border-radius: 10px;
  line-height: 1.7;
  font-size: 14px;
  position: relative;
}
.user-bubble {
  background: var(--ink);
  color: var(--card);
  border-bottom-right-radius: 2px;
  white-space: pre-wrap;
  word-break: break-word;
}
.ai-bubble {
  background: var(--card);
  border: 1px solid var(--line);
  border-top-left-radius: 2px;
  box-shadow: var(--shadow-card);
}
.ai-tag {
  position: absolute;
  top: 0;
  left: 0;
  font-family: 'Noto Serif SC', serif;
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: -0.01em;
  padding: 4px 10px;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 0 0 4px 0;
}
.ai-content {
  margin-top: 8px;
  word-break: break-word;
}
.ai-content :deep(p) {
  margin-bottom: 10px;
}
.ai-content :deep(p:last-child) {
  margin-bottom: 0;
}
.ai-content :deep(ul),
.ai-content :deep(ol) {
  padding-left: 22px;
  margin-bottom: 10px;
}
.ai-content :deep(pre) {
  background: var(--paper-2);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 14px;
  overflow-x: auto;
  margin: 10px 0;
  font-size: 13px;
}
.ai-content :deep(code) {
  font-family: 'SFMono-Regular', Consolas, monospace;
}
.ai-content :deep(blockquote) {
  border-left: 3px solid var(--vermillion);
  padding-left: 12px;
  color: var(--text-muted);
  margin: 10px 0;
}
.loading-dots {
  color: var(--text-muted);
  padding: 6px 0;
}
.loading-dots::after {
  content: '.';
  animation: dots 1.5s steps(4, end) infinite;
}
@keyframes dots {
  0%, 20% { color: transparent; }
  40% { color: var(--vermillion); }
  60%, 100% { color: var(--ink); }
}

.confidence-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: rgba(31, 122, 77, 0.1);
  color: var(--success);
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 12px;
  margin-top: 12px;
}

.sources-block {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--line);
}
.sources-head {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 12px;
}
.sources-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;
  margin-top: 8px;
}
.source-card {
  background: var(--paper-2);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 12px;
  position: relative;
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.2s;
}
.source-card:hover {
  box-shadow: var(--shadow-hover);
  transform: translateY(-1px);
}
.page-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  background: var(--btn-solid);
  color: #fff;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
}
.source-name {
  font-weight: 600;
  margin-bottom: 4px;
  font-size: 14px;
  padding-right: 20px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.source-meta {
  font-size: 12px;
  color: var(--text-muted);
  display: flex;
  justify-content: space-between;
}
.score {
  color: var(--success);
}

/* 消息操作 */
.msg-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--line);
  opacity: 0;
  transition: opacity 0.3s;
}
.ai-bubble:hover .msg-actions {
  opacity: 1;
}
.msg-actions .btn-icon.rated {
  color: var(--vermillion);
  border-color: var(--vermillion);
}
.msg-actions .source-link {
  color: var(--vermillion);
  border: none;
  gap: 4px;
  width: auto;
  padding: 0 4px;
  font-size: 12px;
}

/* ---- 空态 ---- */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: var(--text-muted);
}
.empty-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(33, 49, 56, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 32px;
  color: var(--vermillion);
}
.empty-title {
  font-size: 25px;
  color: var(--ink);
  margin-bottom: 8px;
}
.empty-sub {
  margin-bottom: 32px;
  font-size: 14px;
}
.quick-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  max-width: 600px;
  width: 100%;
}
.quick-item {
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--paper-2);
  cursor: pointer;
  text-align: left;
  font-size: 12px;
  color: var(--ink);
  transition: border-color 0.2s, background 0.2s;
}
.quick-item:hover {
  border-color: var(--vermillion);
  background: var(--card);
}

/* ---- 输入区 ---- */
.input-area {
  border-top: 1px solid var(--line);
  padding: 24px 32px;
  background: var(--paper);
  flex-shrink: 0;
}
.input-inner {
  max-width: 800px;
  margin: 0 auto;
}
.input-text {
  resize: none;
  background: var(--card);
  line-height: 1.6;
}
.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--line);
}
.input-tools {
  display: flex;
  gap: 8px;
}
.send-btn {
  padding: 12px 24px;
}

/* ---- 响应式 ---- */
@media (max-width: 1024px) {
  .chat-page {
    flex-direction: column;
    height: auto;
  }
  .session-panel {
    width: 100%;
    max-height: 200px;
    border-right: none;
    border-bottom: 1px solid var(--line);
  }
  .chat-main {
    min-height: 480px;
  }
}
@media (max-width: 768px) {
  .chat-page {
    height: calc(100vh - var(--topbar-h) - 32px);
  }
  .messages-area {
    padding: 16px;
  }
  .input-area {
    padding: 16px;
  }
  .chat-topbar {
    padding: 0 16px;
  }
  .bubble {
    max-width: 88%;
  }
  .quick-grid {
    grid-template-columns: 1fr;
  }
}
</style>
