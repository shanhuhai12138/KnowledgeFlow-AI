"""POST /ai/ingest — 文档分块向量化入库（T4.0 契约，documentId 幂等）。

请求：{ "documentId": "d1", "kbId": "kb1", "filename": "xx.pdf", "fileType": "pdf", "content": "全文文本" }
响应：{ "documentId": "d1", "chunkCount": 12, "vectorCount": 12 }
流程：删旧点（documentId）→ 中文感知分块 → embedding → upsert（payload 含 documentId/kbId/page）
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config import get_settings
from rag.chunker import RecursiveChineseSplitter
from rag.embedder import get_embedder
from rag.retriever import (delete_by_document, ensure_collection, invalidate_doc_cache, upsert_chunks)
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

router = APIRouter(tags=["ingest"])

# Qdrant 点 id：chunkId 哈希转 uint64（幂等稳定）
import hashlib


def _point_id(chunk_id: str) -> int:
    return int(hashlib.md5(chunk_id.encode("utf-8")).hexdigest()[:16], 16)


class IngestRequest(BaseModel):
    documentId: str = Field(..., description="文档 ID")
    # 兼容 Java 后端（字符串）与直接调用（数字）
    kbId: str | int = Field(..., description="知识库 ID")
    filename: str = Field(..., description="文件名")
    fileType: str = Field(default="txt", description="文件类型：pdf/docx/txt/md")
    content: str = Field(..., description="文档全文文本")


class IngestResponse(BaseModel):
    documentId: str
    chunkCount: int
    vectorCount: int


@router.delete("/ai/documents/{document_id}")
def delete_document(document_id: str):
    """删除文档全部向量（T2.3 Java 删除文档时调用，保证一致性）"""
    settings = get_settings()
    client = QdrantClient(url=settings.qdrant_url)
    try:
        delete_by_document(client, document_id)
        invalidate_doc_cache()  # 文档删除后立即失效 BM25 文档缓存
    except Exception as e:
        # collection 不存在等场景视为已清理
        raise HTTPException(status_code=404, detail=f"删除失败：{e}")
    return {"documentId": document_id, "deleted": True}


@router.post("/ai/ingest", response_model=IngestResponse)
def ingest(req: IngestRequest):
    settings = get_settings()
    if not req.content.strip():
        raise HTTPException(status_code=422, detail="content 不能为空")
    if len(req.content) > 10_000_000:  # 10MB 上限（契约 413）
        raise HTTPException(status_code=413, detail="content 过大（>10MB）")

    embedder = get_embedder()
    client = QdrantClient(url=settings.qdrant_url)
    ensure_collection(client, embedder.dim)

    # 1. 幂等：先删该 documentId 旧向量
    delete_by_document(client, req.documentId)

    # 2. 中文感知分块
    splitter = RecursiveChineseSplitter(settings.chunk_size, settings.chunk_overlap)
    chunks = splitter.split_text(req.content)
    if not chunks:
        raise HTTPException(status_code=422, detail="分块结果为空")

    # 3. embedding + upsert
    vectors = embedder.embed_texts([c.text for c in chunks])
    points = [
        PointStruct(
            id=_point_id(c.id),
            vector=vectors[i],
            payload={
                "documentId": req.documentId,
                "kbId": str(req.kbId),  # 统一字符串，保证检索 filter 匹配
                "chunkIndex": c.chunk_index,
                "chunkId": c.id,
                "page": 1,  # MVP：暂不解析页，固定 1
                "filename": req.filename,
                "content": c.text,
            },
        )
        for i, c in enumerate(chunks)
    ]
    upsert_chunks(client, points)
    invalidate_doc_cache(str(req.kbId))  # 新文档入库后立即失效该 KB 的 BM25 缓存

    return IngestResponse(documentId=req.documentId, chunkCount=len(chunks), vectorCount=len(points))
