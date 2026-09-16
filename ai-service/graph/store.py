"""Agent run 状态存储（拆分自 agent_graph.py，P1-1）。

内存 run 存储（单机演示；生产环境应替换为 Redis 持久化）。
已知边界：进程重启后 run 丢失；无 TTL 清理——演进方向见 graph/README.md。
"""
from __future__ import annotations

import queue
import threading
import uuid
from typing import Dict, Optional

from graph.state import StepRecord


class RunInfo:
    """单个 run 的状态存储。"""

    def __init__(self, run_id: str, session_id: str, kb_id: str, query: str):
        self.run_id = run_id
        self.session_id = session_id
        self.kb_id = kb_id
        self.query = query
        self.status: str = "running"  # running / awaiting_approval / done / rejected / error
        self.steps: list[StepRecord] = []
        self.events: "queue.Queue[dict]" = queue.Queue()
        self.error: Optional[str] = None
        self.finished_at: Optional[str] = None
        # human-in-the-loop：approve/reject 确认值（None=待确认）
        self.approved: Optional[str] = None
        # 报告内容
        self.report: Optional[str] = None
        # 摘要和分类
        self.summary: Optional[str] = None
        self.classification: Optional[str] = None


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


# 模块级单例：routers 与节点共享同一 run 存储
store = AgentRunStore()
