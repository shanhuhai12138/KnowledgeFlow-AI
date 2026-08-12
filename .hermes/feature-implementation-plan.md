# 占位功能实现方案

> 时间：2026-08-04  
> 范围：通知、报表导出、来源跳转、查看原文、上传附件

---

## 一、通知系统（Topbar.vue:63）

### 当前状态
```vue
<button @click="ElMessage.info('暂无新通知')">
```

### 功能设计

| 项目 | 说明 |
|------|------|
| **触发场景** | 文档处理完成、知识库成员变更、系统告警 |
| **数据结构** | `{ id, type, title, message, read, createdAt, link? }` |
| **通知类型** | `doc_processed`（文档就绪）、`member_added`（成员添加）、`system`（系统） |
| **展示方式** | 下拉面板，按时间排序，未读标记 |

### 实现方案

#### 方案 A：WebSocket 实时推送（推荐用于生产）
```typescript
// 后端：Spring Boot + WebSocket
@ServerEndpoint("/ws/notifications/{userId}")
public class NotificationWebSocket {
    // 推送通知给指定用户
}

// 前端：连接 WebSocket
const ws = new WebSocket(`ws://localhost:8080/ws/notifications/${userId}`)
ws.onmessage = (e) => {
  const notification = JSON.parse(e.data)
  notifications.value.unshift(notification)
}
```

#### 方案 B：轮询查询（简单实现）
```typescript
// 每 30 秒查询一次未读通知
setInterval(async () => {
  const res = await getUnreadNotificationsApi()
  if (res.count > unreadCount.value) {
    ElMessage.success(`你有 ${res.count - unreadCount.value} 条新通知`)
  }
  unreadCount.value = res.count
}, 30000)
```

#### 方案 C：本地事件模拟（演示用）
```typescript
// 模拟通知（仅用于演示）
function simulateNotification() {
  const notifications = [
    { id: 1, type: 'doc', title: '文档处理完成', message: '《产品需求文档.pdf》已就绪' },
    { id: 2, type: 'member', title: '成员添加', message: '张三 加入了知识库' },
  ]
  // 随机显示
  ElNotification(notifications[Math.floor(Math.random() * notifications.length)])
}
```

### 后端 API 设计
```java
// GET /admin-api/knowledge/notifications
// 返回：List<Notification>

// POST /admin-api/knowledge/notifications/read
// 标记已读

// DELETE /admin-api/knowledge/notifications/{id}
// 删除通知
```

---

## 二、报表导出（AnalyticsView.vue:191）

### 当前状态
```vue
<button @click="ElMessage.info('报表导出中…')">
```

### 功能设计

| 项目 | 说明 |
|------|------|
| **导出格式** | PDF（带图表）、Excel（原始数据）、CSV（简单数据） |
| **内容范围** | 统计概览、趋势图、文档类型分布、热门查询 |
| **生成方式** | 后端生成 + 前端下载，或前端用 jsPDF 生成 |

### 实现方案

#### 方案 A：后端生成 PDF（推荐）
```typescript
// 前端：调用接口下载
async function exportReport() {
  const res = await fetch('/admin-api/knowledge/stat/export?format=pdf', {
    headers: { 'Authorization': `Bearer ${token}` }
  })
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `知识看板报表_${dayjs().format('YYYYMMDD')}.pdf`
  a.click()
}
```

```java
// 后端：使用 iText 或 Apache PDFBox
@GetMapping("/stat/export")
public void exportReport(@RequestParam String format, HttpServletResponse response) {
    if ("pdf".equals(format)) {
        PdfReportGenerator.generate(overview, trend, docTypes, hot)
            .writeTo(response.getOutputStream());
    } else if ("excel".equals(format)) {
        ExcelReportGenerator.generate(...).writeTo(response.getOutputStream());
    }
}
```

#### 方案 B：前端生成（轻量）
```typescript
import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'

async function exportPDF() {
  const element = document.getElementById('analytics-content')
  const canvas = await html2canvas(element)
  const pdf = new jsPDF()
  pdf.addImage(canvas.toDataURL(), 'PNG', 0, 0)
  pdf.save('report.pdf')
}
```

### 后端 API 设计
```java
// GET /admin-api/knowledge/stat/export?format=pdf|excel|csv
// 返回：文件流
```

---

## 三、来源卡片跳转（ChatView.vue:465）

### 当前状态
```vue
@click="ElMessage.info(`跳转至文档: ${src.documentName}`)"
```

### 功能设计

| 项目 | 说明 |
|------|------|
| **跳转目标** | DocumentsView 页面，自动定位到对应文档 |
| **定位方式** | 传入 documentId 作为查询参数，打开文档预览抽屉 |
| **用户体验** | 点击后切换到文档管理页，显示该文档详情 |

### 实现方案

#### 方案 A：路由跳转（推荐）
```typescript
// ChatView.vue
import { useRouter } from 'vue-router'
const router = useRouter()

function jumpToDocument(source: Source) {
  router.push({
    path: '/documents',
    query: {
      docId: source.documentId,
      kbId: currentKbId.value,
      highlight: `page-${source.page}`
    }
  })
}
```

```vue
<!-- DocumentsView.vue -->
<script setup>
const route = useRoute()
const docId = route.query.docId as string

onMounted(() => {
  if (docId) {
    // 高亮显示该文档
    highlightDocument(docId)
    // 打开预览抽屉
    openPreview(parseInt(docId))
  }
})
</script>
```

#### 方案 B：预览抽屉（不跳转页面）
```typescript
// 在聊天页内打开预览抽屉
const previewVisible = ref(false)
const previewDoc = ref<DocumentItem | null>(null)

function jumpToDocument(source: Source) {
  previewDoc.value = source.documentId
  previewVisible.value = true
}
```

### 后端 API 设计
```java
// GET /admin-api/knowledge/document/get?id=xxx
// 返回文档详情（用于预览）

// GET /admin-api/knowledge/document/preview?id=xxx&page=5
// 返回指定页的内容（用于定位）
```

---

## 四、查看原文（ChatView.vue:493）

### 当前状态
```vue
<button @click="ElMessage.info('跳转至原文档')">
```

### 功能设计

| 项目 | 说明 |
|------|------|
| **用途** | 查看 AI 回答引用的完整文档内容 |
| **展示方式** | 右侧抽屉或新标签页打开文档预览 |
| **内容** | 文档全文或指定页内容 |

### 实现方案

#### 方案 A：预览抽屉（推荐）
```typescript
// 在 ChatView 内添加预览抽屉
const previewVisible = ref(false)
const previewUrl = ref('')

function viewOriginal(source: Source) {
  // 获取文档下载链接
  getDownloadUrlApi(source.documentId).then(url => {
    previewUrl.value = url
    previewVisible.value = true
  })
}
```

```vue
<!-- 预览抽屉 -->
<el-drawer v-model="previewVisible" title="文档预览" size="50%">
  <iframe :src="previewUrl" style="width:100%;height:70vh;border:none;" />
</el-drawer>
```

#### 方案 B：新标签页打开
```typescript
function viewOriginal(source: Source) {
  getDownloadUrlApi(source.documentId).then(url => {
    window.open(url, '_blank')
  })
}
```

### 后端 API 设计
```java
// GET /admin-api/knowledge/document/download-url?id=xxx
// 返回：{ url: "https://minio.../document.pdf" }

// GET /admin-api/knowledge/document/preview?id=xxx&page=5
// 返回：{ content: "第5页内容...", totalPage: 20 }
```

---

## 五、上传附件（ChatView.vue:519）

### 当前状态
```vue
<button @click="ElMessage.info('文件选择器已打开')">
```

### 功能设计

| 项目 | 说明 |
|------|------|
| **用途** | 用户在聊天时上传文件作为上下文 |
| **支持格式** | PDF、DOCX、TXT、MD（与文档管理一致） |
| **处理方式** | 上传到 MinIO，异步处理，结果关联到当前会话 |

### 实现方案

#### 方案 A：简单上传（推荐演示用）
```typescript
const uploadVisible = ref(false)
const uploadingFile = ref<File | null>(null)

function handleFileSelect(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) {
    uploadingFile.value = file
    uploadVisible.value = true
  }
}

async function uploadAndChat() {
  if (!uploadingFile.value) return
  
  // 上传文件
  const result = await uploadDocumentApi(
    currentKbId.value!, 
    uploadingFile.value, 
    'chat-upload'
  )
  
  // 提示用户
  ElMessage.success(`文件「${uploadingFile.value.name}」已上传，正在处理...`)
  
  // 清空
  uploadingFile.value = null
  uploadVisible.value = false
}
```

```vue
<!-- 隐藏的文件输入 -->
<input 
  type="file" 
  ref="fileInputRef" 
  style="display:none"
  accept=".pdf,.docx,.txt,.md"
  @change="handleFileSelect"
/>

<!-- 按钮触发 -->
<button @click="$refs.fileInputRef.click()">
  上传附件
</button>
```

#### 方案 B：拖拽上传
```vue
<div class="upload-zone" @drop.prevent="handleDrop" @dragover.prevent>
  <svg>...</svg>
  <p>拖拽文件到此处，或点击上传</p>
</div>
```

### 后端 API 设计
```java
// POST /admin-api/knowledge/document/upload
// 参数：kbId, file, tags="chat-upload"
// 返回：{ id: 123, status: "processing" }

// GET /admin-api/knowledge/document/page?tags=chat-upload
// 查询最近上传的聊天附件
```

---

## 六、实现优先级建议

### P1 - 核心体验（建议实现）
| 功能 | 难度 | 价值 |
|------|------|------|
| 来源跳转 | ⭐ 低 | 高 - 提升可信度 |
| 查看原文 | ⭐ 低 | 高 - 验证引用 |

### P2 - 增强功能（可选）
| 功能 | 难度 | 价值 |
|------|------|------|
| 上传附件 | ⭐⭐ 中 | 中 - 扩展使用场景 |
| 报表导出 | ⭐⭐ 中 | 中 - 商务需求 |

### P3 - 高级功能（后续）
| 功能 | 难度 | 价值 |
|------|------|------|
| 通知系统 | ⭐⭐⭐ 高 | 低 - 非核心需求 |

---

## 七、最小实现方案（演示可用）

如果只需演示，可以采用最简方案：

### 1. 来源跳转（5 行代码）
```typescript
// ChatView.vue
import { useRouter } from 'vue-router'
const router = useRouter()

function jumpToDoc(source: Source) {
  router.push({ path: '/documents', query: { docId: source.documentId } })
}
```

### 2. 查看原文（3 行代码）
```typescript
// 直接打开下载链接
function viewOriginal(source: Source) {
  window.open(`/admin-api/knowledge/document/download-url?id=${source.documentId}`, '_blank')
}
```

### 3. 上传附件（复用现有功能）
```typescript
// 直接调用已有的 uploadDocumentApi
function handleUpload(file: File) {
  uploadDocumentApi(currentKbId.value!, file, 'chat').then(() => {
    ElMessage.success('文件已上传')
  })
}
```

### 4. 通知系统（暂时隐藏按钮）
```vue
<!-- 直接隐藏 -->
<!-- <button class="btn-icon plain" title="通知">...</button> -->
```

### 5. 报表导出（暂时隐藏按钮）
```vue
<!-- 直接隐藏 -->
<!-- <button class="btn btn-secondary" @click="...">导出报表</button> -->
```

---

**报告生成时间**：2026-08-04  
**生成工具**：Agnes (Hermes Agent)
