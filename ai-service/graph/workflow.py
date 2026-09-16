"""Agent 工作流编排与对外 API（拆分自 agent_graph.py，P1-1）。

图结构：START → retrieve → summarize → classify → report_gate → report_node → END
条件分支：retrieve 结果为空 → direct_answer（跳过 summarize/classify/report_gate）
human-in-the-loop：report_gate 暂停等待人工 approve/reject（显式等待，Worker 线程阻塞）。

对外 API（供 routers/agent.py 使用）：
  start_agent_run(session_id, kb_id, query, api_key) -> RunInfo
  approve_run(run_id, decision, api_key) -> RunInfo
"""
from __future__ import annotations

import threading

from langgraph.graph import END, START, StateGraph

from graph.nodes import (classify_node, direct_answer_node, report_gate_node,
                         report_node, retrieve_node, summarize_node)
from graph.state import AgentState
from graph.store import store


def _route_after_retrieve(state: AgentState) -> str:
    if state.get("results"):
        return "summarize"
    # 没有检索结果，直接跳到最后一步（直接回答）
    return "direct_answer"


def build_agent_graph():
    g = StateGraph(AgentState)
    g.add_node("retrieve", retrieve_node)
    g.add_node("summarize", summarize_node)
    g.add_node("classify", classify_node)
    g.add_node("report_gate", report_gate_node)
    g.add_node("report_node", report_node)
    g.add_node("direct_answer", direct_answer_node)
    g.add_edge(START, "retrieve")
    g.add_conditional_edges("retrieve", _route_after_retrieve,
                            {"summarize": "summarize", "direct_answer": "direct_answer"})
    g.add_edge("summarize", "classify")
    g.add_edge("classify", "report_gate")
    g.add_edge("report_gate", "report_node")
    g.add_edge("report_node", END)
    g.add_edge("direct_answer", END)
    return g.compile()


def start_agent_run(session_id: str, kb_id: str, query: str, api_key: str):
    """启动工作流（后台线程执行，interrupt 处暂停）。返回 RunInfo。"""
    run = store.create(session_id, kb_id, query)
    graph = build_agent_graph()

    def worker():
        try:
            graph.invoke(
                {"query": query, "kbId": kb_id, "sessionId": session_id,
                 "_run_id": run.run_id, "_api_key": api_key},
            )
            if store.get(run.run_id).status in ("running", "awaiting_approval"):
                store.set_status(run.run_id, "done")
        except Exception as e:
            store.get(run.run_id).error = str(e)
            store.set_status(run.run_id, "error")

    threading.Thread(target=worker, daemon=True).start()
    return run


def approve_run(run_id: str, decision: str, api_key: str):
    """人工确认（approve/reject）：设置确认值，Worker 线程在 report_gate 继续执行。"""
    run = store.get(run_id)
    if run is None:
        raise ValueError("runId 不存在")
    run.approved = decision
    return run
