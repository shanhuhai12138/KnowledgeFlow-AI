# Human-in-the-Loop 实现状态分析

## 问题
README 描述了 "Agent 工作流（human-in-the-loop）"，但前端 ChatView 没有相关 UI。

## 当前状态

### 后端 (Python AI 服务) - ✅ 已实现

#### Agent 工作流图
```
START → retrieve → summarize → classify → report_gate (人工确认) → report → END
```

#### API 端点
| 端点 | 方法 | 功能 |
|------|------|------|
| `/ai/agent` | POST | 启动 Agent 工作流 |
| `/ai/agent/status` | GET | 查询工作流状态 |
| `/ai/agent/approve` | POST | 人工确认 (approve/reject) |
| `/ai/agent/events` | GET (SSE) | 实时推送步骤事件 |

#### 关键代码 (`agent_graph.py`)
```python
def _report_gate(state: AgentState) -> AgentState:
    """human-in-the-loop: 生成报告前暂停，等待人工 approve/reject"""
    run = store.get(state["_run_id"])
    store.set_status(run.run_id, "awaiting_approval")
    deadline = time.time() + 600  # 最多等 10 分钟
    while time.time() < deadline and run.approved is None:
        time.sleep(1)
    approved = run.approved == "approve"
    return {"approved": approved}
```

---

### 前端 (Vue 3) - ❌ 未实现

#### 当前 ChatView 功能
- ✅ 简单问答 (SSE 流式)
- ✅ 来源卡片显示
- ✅ 置信度显示
- ✅ 点赞/点踩
- ❌ **没有 Agent 工作流入口**
- ❌ **没有人工确认 UI**
- ❌ **没有工作流状态显示**

---

## 需要实现的内容

### 1. 前端新增 Agent 功能

#### 新增 API 文件
```typescript
// frontend/src/api/agent.ts
export interface AgentStartResponse {
  runId: string
  status: string
}

export interface AgentStep {
  stepName: string
  status: string  // running | success | skipped | error
  durationMs: number
  inputSummary: string
  outputSummary: string
}

export interface AgentRun {
  runId: string
  status: string  // running | awaiting_approval | done | rejected | error
  currentStep: string
  steps: AgentStep[]
  error: string | null
}

export function startAgentApi(query: string, kbId: number, sessionId: string): Promise<AgentStartResponse>
export function getAgentStatusApi(runId: string): Promise<AgentRun>
export function approveAgentApi(runId: string, decision: 'approve' | 'reject'): Promise<any>
export function subscribeAgentEvents(runId: string, onEvent: (event: any) => void): () => void
```

#### 新增 Agent 视图组件
```
frontend/src/views/
  ChatView.vue          (现有 - 简单问答)
  AgentView.vue         (新增 - Agent 工作流)
```

#### AgentView.vue 功能
1. **输入区**
   - 问题输入框
   - 知识库选择
   - "启动 Agent" 按钮

2. **工作流状态展示**
   ```
   [✓] retrieve (检索)     - 命中 5 条
   [✓] summarize (摘要)    - 120ms
   [✓] classify (分类)     - AI/Engineering
   [⏳] report_gate (待确认) ← 人工确认点
   [ ] report (生成报告)
   ```

3. **人工确认 UI**
   - 显示待确认的摘要和分类
   - [批准] [拒绝] 按钮
   - 倒计时提示 (10分钟)

4. **报告展示**
   - 结构化报告 (Markdown)
   - 引用来源
   - 下载/复制功能

---

### 2. 路由配置

```typescript
// frontend/src/router/index.ts
{
  path: '/agent',
  name: 'Agent',
  component: () => import('@/views/AgentView.vue'),
  meta: { title: 'Agent 工作流' }
}
```

---

### 3. 顶部导航更新

```vue
<!-- frontend/src/components/Topbar.vue -->
<router-link to="/chat">智能问答</router-link>
<router-link to="/agent">Agent 工作流</router-link>  <!-- 新增 -->
```

---

## 实现建议

### 方案 A: 快速实现 (推荐)
1. 创建 `AgentView.vue`
2. 添加 `api/agent.ts`
3. 更新路由和导航
4. 预计: 2-3 小时

### 方案 B: 集成到 ChatView
1. 在 ChatView 添加 "Agent 模式" 切换
2. 复用现有 UI 元素
3. 预计: 4-5 小时

### 方案 C: 暂时不实现
1. 更新 README，移除 human-in-the-loop 描述
2. 标记为 "开发中"
3. 预计: 30 分钟

---

## 建议

**推荐方案 A**，理由：
1. Agent 工作流是独立功能，应该有独立视图
2. 快速实现可验证后端功能
3. 符合 "处女原则" - 不临时拼凑

是否执行方案 A？
