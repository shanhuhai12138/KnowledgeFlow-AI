"""Agent 工作流状态类型定义（拆分自 agent_graph.py，P1-1）。

只放类型契约，不含任何行为——节点、存储、编排各归其位。
"""
from __future__ import annotations

from typing import List, TypedDict


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
