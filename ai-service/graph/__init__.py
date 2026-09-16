"""graph 包：LangGraph 文档分析工作流（P1-1 模块化拆分）。

模块职责：
  state.py     状态类型契约（AgentState / StepRecord）
  store.py     run 存储与事件队列（RunInfo / AgentRunStore / store 单例）
  nodes.py     六个节点实现（retrieve / summarize / classify / report_gate / report / direct_answer）
  workflow.py  图编排与对外 API（build_agent_graph / start_agent_run / approve_run）

向后兼容：graph/agent_graph.py 保留为再导出垫片（旧导入路径不破坏）。
HITL 选型说明与演进方向：见 graph/README.md 与 docs/interview-langgraph-hitl.md。
"""
