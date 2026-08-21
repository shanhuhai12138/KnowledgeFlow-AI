# Agent 工作流设计评估

## 当前问题

### 1. SSE 事件流断裂
- **现象**：步骤始终"等待中"，不实时更新
- **原因**：`updateWorkflowSteps([event.step])` 接收单个步骤，但替换整个数组
- **后端**：SSE 每次发送单条步骤 `{type: 'step', step: {...}}`
- **前端**：`updateWorkflowSteps` 用单步替换完整列表，导致之前完成的步骤丢失

### 2. 页面刷新状态丢失
- **现象**：重新进入页面，工作流失效
- **原因**：状态存储在组件 `ref` 中（内存），刷新后重置
- **缺少**：localStorage 持久化或数据库存储

### 3. EventSource 连接问题
- **现象**：前端可能无法连接到 SSE 端点
- **原因**：API_BASE 配置、Nginx 代理、CORS 等问题

---

## 设计对比

### 方案 A：保持 SSE（实时性高，复杂）
```
优点：实时推送，用户体验好
缺点：实现复杂，状态管理困难，刷新丢失
```

### 方案 B：轮询 + 持久化（推荐）
```
优点：简单可靠，状态可恢复，易于调试
缺点：2-3 秒延迟（可接受）
```

### 方案 C：WebSocket（双向通信，最复杂）
```
优点：双向实时，功能强大
缺点：需要额外依赖，实现复杂
```

---

## 推荐方案：轮询 + localStorage 持久化

### 核心设计

1. **启动工作流**
   - 调用 `POST /ai/agent` 获取 runId
   - 将 runId 存入 localStorage
   - 开始轮询 `GET /ai/agent/status?runId=X`（每 2 秒）

2. **轮询更新**
   - 每次获取完整 steps 数组
   - 更新 workflowSteps 显示
   - 检测到 `awaiting_approval` 状态时停止轮询，显示人工确认 UI

3. **人工确认**
   - 用户点击"批准"或"拒绝"
   - 调用 `POST /ai/agent/approve`
   - 恢复轮询等待完成

4. **完成/错误**
   - 检测到 `done` 或 `error` 状态
   - 停止轮询
   - 显示报告

5. **页面刷新恢复**
   - 加载页面时检查 localStorage
   - 如果有未完成的 runId，恢复显示并继续轮询
   - 如果超过 10 分钟，标记为过期

---

## 实现步骤

### 后端（无需修改）
- 保持 `/ai/agent`、`/ai/agent/status`、`/ai/agent/approve` 接口
- SSE 端点可保留但不再使用

### 前端改造

#### 1. 修改 agent.ts
- 移除 `subscribeAgentEvents`
- 添加 `pollAgentStatus` 函数

#### 2. 修改 AgentView.vue
- 添加 localStorage 持久化
- 实现轮询逻辑
- 处理页面刷新恢复

#### 3. 状态管理
```typescript
// localStorage keys
const STORAGE_KEY_RUN = 'agent_run_'
const STORAGE_KEY_DEADLINE = 'agent_deadline_'

// 持久化 runId
localStorage.setItem(STORAGE_KEY_RUN + runId, JSON.stringify({
  startTime: Date.now(),
  query: '...',
  kbId: 1
}))

// 恢复时检查
const savedRunId = localStorage.getItem('agent_last_run_id')
if (savedRunId) {
  const info = JSON.parse(localStorage.getItem(STORAGE_KEY_RUN + savedRunId) || '{}')
  if (Date.now() - info.startTime < 10 * 60 * 1000) {
    // 继续轮询
  }
}
```

---

##  UI 改进

### 当前问题
- 步骤状态不更新（等待中）
- 人工确认 UI 不显示（因为 SSE 事件未到达）
- 报告不显示（因为 done 事件未到达）

### 改进方向
1. **步骤可视化**
   - 使用进度条显示每个步骤
   - 完成后显示检查图标
   - 运行中显示旋转图标

2. **人工确认**
   - 摘要和分类预览
   - 倒计时进度条
   - 批准/拒绝按钮

3. **报告展示**
   - Markdown 渲染
   - 复制/下载按钮

---

## 结论

**建议采用轮询 + localStorage 持久化方案**：
- 实现简单，调试方便
- 状态可恢复，用户体验更好
- 不依赖 SSE 连接稳定性
- 符合当前项目规模和需求
