"""POST /ai/search — 智能检索 API（支持模式选择）."""
from __future__ import annotations

import time
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from config import get_settings
from rag.embedder import get_embedder
from rag.intent_classifier import classify_intent, recommend_mode
from rag.retriever import ensure_collection, search
from rag.bm25_retriever import BM25Retriever
from rag.hybrid_retriever import HybridRetriever
from qdrant_client import QdrantClient

router = APIRouter(tags=["search"])


class SearchRequest(BaseModel):
    query: str = Field(..., description="查询内容")
    # 兼容 Java 后端转发（Long）与直接调用（字符串）
    kbId: str | int = Field(..., description="知识库 ID")
    topK: Optional[int] = Field(default=None, description="返回条数（默认取配置）")
    threshold: Optional[float] = Field(default=None, description="相似度阈值 0-1")
    useHybrid: bool = Field(default=True, description="是否混合检索（预留）")
    mode: str = Field(default="auto", description="检索模式: auto/dense/bm25/hybrid")
    modeOverride: Optional[str] = Field(default=None, description="用户手动覆盖模式")


class SearchResult(BaseModel):
    documentId: str
    documentName: str
    page: int
    score: float
    content: str


class IntentInfo(BaseModel):
    intent: Optional[str] = None
    confidence: Optional[float] = None
    keywords: List[str] = []
    reason: Optional[str] = None
    recommendedMode: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    mode: str
    intent: Optional[IntentInfo] = None
    intentConfidence: Optional[float] = None
    tookMs: int
    results: List[SearchResult]


def _extract_documents_from_qdrant(client: QdrantClient, kb_id: str) -> List[dict]:
    """从 Qdrant 获取文档列表用于 BM25 检索。
    
    注意：这里简化处理，实际项目中可能需要缓存文档元数据。
    """
    return []


@router.post("/ai/search", response_model=SearchResponse)
def search_endpoint(req: SearchRequest):
    settings = get_settings()
    start = time.perf_counter()

    embedder = get_embedder()
    client = QdrantClient(url=settings.qdrant_url)
    ensure_collection(client, embedder.dim)

    top_k = req.topK or settings.top_k
    threshold = req.threshold if req.threshold is not None else settings.threshold

    # 确定使用的模式
    mode = req.modeOverride or req.mode
    
    # 意图识别（仅在 auto 模式下）
    intent_result = None
    if mode == "auto":
        intent_result = classify_intent(req.query)
        mode = recommend_mode(intent_result.intent)

    query_vector = embedder.embed_query(req.query)
    results = []
    
    if mode == "bm25":
        # BM25 关键词检索
        documents = _extract_documents_from_qdrant(client, str(req.kbId))
        if documents:
            bm25_retriever = BM25Retriever(documents)
            results = bm25_retriever.search(req.query, top_k=top_k, threshold=threshold)
            # 转换为标准格式
            results = [
                {
                    "documentId": r["id"],
                    "documentName": r.get("filename", ""),
                    "page": r.get("page", 0),
                    "score": round(float(r["score"]) * 100, 1),  # 归一化到 0-100
                    "content": r["content"],
                }
                for r in results
            ]
        # 否则 results 保持为空列表
    elif mode == "hybrid":
        # 混合检索（需要文档库）
        documents = _extract_documents_from_qdrant(client, str(req.kbId))
        if documents:
            bm25_retriever = BM25Retriever(documents)
            hybrid = HybridRetriever(client, bm25_retriever, rrf_k=60)
            results = hybrid.search(req.query, query_vector, top_k, threshold)
        # 否则降级为 Dense 检索
        if not results:
            results = search(client, query_vector, str(req.kbId), top_k, threshold)
    else:
        # Dense 向量检索（默认）
        results = search(client, query_vector, str(req.kbId), top_k, threshold)

    took_ms = int((time.perf_counter() - start) * 1000)
    
    return SearchResponse(
        query=req.query,
        mode=mode,
        intent=IntentInfo(
            intent=intent_result.intent.value if intent_result else None,
            confidence=intent_result.confidence if intent_result else None,
            keywords=intent_result.keywords if intent_result else [],
            reason=intent_result.reason if intent_result else None,
            recommendedMode=recommend_mode(intent_result.intent) if intent_result else None,
        ) if intent_result else None,
        intentConfidence=intent_result.confidence if intent_result else None,
        tookMs=took_ms,
        results=[SearchResult(**r) for r in results],
    )

