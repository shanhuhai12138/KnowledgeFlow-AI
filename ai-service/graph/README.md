# graph/ — LangGraph 文档分析工作流

> P1-1 模块化拆分：原 `agent_graph.py`（约 300 行单文件）按职责拆为四个模块。
> 拆分原则：**纯等价重构**——图结构、节点行为、对外 API 与拆分前完全一致（有快照对比验证）。

## 模块结构

```
graph/
├── __init__.py    包说明与模块职责
├── state.py       状态类型契约：AgentState（图状态）、StepRecord（步骤记录）
├── store.py       运行时存储：RunInfo（单 run 状态+事件队列）、AgentRunStore（线程安全字典）、store 单例
├── nodes.py       六个节点函数（LangGraph 约定：State -> 部分状态更新）
├── workflow.py    图编排：build_agent_graph() + 对外 API（start_agent_run / approve_run）
└── agent_graph.py 向后兼容垫片：从 workflow/store 再导出，旧导入路径不受影响
```

## 数据流

```
POST /ai/agent (routers/agent.py)
  └─> start_agent_run()          workflow.py：创建 RunInfo + 起后台线程
        └─> graph.invoke(state)  LangGraph 按下图推进，节点写步骤/事件进 store
              START → retrieve ─┬─ 有结果 → summarize → classify → report_gate → report_node → END
                                └─ 无结果 → direct_answer ──────────────────────────────────→ END
                                              （直接回答：不走摘要/分类/门控，避免无关内容进引用链）

GET  /ai/agent/status  → store.get(run_id)：步骤列表、当前节点、报告
GET  /ai/agent/events  → run.events 队列 SSE 流式推送（step/status/done）
POST /ai/agent/approve → approve_run()：置 approved，report_gate 轮询到后放行/拒绝
```

## 职责边界（拆分前后对照）

| 职责 | 拆分前（单文件） | 拆分后 |
|------|----------------|--------|
| 状态类型 | AgentState/StepRecord 混在文件头 | `state.py` |
| run 存储 + 事件 | RunInfo/AgentRunStore 混在文件中 | `store.py` |
| 节点行为 | 六个 _xxx 节点函数 | `nodes.py`（公开命名 retrieve_node 等） |
| 图编排 + API | build/start/approve | `workflow.py` |
| 步骤计时 | _StepTimer | `nodes.py` 内部（唯一使用方） |

## 设计取舍与演进方向（面试答辩要点）

1. **HITL 为什么是线程轮询而不是 LangGraph checkpointer/interrupt？**
   当前部署形态单进程单机，run 状态本就在内存；interrupt + checkpointer 的价值在持久化与多进程恢复。选型说明见 `docs/interview-langgraph-hitl.md`。演进路径：MemorySaver（进程内断点恢复）→ SqliteSaver（持久化）→ Redis（多副本）。
2. **RunInfo 为什么是内存字典？**
   单机演示的最小正确实现；重启丢 run 是已知边界（store.py 模块注释明示）。生产化第一步是 store 接口化 + Redis 实现，节点与编排层不需要改。
3. **无结果分支为什么仍调 LLM（direct_answer）？**
   语义是"知识库没有 → 换通用知识回答并声明无相关信息"，而不是拒绝服务。若要强防幻觉：对 direct_answer 的输出不挂引用卡片、前端明示"非知识库来源"。这与检索命中时的"基于检索内容 + 标注引用"是两条不同信任级别的链路。

## 等价性验证

拆分前图结构快照：6 业务节点（retrieve/summarize/classify/report_gate/report_node/direct_answer）+ 8 条边（含 retrieve 处条件路由）。
拆分后以 `dump_graph` 同法对比，节点与边完全一致；pytest 全量通过。
