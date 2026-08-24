"""BM25 关键词检索器。

使用 rank-bm25 库实现 TF-IDF 风格的关键词检索。
适用于包含日期、版本、数值等精确信息的查询。
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None


class BM25Retriever:
    """BM25 关键词检索器。
    
    Attributes:
        documents: 文档列表，每个文档包含 id, content, metadata
        tokenized_docs: 分词后的文档列表
        bm25: BM25Okapi 实例
    """
    
    def __init__(self, documents: List[dict]) -> None:
        """初始化 BM25 检索器。
        
        Args:
            documents: 文档列表，格式: [{"id": str, "content": str, "metadata": dict}, ...]
        """
        if BM25Okapi is None:
            raise ImportError("请先安装 rank-bm25: pip install rank-bm25")
        
        # 空文档列表时直接返回
        if not documents:
            self.documents = []
            self.tokenized_docs = []
            self.bm25 = None
            return
        
        self.documents = documents
        self.tokenized_docs = [self._tokenize(doc["content"]) for doc in documents]
        self.bm25 = BM25Okapi(self.tokenized_docs)
    
    def _tokenize(self, text: str) -> List[str]:
        """中英文混合分词。
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 分词结果
        """
        tokens: List[str] = []
        
        # 提取中文词语（连续汉字）
        zh_words = re.findall(r'[\u4e00-\u9fff]{2,}', text)
        for word in zh_words:
            tokens.extend(list(word))  # 中文字符单独分词
        
        # 提取英文单词（3字符以上）
        en_words = re.findall(r'[a-zA-Z]{3,}', text)
        tokens.extend([w.lower() for w in en_words])
        
        # 提取数字（2位以上）
        numbers = re.findall(r'\d{2,}', text)
        tokens.extend(numbers)
        
        return tokens
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.0
    ) -> List[dict]:
        """执行 BM25 检索。
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            threshold: 最低分数阈值
            
        Returns:
            List[dict]: 检索结果，格式: [{"id": str, "score": float, "content": str, **metadata}, ...]
        """
        # 空文档库或无 BM25 实例时返回空结果
        if not self.bm25:
            return []
        
        query_tokens = self._tokenize(query)
        
        if not query_tokens:
            return []
        
        # 计算 BM25 分数
        scores = self.bm25.get_scores(query_tokens)
        
        # 获取 Top-K
        results: List[dict] = []
        for idx in scores.argsort()[::-1][:top_k]:
            score = float(scores[idx])
            if score >= threshold:
                doc = self.documents[idx]
                result: Dict = {
                    "id": doc["id"],
                    "score": score,
                    "content": doc["content"],
                }
                # 合并 metadata
                if "metadata" in doc:
                    result.update(doc["metadata"])
                results.append(result)
        
        return results
    
    def get_document_count(self) -> int:
        """获取文档数量。
        
        Returns:
            int: 文档数量
        """
        return len(self.documents)

    @property
    def is_empty(self) -> bool:
        """检查是否为空文档库。"""
        return self.bm25 is None
