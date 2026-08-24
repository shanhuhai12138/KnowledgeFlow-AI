"""/ai/chat（同步）+ /ai/chat/stream（SSE 流式）— T4.0 契约，支持智能检索模式."""
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
from rag.intent_classifier import classify_intent, recommend_mode
from rag.llm import get_llm_client, resolve_api_key, stream_chat, sync_chat
from rag.prompts import build_messages
from rag.retriever import ensure_collection, search
from rag.bm25_retriever import BM25Retriever
from rag.hybrid_retriever import HybridRetriever
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
    mode: str = Field(default="auto", description="检索模式: auto/dense/bm25/hybrid")


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


def _extract_documents_from_qdrant(client: QdrantClient, kb_id: str) -> List[dict]:
    """从 Qdrant 获取文档列表用于 BM25 检索。"""
    return []


def _retrieve(kb_id: str, query: str, top_k: int, mode: str = "auto") -> tuple[List[dict], float]:
    """智能检索 + confidence（最高分加权映射 0-100）。"""
    settings = get_settings()
    embedder = get_embedder()
    client = QdrantClient(url=settings.qdrant_url)
    ensure_collection(client, embedder.dim)

    # 确定检索模式
    actual_mode = mode
    if mode == "auto":
        intent_result = classify_intent(query)
        actual_mode = recommend_mode(intent_result.intent)

    query_vector = embedder.embed_query(query)
    results = []

    if actual_mode == "bm25":
        documents = _extract_documents_from_qdrant(client, kb_id)
        if documents:
            bm25_retriever = BM25Retriever(documents)
            results = bm25_retriever.search(query, top_k=top_k, threshold=settings.threshold)
            results = [
                {
                    "documentId": r["id"],
                    "documentName": r.get("filename", ""),
                    "page": r.get("page", 0),
                    "score": round(float(r["score"]) * 100, 1),
                    "content": r["content"],
                }
                for r in results
            ]
        # 否则 results 保持为空列表
    elif actual_mode == "hybrid":
        documents = _extract_documents_from_qdrant(client, kb_id)
        if documents:
            bm25_retriever = BM25Retriever(documents)
            hybrid = HybridRetriever(client, bm25_retriever, rrf_k=60)
            results = hybrid.search(query, query_vector, top_k, settings.threshold)
        # 否则降级为 Dense 检索
        if not results:
            results = search(client, query_vector, kb_id, top_k, settings.threshold)
    else:
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

    results, confidence = _retrieve(str(req.kbId), req.message, settings.top_k, req.mode)
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
def chat_stream(sessionId: str, kbId: str | int, message: str, mode: str = "auto", request: Request = None):
    api_key = _resolve_key_or_400(request)
    settings = get_settings()

    results, confidence = _retrieve(str(kbId), message, settings.top_k, mode)
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
