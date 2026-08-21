"""/ai/agent 系列接口 — LangGraph 文档分析工作流（T4.4）。

  POST /ai/agent          启动工作流 {query, kbId, sessionId} → {runId, status}
  GET  /ai/agent/status   查询进度与当前步骤 ?runId=
  POST /ai/agent/approve  人工确认 ?runId=&decision=approve|reject
  GET  /ai/agent/events   SSE 步骤流式推送 ?runId=

Key 解析顺序沿用：请求头 X-API-Key → 环境变量 LLM_API_KEY → 明确报错。
"""
from __future__ import annotations

import queue as _queue
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from graph.agent_graph import (approve_run, build_agent_graph, start_agent_run,
                               store)
from rag.llm import resolve_api_key

router = APIRouter(tags=["agent"])


class AgentRequest(BaseModel):
    query: str = Field(..., description="分析问题")
    kbId: str | int = Field(..., description="知识库 ID")
    sessionId: str = Field(default="default", description="会话编号")


class AgentStartResponse(BaseModel):
    runId: str
    status: str


def _key_or_400(request: Request) -> str:
    try:
        return resolve_api_key(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/ai/agent", response_model=AgentStartResponse)
def start_agent(req: AgentRequest, request: Request):
    api_key = _key_or_400(request)
    run = start_agent_run(req.sessionId, str(req.kbId), req.query, api_key)
    return AgentStartResponse(runId=run.run_id, status=run.status)


@router.get("/ai/agent/status")
def agent_status(runId: str):
    run = store.get(runId)
    if run is None:
        raise HTTPException(status_code=404, detail="runId 不存在")
    current_step = None
    for s in reversed(run.steps):
        if s["status"] == "running":
            current_step = s["stepName"]
            break
    return {
        "runId": run.run_id,
        "status": run.status,
        "currentStep": current_step,
        "steps": run.steps,
        "error": run.error,
        "report": getattr(run, 'report', None),
        "summary": getattr(run, 'summary', None),
        "classification": getattr(run, 'classification', None),
    }


@router.post("/ai/agent/approve")
def agent_approve(runId: str, request: Request, decision: str = "approve"):
    if decision not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="decision 必须为 approve 或 reject")
    api_key = _key_or_400(request)
    try:
        run = approve_run(runId, decision, api_key)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"runId": run.run_id, "status": run.status, "approved": decision == "approve"}


@router.get("/ai/agent/events")
def agent_events(runId: str):
    run = store.get(runId)
    if run is None:
        raise HTTPException(status_code=404, detail="runId 不存在")

    def gen():
        # 先推送已有步骤
        for step in run.steps:
            yield _sse("step", step)
        # 再实时推送后续事件（最多 120s）
        deadline = time.time() + 120
        while time.time() < deadline:
            try:
                event = run.events.get(timeout=2)
                yield _sse(event["type"], event)
            except _queue.Empty:
                if run.status in ("done", "rejected", "error"):
                    break
                continue
            if run.status in ("done", "rejected", "error") and run.events.empty():
                break
        yield _sse("done", {"runId": run.run_id, "status": run.status, "report": getattr(run, 'report', None)})

    return StreamingResponse(gen(), media_type="text/event-stream")


def _sse(event: str, data) -> str:
    import json
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
