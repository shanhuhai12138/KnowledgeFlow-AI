"""意图识别模块单元测试。"""
import pytest
from rag.intent_classifier import classify_intent, recommend_mode, QueryIntent


class TestClassifyIntent:
    """意图分类测试。"""
    
    def test_keyword_intent_date(self):
        """测试日期查询识别。"""
        result = classify_intent("2026年8月21日的版本号")
        # 包含中文日期模式，应该是关键词意图
        assert result.intent == QueryIntent.KEYWORD
        assert result.confidence > 0.6
    
    def test_keyword_intent_version(self):
        """测试版本号查询识别。"""
        result = classify_intent("v1.0版本更新日志")
        assert result.intent == QueryIntent.KEYWORD

    def test_keyword_intent_long_number(self):
        """测试长数字查询识别。"""
        result = classify_intent("订单号123456789的处理状态")
        assert result.intent == QueryIntent.KEYWORD
    
    def test_semantic_intent_how(self):
        """测试如何查询识别。"""
        result = classify_intent("如何搭建开发环境")
        assert result.intent == QueryIntent.SEMANTIC
    
    def test_analytical_intent(self):
        """测试分析型查询识别。"""
        result = classify_intent("分析本月销售数据，生成报告")
        assert result.intent == QueryIntent.ANALYTICAL
    
    def test_empty_query(self):
        """测试空查询。"""
        result = classify_intent("")
        assert result.intent == QueryIntent.SEMANTIC
        assert result.confidence == 0.5
    
    def test_keywords_extraction(self):
        """测试关键词提取。"""
        result = classify_intent("2026年8月21日的版本号v1.0")
        assert "2026" in result.keywords
        assert "21" in result.keywords


class TestRecommendMode:
    """检索模式推荐测试。"""
    
    def test_keyword_recommends_bm25(self):
        """关键词查询推荐 BM25。"""
        assert recommend_mode(QueryIntent.KEYWORD) == "bm25"
    
    def test_semantic_recommends_dense(self):
        """语义查询推荐 Dense。"""
        assert recommend_mode(QueryIntent.SEMANTIC) == "dense"
    
    def test_mixed_recommends_hybrid(self):
        """混合查询推荐 Hybrid。"""
        assert recommend_mode(QueryIntent.MIXED) == "hybrid"
    
    def test_analytical_recommends_hybrid(self):
        """分析查询推荐 Hybrid。"""
        assert recommend_mode(QueryIntent.ANALYTICAL) == "hybrid"
