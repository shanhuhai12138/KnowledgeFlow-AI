"""BM25 检索器单元测试。"""
import pytest
from rag.bm25_retriever import BM25Retriever


class TestBM25Retriever:
    """BM25 检索器测试。"""
    
    @pytest.fixture
    def retriever(self):
        """创建测试检索器。"""
        documents = [
            {"id": "doc1", "content": "Python 3.11 环境配置指南", "metadata": {"filename": "python.md"}},
            {"id": "doc2", "content": "2026年8月21日版本更新说明", "metadata": {"filename": "version.md"}},
            {"id": "doc3", "content": "如何搭建开发环境", "metadata": {"filename": "setup.md"}},
        ]
        return BM25Retriever(documents)
    
    def test_search_exact_match(self, retriever):
        """测试精确匹配。"""
        results = retriever.search("2026年8月21日", top_k=2)
        assert len(results) > 0
        # 应优先匹配包含日期的文档
        assert results[0]["id"] == "doc2"
    
    def test_search_keyword_match(self, retriever):
        """测试关键词匹配。"""
        results = retriever.search("Python 3.11", top_k=2)
        assert len(results) > 0
        assert results[0]["id"] == "doc1"
    
    def test_search_empty_query(self, retriever):
        """测试空查询。"""
        results = retriever.search("", top_k=2)
        assert len(results) == 0
    
    def test_search_threshold(self, retriever):
        """测试阈值过滤。"""
        results = retriever.search("Python", top_k=2, threshold=10.0)
        assert len(results) == 0
