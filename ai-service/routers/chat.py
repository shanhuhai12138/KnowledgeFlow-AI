"""/ai/chat（同步）+ /ai/chat/stream（SSE 流式）— T4.0 契约。

流程：检索（kbId 过滤）→ 组装上下文（文档名/页码）→ 提示词模板 → LLM 流式/同步；
sources 取自检索结果，confidence = 检索分加权（最高分/100 映射 0-100）。
"""
from __future__ import annotations

import json
import time
import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from config import get_settings
from rag.embedder import get_embedder
from rag.llm import get_llm_client, resolve_api_key, stream_chat, sync_chat
from rag.prompts import build_messages
from rag.retriever import ensure_collection, search
from qdrant_client import QdrantClient

router = APIRouter(tags=["chat"])


class ChatHistoryItem(BaseModel):
    role: str = Field(..., description="user / assistant")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    sessionId: str = Field(default="s1", description="会话编号")
    kbId: str | int = Field(..., description="知识库 ID（兼容 Java 转发数字）")
    message: str = Field(..., description="用户消息")
    history: Optional[List[ChatHistoryItem]] = Field(default=None, description="多轮历史")


class SourceItem(BaseModel):
    documentId: str
    documentName: str
    page: int
    score: float


class ChatResponse(BaseModel):
    id: str
    role: str = "assistant"
    content: str
    sources: List[SourceItem]
    confidence: int
    rating: None = None
    createdAt: str


def _retrieve(kb_id: str, query: str, top_k: int) -> tuple[List[dict], float]:
    """检索 + confidence（最高分加权映射 0-100）。"""
    settings = get_settings()
    embedder = get_embedder()
    client = QdrantClient(url=settings.qdrant_url)
    ensure_collection(client, embedder.dim)
    query_vector = embedder.embed_query(query)
    results = search(client, query_vector, kb_id, top_k, settings.threshold)
    if not results:
        return [], 0
    max_score = max(r["score"] for r in results)
    confidence = int(max(0, min(100, max_score)))
    return results, confidence


def _sources(results: list[dict]) -> list[dict]:
    return [
        {"documentId": r["documentId"], "documentName": r["documentName"],
         "page": r["page"], "score": r["score"]}
        for r in results
    ]


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _resolve_key_or_400(request: Request) -> str:
    try:
        return resolve_api_key(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== POST /ai/chat（同步） ====================


@router.post("/ai/chat", response_model=ChatResponse)
def chat(req: ChatRequest, request: Request):
    api_key = _resolve_key_or_400(request)
    settings = get_settings()

    results, confidence = _retrieve(str(req.kbId), req.message, settings.top_k)
    messages = build_messages(req.message,
                              [h.model_dump() for h in (req.history or [])], results)

    client = get_llm_client(api_key)
    try:
        content = sync_chat(client, messages)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM 调用失败：{e}")

    return ChatResponse(
        id=uuid.uuid4().hex[:12],
        content=content,
        sources=_sources(results),
        confidence=confidence,
        createdAt=time.strftime("%Y-%m-%dT%H:%M:%S"),
    )


# ==================== GET /ai/chat/stream（SSE） ====================


@router.get("/ai/chat/stream")
def chat_stream(sessionId: str, kbId: str | int, message: str, request: Request):
    api_key = _resolve_key_or_400(request)
    settings = get_settings()

    results, confidence = _retrieve(str(kbId), message, settings.top_k)
    messages = build_messages(message, None, results)

    def gen():
        # 1. meta
        yield _sse("meta", {"type": "meta", "sessionId": sessionId, "message": message})
        # 2. content × n（流式）
        client = get_llm_client(api_key)
        message_id = uuid.uuid4().hex[:12]
        try:
            for delta in stream_chat(client, messages):
                if delta:
                    yield _sse("content", {"type": "content", "delta": delta})
        except Exception as e:
            yield _sse("error", {"type": "error", "message": f"LLM 调用失败：{e}"})
            return
        # 3. sources + confidence
        yield _sse("sources", {"type": "sources", "sources": _sources(results), "confidence": confidence})
        # 4. done
        yield _sse("done", {"type": "done", "messageId": message_id})

    return StreamingResponse(gen(), media_type="text/event-stream")
