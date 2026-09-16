"""graph 包向后兼容垫片（P1-1 模块化拆分后保留旧导入路径）。

实现已按职责拆分：
  状态契约  -> graph/state.py（AgentState / StepRecord）
  run 存储  -> graph/store.py（RunInfo / AgentRunStore / store）
  节点实现  -> graph/nodes.py（retrieve_node / summarize_node / classify_node /
                            report_gate_node / report_node / direct_answer_node）
  编排与API -> graph/workflow.py（build_agent_graph / start_agent_run / approve_run）

新代码请直接从上述模块导入；本文件仅为 routers 等既有调用方保留。
结构说明与设计取舍见 graph/README.md。
"""
from graph.state import AgentState, StepRecord  # noqa: F401
from graph.store import AgentRunStore, RunInfo, store  # noqa: F401
from graph.workflow import (approve_run, build_agent_graph,  # noqa: F401
                            start_agent_run)

__all__ = [
    "AgentState", "StepRecord",
    "AgentRunStore", "RunInfo", "store",
    "build_agent_graph", "start_agent_run", "approve_run",
]
