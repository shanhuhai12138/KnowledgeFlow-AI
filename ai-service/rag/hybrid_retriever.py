"""混合检索器：Dense + Sparse + RRF 融合。

结合向量检索和关键词检索的优势，使用 RRF (Reciprocal Rank Fusion) 算法融合结果。
"""
from __future__ import annotations

from typing import Dict, List, Optional

from rag.bm25_retriever import BM25Retriever


class HybridRetriever:
    """混合检索器，融合 Dense 和 BM25 检索结果。
    
    Attributes:
        dense: 向量检索器（支持 search 方法）
        sparse: BM25 检索器实例
        rrf_k: RRF 融合常数，默认 60
    """
    
    def __init__(
        self,
        dense_retriever,
        sparse_retriever: BM25Retriever,
        rrf_k: int = 60
    ) -> None:
        """初始化混合检索器。
        
        Args:
            dense_retriever: 向量检索器（支持 search 方法）
            sparse_retriever: BM25 检索器实例
            rrf_k: RRF 融合常数
        """
        self.dense = dense_retriever
        self.sparse = sparse_retriever
        self.rrf_k = rrf_k
    
    def search(
        self,
        query: str,
        vector: List[float],
        top_k: int = 5,
        threshold: float = 0.0
    ) -> List[dict]:
        """执行混合检索并融合结果。
        
        使用 RRF (Reciprocal Rank Fusion) 算法融合 Dense 和 BM25 结果：
        score(doc) = Σ 1/(k + rank(doc) + 1)
        
        Args:
            query: 查询文本
            vector: 查询向量
            top_k: 返回结果数量
            threshold: 最低相似度阈值
            
        Returns:
            List[dict]: 融合后的检索结果
        """
        # 双路检索（扩大检索范围以便融合）
        dense_results = self.dense.search(vector, top_k=top_k * 2, threshold=threshold)
        sparse_results = self.sparse.search(query, top_k=top_k * 2, threshold=threshold)
        
        # RRF 融合
        rrf_scores: Dict[str, float] = {}
        dense_scores: Dict[str, float] = {}
        sparse_scores: Dict[str, float] = {}
        
        # 处理 Dense 结果
        for i, hit in enumerate(dense_results):
            doc_id = hit["documentId"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (self.rrf_k + i + 1)
            dense_scores[doc_id] = hit["score"]
        
        # 处理 BM25 结果
        for i, hit in enumerate(sparse_results):
            doc_id = hit["id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1 / (self.rrf_k + i + 1)
            sparse_scores[doc_id] = hit["score"]
        
        # 去重并排序
        final_results: List[dict] = []
        seen_ids = set()
        
        for doc_id, rrf_score in sorted(rrf_scores.items(), key=lambda x: -x[1]):
            if doc_id in seen_ids:
                continue
            seen_ids.add(doc_id)
            
            # 获取原始分数（归一化到 0-100）
            dense_score = dense_scores.get(doc_id, 0)
            sparse_score = sparse_scores.get(doc_id, 0)
            
            # 找到对应的内容
            content = ""
            document_name = ""
            page = 0
            
            # 从 Dense 结果查找
            for r in dense_results:
                if r["documentId"] == doc_id:
                    content = r["content"]
                    document_name = r.get("documentName", "")
                    page = r.get("page", 0)
                    break
            
            # 如果没找到，从 BM25 结果查找
            if not content:
                for r in sparse_results:
                    if r["id"] == doc_id:
                        content = r["content"]
                        document_name = r.get("filename", "")
                        page = r.get("page", 0)
                        break
            
            final_results.append({
                "documentId": doc_id,
                "documentName": document_name,
                "page": page,
                "score": round(max(dense_score, sparse_score), 1),
                "content": content,
                "rrfScore": round(rrf_score, 4),
                "denseScore": round(dense_score, 4),
                "sparseScore": round(sparse_score, 4),
            })
            
            if len(final_results) >= top_k:
                break
        
        return final_results
