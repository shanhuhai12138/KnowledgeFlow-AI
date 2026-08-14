<script setup lang="ts">
// 文档页：筛选（知识库/格式/状态）+ 多选批量删除 + 上传对话框（拖拽+进度）+ 状态徽标 + 预览抽屉 + 分页
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import {
  deleteDocumentsApi,
  downloadUrl,
  getDocumentPageApi,
  uploadDocumentApi,
  getContentApi,
} from '@/api/document'
import { getKbPageApi } from '@/api/kb'
import type { DocumentItem, KnowledgeBase } from '@/types'

const route = useRoute()

// ---------- 筛选 ----------
const filters = reactive({
  filename: '',
  kbId: undefined as number | undefined,
  fileType: '',
  status: '',
})
const searchInput = ref('')

// ---------- 数据 ----------
const docs = ref<DocumentItem[]>([])
const kbs = ref<KnowledgeBase[]>([])
const total = ref(0)
const page = ref(1)
const size = 10
const loading = ref(false)
const selectedIds = ref<number[]>([])

const TYPE_OPTIONS = [
  { label: '所有格式', value: '' },
  { label: 'PDF', value: 'pdf' },
  { label: 'Word', value: 'docx' },
  { label: 'Markdown', value: 'md' },
  { label: 'TXT', value: 'txt' },
]
const STATUS_OPTIONS = [
  { label: '所有状态', value: '' },
  { label: '已就绪', value: 'processed' },
  { label: '处理中', value: 'processing' },
  { label: '待处理', value: 'pending' },
  { label: '失败', value: 'failed' },
]

async function loadKbs() {
  try {
    const data = await getKbPageApi({ pageNo: 1, pageSize: 100 })
    kbs.value = data?.list || []
  } catch {
    kbs.value = []
  }
}

async function loadDocs() {
  loading.value = true
  try {
    const data = await getDocumentPageApi({
      pageNo: page.value,
      pageSize: size,
      kbId: filters.kbId,
      fileType: filters.fileType || undefined,
      status: filters.status || undefined,
      filename: filters.filename || undefined,
    })
    docs.value = data?.list || []
    total.value = data?.total || 0
    // 清理已不存在的选中项
    const ids = new Set(docs.value.map((d) => d.id))
    selectedIds.value = selectedIds.value.filter((id) => ids.has(id))
  } catch {
    docs.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function onSearch() {
  filters.filename = searchInput.value.trim()
  page.value = 1
  loadDocs()
}

function onFilterChange() {
  page.value = 1
  loadDocs()
}

// ---------- 选择与批量删除 ----------
const allChecked = computed(() => docs.value.length > 0 && selectedIds.value.length === docs.value.length)

function toggleSelectAll(e: Event) {
  const checked = (e.target as HTMLInputElement).checked
  selectedIds.value = checked ? docs.value.map((d) => d.id) : []
}

function toggleOne(id: number, e: Event) {
  const checked = (e.target as HTMLInputElement).checked
  if (checked) {
    if (!selectedIds.value.includes(id)) selectedIds.value.push(id)
  } else {
    selectedIds.value = selectedIds.value.filter((x) => x !== id)
  }
}

async function batchDelete() {
  if (!selectedIds.value.length) return
  try {
    await ElMessageBox.confirm(`确定删除选中的 ${selectedIds.value.length} 个文档？删除后向量数据将一并清理。`, '批量删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteDocumentsApi(selectedIds.value)
    ElMessage.success('删除成功')
    selectedIds.value = []
    loadDocs()
  } catch {
    /* toast 已由拦截器处理 */
  }
}

async function deleteOne(d: DocumentItem) {
  try {
    await ElMessageBox.confirm(`确定删除文档「${d.filename}」？`, '删除文档', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteDocumentsApi([d.id])
    ElMessage.success('删除成功')
    loadDocs()
  } catch {
    /* toast 已由拦截器处理 */
  }
}

// ---------- 格式化 ----------
function fmtSize(bytes: number) {
  if (!bytes && bytes !== 0) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}
function fmtTime(t: number | string | undefined) {
  if (!t && t !== 0) return '-'
  return dayjs(t).format('YYYY-MM-DD HH:mm')
}
const STATUS_META: Record<string, { label: string; color: string; bg: string }> = {
  pending: { label: '待处理', color: 'var(--text-muted)', bg: 'rgba(110,102,91,.12)' },
  processing: { label: '处理中', color: 'var(--warning)', bg: 'rgba(165,131,62,.14)' },
  processed: { label: '已就绪', color: 'var(--success)', bg: 'rgba(31,122,77,.12)' },
  failed: { label: '失败', color: 'var(--error)', bg: 'rgba(176,71,47,.12)' },
}

// ---------- 分页 ----------
const pageCount = computed(() => Math.max(1, Math.ceil(total.value / size)))
const pageNumbers = computed(() => {
  const pc = pageCount.value
  const cur = page.value
  if (pc <= 5) return Array.from({ length: pc }, (_, i) => i + 1)
  const set = new Set<number>([1, pc, cur - 1, cur, cur + 1])
  return [...set].filter((n) => n >= 1 && n <= pc).sort((a, b) => a - b)
})
function goPage(p: number) {
  if (p < 1 || p > pageCount.value || p === page.value) return
  page.value = p
  loadDocs()
}
const pagerInfo = computed(() => {
  if (!total.value) return '共 0 条记录'
  const from = (page.value - 1) * size + 1
  const to = Math.min(page.value * size, total.value)
  return `显示 ${from} 到 ${to} 条，共 ${total.value} 条记录`
})

// ---------- 上传对话框 ----------
const uploadVisible = ref(false)
const uploadFile = ref<File | null>(null)
const uploadKbId = ref<number | undefined>()
const uploadTags = ref('')
const uploading = ref(false)
const uploadPercent = ref(0)
const fileInputRef = ref<HTMLInputElement | null>(null)
const dragOver = ref(false)

function openUpload() {
  if (!kbs.value.length) {
    ElMessage.warning('请先创建知识库')
    return
  }
  uploadFile.value = null
  uploadTags.value = ''
  uploadPercent.value = 0
  uploadKbId.value = kbs.value[0]?.id
  uploadVisible.value = true
}

function pickFile() {
  fileInputRef.value?.click()
}
function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.length) uploadFile.value = input.files[0]
  input.value = ''
}
function onDrop(e: DragEvent) {
  dragOver.value = false
  const f = e.dataTransfer?.files?.[0]
  if (f) uploadFile.value = f
}

async function startUpload() {
  if (!uploadFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  if (!uploadKbId.value) {
    ElMessage.warning('请选择目标知识库')
    return
  }
  uploading.value = true
  uploadPercent.value = 0
  try {
    const res = await uploadDocumentApi(uploadKbId.value, uploadFile.value, uploadTags.value.trim(), (p) => {
      uploadPercent.value = p
    })
    if (res?.code === 0) {
      ElMessage.success('文档上传成功，正在后台解析处理')
      uploadVisible.value = false
      loadDocs()
    } else {
      ElMessage.error(res?.message || '上传失败')
    }
  } catch {
    /* toast 已处理 */
  } finally {
    uploading.value = false
  }
}

// ---------- 预览抽屉 ----------
const previewVisible = ref(false)
const previewDoc = ref<DocumentItem | null>(null)
const previewContent = ref('')
const previewLoading = ref(false)
const previewError = ref('')

async function openPreview(d: DocumentItem) {
  previewDoc.value = d
  previewVisible.value = true
  previewContent.value = ''
  previewError.value = ''
  previewLoading.value = true
  try {
    const res = await getContentApi(d.id)
    if (res != null && res !== '') {
      previewContent.value = res
    } else {
      previewError.value = '获取内容失败'
    }
  } catch {
    previewError.value = '获取内容失败'
  } finally {
    previewLoading.value = false
  }
}
function downloadDoc(d: DocumentItem) {
  window.open(downloadUrl(d.id), '_blank')
}

// ---------- 初始化 ----------
onMounted(async () => {
  await loadKbs()
  // 顶栏全局搜索带入
  const kw = route.query.kw as string | undefined
  if (kw) {
    searchInput.value = kw
    filters.filename = kw
  }
  loadDocs()
})
</script>

<template>
  <div class="docs-page page-enter">
    <div class="page-head">
      <h1 class="serif page-title">文档管理</h1>
      <div class="head-actions">
        <span class="doc-count">{{ total }} 个文档</span>
        <div class="btn-group">
          <button class="btn btn-secondary" @click="loadDocs">
            <svg width="16" height="16" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>刷新
          </button>
          <button class="btn btn-secondary" :disabled="!selectedIds.length" @click="batchDelete">
            <svg width="16" height="16" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>批量删除
          </button>
          <button class="btn btn-primary" @click="openUpload">
            <svg width="16" height="16" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>上传文档
          </button>
        </div>
      </div>
    </div>

    <!-- 筛选条 -->
    <div class="filter-bar">
      <div class="search-box">
        <svg width="16" height="16" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input v-model="searchInput" class="filter-input" placeholder="搜索文档名称…" @keyup.enter="onSearch" />
      </div>
      <select v-model="filters.kbId" class="form-input filter-select" @change="onFilterChange">
        <option :value="undefined">所有知识库</option>
        <option v-for="kb in kbs" :key="kb.id" :value="kb.id">{{ kb.name }}</option>
      </select>
      <select v-model="filters.fileType" class="form-input filter-select" @change="onFilterChange">
        <option v-for="o in TYPE_OPTIONS" :key="o.value" :value="o.value">{{ o.label }}</option>
      </select>
      <select v-model="filters.status" class="form-input filter-select" @change="onFilterChange">
        <option v-for="o in STATUS_OPTIONS" :key="o.value" :value="o.value">{{ o.label }}</option>
      </select>
    </div>

    <!-- 表格 -->
    <div class="card table-card" v-loading="loading">
      <table class="doc-table">
        <thead>
          <tr>
            <th class="col-check"><input type="checkbox" :checked="allChecked" @change="toggleSelectAll" /></th>
            <th>文档名称</th>
            <th>所属知识库</th>
            <th>大小 / 页数</th>
            <th>上传人</th>
            <th>状态</th>
            <th>创建时间</th>
            <th>更新时间</th>
            <th class="col-op">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in docs" :key="d.id">
            <td class="col-check">
              <input type="checkbox" :checked="selectedIds.includes(d.id)" @change="toggleOne(d.id, $event)" />
            </td>
            <td>
              <div class="doc-cell">
                <div class="file-icon">
                  <svg width="18" height="18" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div class="doc-info">
                  <div class="doc-name" :title="d.filename">{{ d.filename }}</div>
                  <div v-if="d.tags?.length" class="doc-tags">
                    <span v-for="t in d.tags" :key="t" class="tag">{{ t }}</span>
                  </div>
                </div>
              </div>
            </td>
            <td class="cell-muted">{{ d.kbName }}</td>
            <td class="cell-num">{{ fmtSize(d.fileSize) }} / {{ d.pageCount || '-' }}P</td>
            <td class="cell-muted">{{ d.uploader || '-' }}</td>
            <td>
              <span class="status-badge" :style="{ color: STATUS_META[d.status]?.color, background: STATUS_META[d.status]?.bg }">
                <span class="status-dot" :style="{ background: STATUS_META[d.status]?.color }"></span>
                {{ STATUS_META[d.status]?.label || d.status }}
              </span>
            </td>
            <td class="cell-time">{{ fmtTime(d.createdAt) }}</td>
            <td class="cell-time">{{ fmtTime(d.updatedAt) }}</td>
            <td class="col-op">
              <div class="op-btns">
                <button class="btn-icon" title="预览" @click="openPreview(d)">
                  <svg width="16" height="16" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                </button>
                <button class="btn-icon" title="下载" @click="downloadDoc(d)">
                  <svg width="16" height="16" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                </button>
                <button class="btn-icon danger" title="删除" @click="deleteOne(d)">
                  <svg width="16" height="16" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="!docs.length && !loading">
            <td colspan="9" class="empty-row">暂无文档，点击右上角「上传文档」开始建立知识库</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分页 -->
    <div class="pager">
      <span class="pager-info">{{ pagerInfo }}</span>
      <div class="pager-btns">
        <button class="btn btn-secondary pager-btn" :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
        <template v-for="(n, i) in pageNumbers" :key="n">
          <span v-if="i > 0 && n - pageNumbers[i - 1] > 1" class="pager-ellipsis">…</span>
          <button
            class="btn pager-btn"
            :class="n === page ? 'btn-primary' : 'btn-secondary'"
            @click="goPage(n)"
          >{{ n }}</button>
        </template>
        <button class="btn btn-secondary pager-btn" :disabled="page >= pageCount" @click="goPage(page + 1)">下一页</button>
      </div>
    </div>

    <!-- 上传对话框 -->
    <el-dialog v-model="uploadVisible" title="上传文档至知识库" width="560px" :close-on-click-modal="false">
      <div class="upload-body">
        <div class="form-field">
          <label class="form-label">目标知识库</label>
          <el-select v-model="uploadKbId" placeholder="选择知识库" style="width: 100%">
            <el-option v-for="kb in kbs" :key="kb.id" :label="kb.name" :value="kb.id" />
          </el-select>
        </div>
        <div
          class="dropzone"
          :class="{ 'drag-over': dragOver }"
          @click="pickFile"
          @dragover.prevent="dragOver = true"
          @dragleave="dragOver = false"
          @drop.prevent="onDrop"
        >
          <svg width="48" height="48" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5" fill="none" class="dz-icon">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          <div class="dz-title">{{ uploadFile ? uploadFile.name : '点击或拖拽文件到此处上传' }}</div>
          <div class="dz-sub">支持 PDF, DOCX, TXT, MD 格式，单个文件最大 50MB</div>
          <input ref="fileInputRef" type="file" accept=".pdf,.docx,.txt,.md" hidden @change="onFileChange" />
        </div>
        <div class="form-field" style="margin-top: 16px">
          <label class="form-label">标签（逗号分隔，可选）</label>
          <input v-model="uploadTags" class="form-input" placeholder="如：需求, 产品" />
        </div>
        <div v-if="uploading" class="upload-progress">
          <div class="progress-label">
            <span>{{ uploadFile?.name }}</span>
            <span>{{ uploadPercent }}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: uploadPercent + '%' }"></div>
          </div>
        </div>
      </div>
      <template #footer>
        <button class="btn btn-secondary" :disabled="uploading" @click="uploadVisible = false">取消</button>
        <button class="btn btn-primary" :disabled="uploading || !uploadFile" @click="startUpload">
          {{ uploading ? '上传中...' : '开始处理' }}
        </button>
      </template>
    </el-dialog>

    <!-- 预览抽屉 -->
    <el-drawer v-model="previewVisible" :title="previewDoc?.filename || '文档预览'" size="720px">
      <div v-if="previewDoc" class="preview-body">
        <div class="preview-meta">
          <span class="status-badge" :style="{ color: STATUS_META[previewDoc.status]?.color, background: STATUS_META[previewDoc.status]?.bg }">
            <span class="status-dot" :style="{ background: STATUS_META[previewDoc.status]?.color }"></span>
            {{ STATUS_META[previewDoc.status]?.label || previewDoc.status }}
          </span>
          <span class="meta-item">知识库：{{ previewDoc.kbName }}</span>
          <span class="meta-item">大小：{{ fmtSize(previewDoc.fileSize) }}</span>
          <span class="meta-item">页数：{{ previewDoc.pageCount || '-' }}</span>
          <span class="meta-item">类型：{{ previewDoc.fileType?.toUpperCase() }}</span>
        </div>
        <div class="preview-actions">
          <button class="btn btn-secondary" @click="downloadDoc(previewDoc)">
            <svg width="16" height="16" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>下载原文件
          </button>
        </div>
        <!-- 加载状态 -->
        <div v-if="previewLoading" class="preview-loading">
          <div class="loading-spinner"></div>
          <span>正在解析文档内容...</span>
        </div>
        <!-- 错误状态 -->
        <div v-else-if="previewError" class="preview-error">
          <svg width="24" height="24" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span>{{ previewError }}</span>
        </div>
        <!-- 文档内容 -->
        <div v-else-if="previewContent" class="preview-content">
          <pre>{{ previewContent }}</pre>
        </div>
        <!-- 空状态 -->
        <div v-else class="preview-empty">
          <svg width="48" height="48" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5" fill="none">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span>文档内容暂不可用</span>
          <p>该文档可能尚未处理完成或格式不支持预览</p>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script lang="ts">
export default {
  name: 'DocumentsView',
}
</script>

<style scoped>
.page-title {
  font-size: 39px;
  margin-bottom: 16px;
}
.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}
.doc-count {
  font-size: 12px;
  color: var(--text-muted);
}
.head-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}
.btn-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* 筛选条 */
.filter-bar {
  display: flex;
  gap: 16px;
  align-items: center;
  background: var(--paper-2);
  border: 1px solid var(--line);
  border-radius: var(--card-radius);
  padding: 12px;
  margin-bottom: var(--sp-comfortable);
  flex-wrap: wrap;
}
.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 8px 12px;
  flex: 1;
  min-width: 200px;
  color: var(--text-muted);
}
.filter-input {
  border: none;
  background: none;
  outline: none;
  flex: 1;
  font-size: 13px;
  color: var(--ink);
}
.filter-select {
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 8px 12px;
  min-width: 120px;
  width: auto;
  font-size: 13px;
  background: var(--card);
  cursor: pointer;
}

/* 表格 */
.table-card {
  overflow: hidden;
  padding: 0;
  box-shadow: var(--shadow-card);
}
.doc-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.doc-table thead tr {
  border-bottom: 1px solid var(--line);
  background: var(--paper-2);
}
.doc-table th {
  padding: 12px 16px;
  text-align: left;
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-weight: 600;
  white-space: nowrap;
}
.doc-table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--line);
  vertical-align: middle;
}
.doc-table tbody tr {
  transition: background 0.15s;
}
.doc-table tbody tr:hover {
  background: var(--paper-2);
}
.col-check {
  width: 40px;
}
.col-op {
  width: 130px;
}
input[type='checkbox'] {
  accent-color: var(--vermillion);
  cursor: pointer;
}
.doc-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}
.file-icon {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  background: var(--paper-2);
  border: 1px solid var(--line);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--vermillion);
  flex-shrink: 0;
}
.doc-name {
  font-weight: 600;
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.doc-tags {
  display: flex;
  gap: 4px;
  margin-top: 4px;
}
.tag {
  font-size: 10px;
  padding: 2px 8px;
  background: var(--paper-2);
  border: 1px solid var(--line);
  border-radius: 4px;
  color: var(--text-muted);
}
.cell-muted {
  color: var(--text-muted);
}
.cell-num {
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}
.cell-time {
  color: var(--text-muted);
  font-size: 12px;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.op-btns {
  display: flex;
  gap: 4px;
}
.op-btns .btn-icon.danger {
  color: var(--error);
}
.empty-row {
  text-align: center;
  color: var(--text-muted);
  padding: 48px !important;
}

/* 分页 */
.pager {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  font-size: 12px;
  color: var(--text-muted);
  flex-wrap: wrap;
  gap: 12px;
}
.pager-btns {
  display: flex;
  gap: 8px;
  align-items: center;
}
.pager-btn {
  font-size: 12px;
  padding: 8px 14px;
}
.pager-ellipsis {
  color: var(--text-muted);
  padding: 0 2px;
}

/* 上传 */
.upload-body {
  padding-top: 4px;
}
.form-field {
  margin-bottom: 16px;
}
.dropzone {
  border: 2px dashed var(--line);
  border-radius: var(--card-radius);
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: var(--paper-2);
}
.dropzone.drag-over {
  border-color: var(--vermillion);
  background: color-mix(in oklab, var(--vermillion) 6%, var(--paper-2));
}
.dz-icon {
  color: var(--text-muted);
  margin-bottom: 12px;
}
.dz-title {
  font-weight: 600;
  margin-bottom: 8px;
  font-size: 14px;
}
.dz-sub {
  font-size: 12px;
  color: var(--text-muted);
}
.upload-progress {
  margin-top: 16px;
}
.progress-label {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 4px;
}

/* 预览 */
.preview-body {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.preview-meta {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
.meta-item {
  font-size: 12px;
  color: var(--text-muted);
}
.preview-actions {
  margin-bottom: 16px;
}

/* 预览内容 */
.preview-loading,
.preview-error,
.preview-content,
.preview-empty {
  padding: 24px;
  text-align: center;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.preview-loading {
  color: var(--text-muted);
}

.preview-loading .loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--line);
  border-top-color: var(--vermillion);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.preview-error {
  color: var(--error);
}

.preview-error svg {
  opacity: 0.6;
}

.preview-content {
  text-align: left;
  width: 100%;
  max-height: 500px;
  overflow-y: auto;
}

.preview-content pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-primary);
  background: var(--paper-2);
  padding: 16px;
  border-radius: var(--input-radius);
  border: 1px solid var(--line);
}

.preview-empty {
  color: var(--text-muted);
}

.preview-empty span {
  display: block;
  color: var(--text-secondary);
  font-size: 14px;
  margin-top: 12px;
}

.preview-empty p {
  color: var(--text-muted);
  font-size: 12px;
}

@media (max-width: 768px) {
  .doc-table {
    min-width: 900px;
  }
  .table-card {
    overflow-x: auto;
  }
}
</style>
