"""LangGraph Agent 工作流 — 「文档分析工作流」。

图结构：START → retrieve → summarize → classify → report(人工确认门) → END
条件分支：retrieve 结果为空 → not_found（跳过 summarize/classify/report）
human-in-the-loop：report 生成前 interrupt 暂停，等待人工 approve/reject（显式等待，Worker 线程阻塞）。

步骤记录（steps）与 SSE 事件：通过 AgentRunStore 共享（节点内写入步骤 + 事件队列）。
"""
from __future__ import annotations

import threading
import time
import uuid
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from rag.embedder import get_embedder
from rag.llm import get_llm_client, stream_chat, sync_chat
from rag.prompts import build_context
from rag.retriever import ensure_collection, search
from qdrant_client import QdrantClient

from config import get_settings


class AgentState(TypedDict, total=False):
    query: str
    kbId: str
    sessionId: str
    results: List[dict]
    summary: str
    classification: str
    report: str
    approved: bool
    step_name: str
    _run_id: str
    _api_key: str


class StepRecord(TypedDict):
    stepName: str
    status: str  # running / success / skipped / error
    durationMs: int
    inputSummary: str
    outputSummary: str


class RunInfo:
    """单个 run 的状态存储。"""

    def __init__(self, run_id: str, session_id: str, kb_id: str, query: str):
        self.run_id = run_id
        self.session_id = session_id
        self.kb_id = kb_id
        self.query = query
        self.status: str = "running"  # running / awaiting_approval / done / rejected / error
        self.steps: List[StepRecord] = []
        self.events: "queue.Queue[dict]" = __import__("queue").Queue()
        self.error: Optional[str] = None
        self.finished_at: Optional[str] = None
        # human-in-the-loop：approve/reject 确认值（None=待确认）
        self.approved: Optional[str] = None


class AgentRunStore:
    """内存 run 存储（单机演示；生产环境应替换为 Redis 持久化）。"""

    def __init__(self):
        self._runs: Dict[str, RunInfo] = {}
        self._lock = threading.Lock()

    def create(self, session_id: str, kb_id: str, query: str) -> RunInfo:
        run = RunInfo(uuid.uuid4().hex[:12], session_id, kb_id, query)
        with self._lock:
            self._runs[run.run_id] = run
        return run

    def get(self, run_id: str) -> Optional[RunInfo]:
        with self._lock:
            return self._runs.get(run_id)

    def add_step(self, run_id: str, step: StepRecord):
        run = self.get(run_id)
        if run:
            run.steps.append(step)
            run.events.put({"type": "step", "step": step})

    def set_status(self, run_id: str, status: str):
        run = self.get(run_id)
        if run:
            run.status = status
            run.events.put({"type": "status", "status": status})


store = AgentRunStore()


class _StepTimer:
    """节点耗时计时 + 步骤落库。"""

    def __init__(self, run_id: str, name: str):
        self.run_id = run_id
        self.name = name
        self.start = time.perf_counter()
        store.add_step(run_id, {"stepName": name, "status": "running", "durationMs": 0,
                                "inputSummary": "", "outputSummary": ""})

    def finish(self, input_summary: str, output_summary: str, status: str = "success"):
        ms = int((time.perf_counter() - self.start) * 1000)
        store.get(self.run_id).steps[-1].update(
            status=status, durationMs=ms, inputSummary=input_summary[:200], outputSummary=output_summary[:500])


def _step(run_id: str, name: str) -> _StepTimer:
    return _StepTimer(run_id, name)


def _trunc(text: str, n: int = 120) -> str:
    text = (text or "").replace("\n", " ")
    return text[:n] + ("…" if len(text) > n else "")


# ==================== 节点 ====================


def _retrieve(state: AgentState) -> AgentState:
    timer = _step(state["_run_id"], "retrieve")
    settings = get_settings()
    embedder = get_embedder()
    client = QdrantClient(url=settings.qdrant_url)
    ensure_collection(client, embedder.dim)
    vector = embedder.embed_query(state["query"])
    results = search(client, vector, str(state["kbId"]), settings.top_k, settings.threshold)
    timer.finish(f"query={state['query']}", f"命中 {len(results)} 条")
    return {"results": results, "step_name": "retrieve"}


def _summarize(state: AgentState) -> AgentState:
    timer = _step(state["_run_id"], "summarize")
    llm = get_llm_client(state["_api_key"])
    content = build_context(state["results"])
    prompt = (f"请对以下知识库内容进行不超过 200 字的摘要，突出关键信息：\n\n{content}")
    summary = sync_chat(llm, [{"role": "user", "content": prompt}])
    timer.finish(f"输入 {len(content)} 字", summary)
    return {"summary": summary}


def _classify(state: AgentState) -> AgentState:
    timer = _step(state["_run_id"], "classify")
    llm = get_llm_client(state["_api_key"])
    content = build_context(state["results"])
    prompt = (f"请对以下知识库内容进行主题分类，输出格式：主分类 / 子分类，并给出 1 句依据：\n\n{content}")
    classification = sync_chat(llm, [{"role": "user", "content": prompt}])
    timer.finish(f"输入 {len(content)} 字", classification)
    return {"classification": classification}


def _report_gate(state: AgentState) -> AgentState:
    """human-in-the-loop：生成报告前暂停，等待人工 approve/reject（显式等待，Worker 线程阻塞）。"""
    run = store.get(state["_run_id"])
    store.set_status(run.run_id, "awaiting_approval")
    deadline = time.time() + 600  # 最多等 10 分钟
    while time.time() < deadline and run.approved is None:
        time.sleep(1)
    approved = run.approved == "approve"
    return {"approved": approved}


def _report(state: AgentState) -> AgentState:
    timer = _step(state["_run_id"], "report")
    llm = get_llm_client(state["_api_key"])
    if not state.get("approved"):
        store.set_status(state["_run_id"], "rejected")
        timer.finish("人工拒绝", "报告生成已取消（人工拒绝）", status="skipped")
        return {"report": "报告生成已取消（人工拒绝）"}
    prompt = (
        "你是文档分析报告生成器。请基于以下检索内容、摘要与分类，生成结构化分析报告"
        "（包含：分析结论、关键要点、引用来源）。\n\n"
        f"【检索内容】\n{build_context(state['results'])}\n\n"
        f"【摘要】\n{state.get('summary', '')}\n\n"
        f"【分类】\n{state.get('classification', '')}"
    )
    report = sync_chat(llm, [{"role": "user", "content": prompt}])
    timer.finish("摘要+分类+检索内容", report)
    return {"report": report}


def _not_found(state: AgentState) -> AgentState:
    timer = _step(state["_run_id"], "not_found")
    timer.finish("检索结果为空", "未找到相关内容")
    return {"report": "未找到相关内容", "summary": "", "classification": ""}


# ==================== 图 ====================


def _route_after_retrieve(state: AgentState) -> str:
    return "summarize" if state.get("results") else "not_found"


def build_agent_graph():
    g = StateGraph(AgentState)
    g.add_node("retrieve", _retrieve)
    g.add_node("summarize", _summarize)
    g.add_node("classify", _classify)
    g.add_node("report_gate", _report_gate)
    g.add_node("report_node", _report)
    g.add_node("not_found", _not_found)
    g.add_edge(START, "retrieve")
    g.add_conditional_edges("retrieve", _route_after_retrieve,
                            {"summarize": "summarize", "not_found": "not_found"})
    g.add_edge("summarize", "classify")
    g.add_edge("classify", "report_gate")
    g.add_edge("report_gate", "report_node")
    g.add_edge("report_node", END)
    g.add_edge("not_found", END)
    return g.compile()


# ==================== 对外 API（供 routers/agent.py 使用） ====================


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
