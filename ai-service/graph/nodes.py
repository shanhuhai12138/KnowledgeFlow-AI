"""Agent 工作流节点实现（拆分自 agent_graph.py，P1-1）。

每个节点函数签名保持 LangGraph 约定：AgentState -> 部分状态更新。
耗时与步骤记录通过 store.add_step / _StepTimer 完成。
"""
from __future__ import annotations

import threading
import time
from typing import List

from qdrant_client import QdrantClient

from config import get_settings
from graph.state import AgentState, StepRecord
from rag.embedder import get_embedder
from rag.llm import sync_chat
from rag.prompts import build_context
from rag.retriever import ensure_collection, search


def _step(run_id: str, name: str) -> "_StepTimer":
    return _StepTimer(run_id, name)


def _trunc(text: str, n: int = 120) -> str:
    text = (text or "").replace("\n", " ")
    return text[:n] + ("…" if len(text) > n else "")


class _StepTimer:
    """节点耗时计时 + 步骤落库。"""

    def __init__(self, run_id: str, name: str):
        from graph.store import store  # 延迟导入避免循环依赖
        self.store = store
        self.run_id = run_id
        self.name = name
        self.start = time.perf_counter()
        self.store.add_step(run_id, {"stepName": name, "status": "running", "durationMs": 0,
                                     "inputSummary": "", "outputSummary": ""})

    def finish(self, input_summary: str, output_summary: str, status: str = "success"):
        ms = int((time.perf_counter() - self.start) * 1000)
        self.store.get(self.run_id).steps[-1].update(
            status=status, durationMs=ms, inputSummary=input_summary[:200], outputSummary=output_summary[:500])


# ==================== 节点 ====================


def retrieve_node(state: AgentState) -> AgentState:
    timer = _step(state["_run_id"], "retrieve")
    settings = get_settings()
    embedder = get_embedder()
    client = QdrantClient(url=settings.qdrant_url)
    ensure_collection(client, embedder.dim)
    vector = embedder.embed_query(state["query"])
    results = search(client, vector, str(state["kbId"]), settings.top_k, settings.threshold)
    timer.finish(f"query={state['query']}", f"命中 {len(results)} 条")
    return {"results": results, "step_name": "retrieve"}


def summarize_node(state: AgentState) -> AgentState:
    timer = _step(state["_run_id"], "summarize")
    from graph.store import store  # 延迟导入避免循环依赖
    llm = get_llm_client(state["_api_key"])
    content = build_context(state["results"])
    prompt = (f"请对以下知识库内容进行不超过 200 字的摘要，突出关键信息：\n\n{content}")
    summary = sync_chat(llm, [{"role": "user", "content": prompt}])
    store.get(state["_run_id"]).summary = summary
    timer.finish(f"输入 {len(content)} 字", summary)
    return {"summary": summary}


def classify_node(state: AgentState) -> AgentState:
    timer = _step(state["_run_id"], "classify")
    from graph.store import store  # 延迟导入避免循环依赖
    llm = get_llm_client(state["_api_key"])
    content = build_context(state["results"])
    prompt = (f"请对以下知识库内容进行主题分类，输出格式：主分类 / 子分类，并给出 1 句依据：\n\n{content}")
    classification = sync_chat(llm, [{"role": "user", "content": prompt}])
    store.get(state["_run_id"]).classification = classification
    timer.finish(f"输入 {len(content)} 字", classification)
    return {"classification": classification}


def report_gate_node(state: AgentState) -> AgentState:
    """human-in-the-loop：生成报告前暂停，等待人工 approve/reject（显式等待，Worker 线程阻塞）。"""
    from graph.store import store  # 延迟导入避免循环依赖
    run = store.get(state["_run_id"])
    store.set_status(run.run_id, "awaiting_approval")
    deadline = time.time() + 600  # 最多等 10 分钟
    while time.time() < deadline and run.approved is None:
        time.sleep(1)
    approved = run.approved == "approve"
    return {"approved": approved}


def report_node(state: AgentState) -> AgentState:
    timer = _step(state["_run_id"], "report")
    from graph.store import store  # 延迟导入避免循环依赖
    llm = get_llm_client(state["_api_key"])
    if not state.get("approved"):
        store.get(state["_run_id"]).status = "rejected"
        store.get(state["_run_id"]).report = "报告生成已取消（人工拒绝）"
        timer.finish("人工拒绝", "报告生成已取消（人工拒绝）", status="skipped")
        return {"report": "报告生成已取消（人工拒绝）"}

    # 如果是 not_found 路径（没有检索结果），直接返回
    if not state.get("results"):
        store.get(state["_run_id"]).report = state.get("report", "知识库中没有相关内容")
        timer.finish("直接回答", state.get("report", ""))
        return {"report": state.get("report", "")}

    # 正常路径：生成结构化报告
    prompt = (
        f"你是知识库问答助手。请基于以下检索内容，回答用户问题。\n\n"
        f"【用户问题】\n{state['query']}\n\n"
        f"【检索内容】\n{build_context(state['results'])}\n\n"
        f"请给出准确、简洁的回答，并标注引用来源。"
    )
    report = sync_chat(llm, [{"role": "user", "content": prompt}])
    store.get(state["_run_id"]).report = report
    timer.finish("问答生成", report)
    return {"report": report}


def direct_answer_node(state: AgentState) -> AgentState:
    """没有检索结果时，直接用通用知识回答。"""
    timer = _step(state["_run_id"], "direct_answer")
    llm = get_llm_client(state["_api_key"])
    prompt = (
        f"用户问题：{state['query']}\n\n"
        "知识库中没有找到相关内容。请基于你的通用知识，给出一个简洁的回答。"
        '如果问题确实无法回答，请说明"知识库中没有相关信息"。'
    )
    report = sync_chat(llm, [{"role": "user", "content": prompt}])
    from graph.store import store  # 延迟导入避免循环依赖
    store.get(state["_run_id"]).report = report
    timer.finish("通用知识回答", report)
    return {"report": report, "summary": "", "classification": ""}
