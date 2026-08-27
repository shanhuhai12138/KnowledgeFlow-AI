# LangGraph Agent 人工确认节点：实现选型与演进路线（面试准备）

## 现状实现（诚实描述）

`graph/agent_graph.py` 的 human-in-the-loop 采用 **Worker 线程阻塞等待 + 内存状态存储**：

1. `start_agent_run()` 启动后台 Worker 线程执行 `graph.invoke()`
2. 到达 `report_gate` 节点时置状态 `awaiting_approval`
3. 节点内 `while time.time() < deadline and run.approved is None: sleep(1)` 轮询（上限 600s）
4. API 层 `approve_run()` 被调用时设置确认值，Worker 恢复执行
5. 运行状态存 `AgentRunStore`（进程内存 Dict + threading.Lock），SSE 推送步骤事件

## 为什么当初这么写（合理动机）

- 需求只是"人工确认后再生成报告"，轮询方案 20 行代码就能跑通，复杂度匹配 MVP 阶段
- LangGraph 原生 interrupt 依赖 checkpointer 持久化（MemorySaver/SqliteSaver/Redis），
  当时优先保证功能闭环快速可见
- 单机演示场景下，内存存储 + 线程阻塞没有正确性问题

## 已知局限（主动承认）

| 局限 | 影响 | 对应演进 |
|---|---|---|
| 状态在内存 | 进程重启丢运行态；多副本部署无法共享状态 | RunStore 接 Redis（项目已有 Redis），按 runId 序列化 |
| while-sleep 轮询 | 每秒空转一次；600s 超时后静默拒绝 | 用 `threading.Event`/`Condition` 替代 sleep 轮询，唤醒零延迟 |
| 非官方 interrupt() | 与 LangGraph 生态（checkpoint/time-travel/debug 工具）不兼容 | 改用 `interrupt_before=['report_node']` + checkpointer，approve 后 `invoke(None, config)` 续跑 |
| 超时即拒绝 | 用户无感知超时原因 | 超时事件也推 SSE，前端倒计时 |

## 官方 interrupt() 方案长什么样（证明理解深度）

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer, interrupt_before=["report_node"])

config = {"configurable": {"thread_id": run_id}}
graph.invoke(state, config)                      # 跑到 report_node 前暂停
state = graph.get_state(config)                  # 检查暂停点
if state.next == ("report_node",):
    graph.invoke(None, config, update_state?)    # approve 后传入 None 续跑
```

关键点：interrupt 由 checkpointer 承载状态快照，续跑不需要进程常驻 ——
这就是与线程阻塞方案的本质区别：**从「活等」变成「状态机停驻」**。

## 面试话术（30 秒版）

> "Agent 的人工确认我最早用 Worker 线程加条件等待实现的，二十行代码解决了
> MVP 需求；但我清楚它的局限——状态在内存、重启就丢、也没法多副本。标准做
> 法应该是 LangGraph 的 interrupt 加 checkpointer，把『线程活等』变成『状态
> 机停驻』，续跑时 invoke None 就行。这个重构在我的改进计划里，主要是在衡量
> 引入 checkpoint 存储的成本。"
