"""Qdrant 向量检索器 — 按 kbId 过滤 + Top-K + 阈值。

payload 契约（与任务书 §6 Qdrant 约定一致）：
  { documentId, kbId, chunkIndex, chunkId, page, filename, content }
"""
from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple

from qdrant_client import QdrantClient
from qdrant_client.models import (Distance, FieldCondition, Filter, MatchValue,
                                  PointStruct, VectorParams)

from config import get_settings

# ---------------- 文档集提取（供 BM25 / Hybrid 使用） ----------------
# 进程内缓存：{kbId: (documents, fetched_at)}，TTL 内复用，避免每次检索全量 scroll
_DOC_CACHE: Dict[str, Tuple[List[dict], float]] = {}
_DOC_CACHE_TTL_SECONDS = 300.0  # 5 分钟；文档 ingest/删除后可调用 invalidate_doc_cache 立即刷新


def ensure_collection(client: QdrantClient, vector_size: int) -> None:
    """幂等创建集合（Cosine 距离）。"""
    settings = get_settings()
    if not client.collection_exists(settings.qdrant_collection):
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


def delete_by_document(client: QdrantClient, document_id: str) -> None:
    """幂等：删除该 documentId 的全部旧向量点。"""
    settings = get_settings()
    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=Filter(
            must=[FieldCondition(key="documentId", match=MatchValue(value=document_id))]
        ),
    )


def upsert_chunks(client: QdrantClient, points: List[PointStruct]) -> None:
    settings = get_settings()
    client.upsert(collection_name=settings.qdrant_collection, points=points)


def extract_documents_by_kb(client: QdrantClient, kb_id: str) -> List[dict]:
    """按 kbId 全量拉取向量点，构造 BM25 所需的文档集（带 TTL 缓存）。

    返回格式（与 BM25Retriever 契约一致）：
        [{ "id": documentId, "content": str,
           "metadata": { "filename": ..., "page": ..., "documentId": ... } }, ...]
    """
    settings = get_settings()
    now = time.monotonic()
    cached = _DOC_CACHE.get(kb_id)
    if cached and (now - cached[1]) < _DOC_CACHE_TTL_SECONDS:
        return cached[0]

    documents: List[dict] = []
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=settings.qdrant_collection,
            scroll_filter=Filter(must=[FieldCondition(key="kbId", match=MatchValue(value=kb_id))]),
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for p in points:
            payload = p.payload or {}
            content = payload.get("content", "")
            if not content:
                continue
            documents.append({
                "id": str(payload.get("documentId", p.id)),
                "content": content,
                # BM25 结果会 update(metadata)，字段平铺进 metadata 供上层读取
                "metadata": {
                    "filename": payload.get("filename", ""),
                    "page": payload.get("page", 0),
                    "documentId": payload.get("documentId"),
                },
            })
        if offset is None:
            break

    _DOC_CACHE[kb_id] = (documents, now)
    return documents


def invalidate_doc_cache(kb_id: Optional[str] = None) -> None:
    """文档 ingest / 删除后调用，立即失效缓存（不传则清空全部）。"""
    global _DOC_CACHE
    if kb_id is None:
        _DOC_CACHE.clear()
    else:
        _DOC_CACHE.pop(str(kb_id), None)


def search(
    client: QdrantClient,
    vector: List[float],
    kb_id: str,
    top_k: int,
    threshold: float,
) -> List[dict]:
    """按 kbId 过滤检索 Top-K，返回契约字段。"""
    settings = get_settings()
    hits = client.search(
        collection_name=settings.qdrant_collection,
        query_vector=vector,
        query_filter=Filter(must=[FieldCondition(key="kbId", match=MatchValue(value=kb_id))]),
        limit=top_k,
        score_threshold=threshold,
    )
    results = []
    for hit in hits:
        p = hit.payload or {}
        results.append({
            "documentId": p.get("documentId"),
            "documentName": p.get("filename", ""),
            "page": p.get("page", 0),
            "score": round(float(hit.score) * 100, 1),  # 契约 score 0-100
            "content": p.get("content", ""),
        })
    return results
