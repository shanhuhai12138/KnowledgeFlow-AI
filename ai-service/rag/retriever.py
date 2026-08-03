"""Qdrant 向量检索器 — 按 kbId 过滤 + Top-K + 阈值。

payload 契约（与任务书 §6 Qdrant 约定一致）：
  { documentId, kbId, chunkIndex, chunkId, page, filename, content }
"""
from __future__ import annotations

from typing import List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (Distance, FieldCondition, Filter, MatchValue,
                                  PointStruct, VectorParams)

from config import get_settings


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
