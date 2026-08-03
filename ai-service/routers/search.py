"""POST /ai/search — 语义检索（T4.0 契约）。

请求：{ "query": "...", "kbId": "kb1", "topK": 5, "threshold": 0.6, "useHybrid": true }
响应：{ "query": "...", "tookMs": 45, "results": [{documentId, documentName, page, score, content}] }
说明：useHybrid=false 仅 dense（当前实现）；true 预留混合检索（T4.5 落地 RRF 融合）。
"""
from __future__ import annotations

import time
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from config import get_settings
from rag.embedder import get_embedder
from rag.retriever import ensure_collection, search
from qdrant_client import QdrantClient

router = APIRouter(tags=["search"])


class SearchRequest(BaseModel):
    query: str = Field(..., description="查询内容")
    # 兼容 Java 后端转发（Long）与直接调用（字符串）
    kbId: str | int = Field(..., description="知识库 ID")
    topK: Optional[int] = Field(default=None, description="返回条数（默认取配置）")
    threshold: Optional[float] = Field(default=None, description="相似度阈值 0-1")
    useHybrid: bool = Field(default=True, description="是否混合检索（预留）")


class SearchResult(BaseModel):
    documentId: str
    documentName: str
    page: int
    score: float
    content: str


class SearchResponse(BaseModel):
    query: str
    tookMs: int
    results: List[SearchResult]


@router.post("/ai/search", response_model=SearchResponse)
def search_endpoint(req: SearchRequest):
    settings = get_settings()
    start = time.perf_counter()

    embedder = get_embedder()
    client = QdrantClient(url=settings.qdrant_url)
    ensure_collection(client, embedder.dim)

    top_k = req.topK or settings.top_k
    threshold = req.threshold if req.threshold is not None else settings.threshold

    query_vector = embedder.embed_query(req.query)
    results = search(client, query_vector, str(req.kbId), top_k, threshold)

    took_ms = int((time.perf_counter() - start) * 1000)
    return SearchResponse(query=req.query, tookMs=took_ms, results=results)
