"""查询意图识别模块。

使用正则表达式快速分类查询意图，支持可选 LLM 辅助判断。
"""
from __future__ import annotations

import re
from enum import Enum
from typing import List, Optional


class QueryIntent(str, Enum):
    """查询意图类型。"""
    KEYWORD = "keyword"      # 数值/日期/版本/精确术语
    SEMANTIC = "semantic"    # 自然语言/语义查询
    MIXED = "mixed"          # 混合型
    ANALYTICAL = "analytical" # 分析型任务


class IntentResult:
    """意图识别结果。"""
    def __init__(
        self,
        intent: QueryIntent,
        confidence: float,
        keywords: List[str],
        reason: str
    ):
        self.intent = intent
        self.confidence = confidence
        self.keywords = keywords
        self.reason = reason
    
    def to_dict(self) -> dict:
        """序列化为字典。"""
        return {
            "intent": self.intent.value,
            "confidence": round(self.confidence, 2),
            "keywords": self.keywords,
            "reason": self.reason,
        }


# 正则模式定义
_PATTERNS: dict[QueryIntent, list[str]] = {
    QueryIntent.KEYWORD: [
        r'\d{4}[.\-]\d{1,2}[.\-]\d{1,2}',      # 日期 2026-08-21
        r'\d{4}年\d{1,2}月\d{1,2}日',           # 中文日期 2026年8月21日
        r'v\d+\.\d+',                           # 版本号 v1.0
        r'版本[vV]?\d+',                        # 版本号 v1.0
        r'\d+年第\d+季度',                      # 第三季度
        r'\d+[万千万亿]+',                      # 100万
        r'\d{6,}',                               # 长数字
        r'[A-Z]{2,}\d+',                        # 术语+数字 BGE-M3
    ],
    QueryIntent.SEMANTIC: [
        r'如何.{2,}',                            # 如何搭建
        r'为什么.{2,}',                           # 为什么慢
        r'什么.{2,}',                             # 什么是
        r'介绍.{2,}',                            # 介绍下
        r'.{2,}情况.{0,}',                       # 销售情况
    ],
    QueryIntent.ANALYTICAL: [
        r'.{2,}分析.{2,}',                       # 分析数据
        r'.{2,}生成.{2,}',                       # 生成报告
        r'.{2,}总结.{2,}',                       # 总结成果
        r'.{2,}报告.{2,}',                       # 写个报告
    ],
}


def classify_intent(query: str, use_llm: bool = False) -> IntentResult:
    """基于正则表达式快速分类查询意图。
    
    Args:
        query: 用户查询文本
        use_llm: 是否启用 LLM 辅助判断（默认 False）
        
    Returns:
        IntentResult: 意图识别结果
    """
    if not query or not query.strip():
        return IntentResult(
            intent=QueryIntent.SEMANTIC,
            confidence=0.5,
            keywords=[],
            reason="空查询，使用默认语义检索"
        )
    
    # 统计各模式匹配数
    scores: dict[QueryIntent, int] = {intent: 0 for intent in QueryIntent}
    
    # 正则匹配
    for intent, patterns in _PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, query):
                scores[intent] += 1
    
    # 提取关键词
    keywords = _extract_keywords(query)
    
    # 判断意图
    max_score = max(scores.values())
    
    if max_score == 0:
        # 无明确模式
        intent = QueryIntent.SEMANTIC
        confidence = 0.5
        reason = "未检测到特定模式，使用语义检索"
    elif scores[QueryIntent.ANALYTICAL] >= 1 and max_score == scores[QueryIntent.ANALYTICAL]:
        intent = QueryIntent.ANALYTICAL
        confidence = min(0.95, 0.6 + scores[QueryIntent.ANALYTICAL] * 0.1)
        reason = "检测到分析型查询模式"
    elif scores[QueryIntent.KEYWORD] >= scores[QueryIntent.SEMANTIC]:
        intent = QueryIntent.KEYWORD
        confidence = min(0.95, 0.6 + scores[QueryIntent.KEYWORD] * 0.1)
        reason = "检测到关键词/数值查询模式"
    else:
        intent = QueryIntent.SEMANTIC
        confidence = min(0.95, 0.6 + scores[QueryIntent.SEMANTIC] * 0.1)
        reason = "检测到自然语言查询模式"
    
    return IntentResult(
        intent=intent,
        confidence=confidence,
        keywords=keywords,
        reason=reason
    )


def recommend_mode(intent: QueryIntent) -> str:
    """根据意图推荐检索模式。
    
    Args:
        intent: 查询意图
        
    Returns:
        str: 推荐模式 (dense/bm25/hybrid)
    """
    mapping: dict[QueryIntent, str] = {
        QueryIntent.KEYWORD: "bm25",
        QueryIntent.SEMANTIC: "dense",
        QueryIntent.MIXED: "hybrid",
        QueryIntent.ANALYTICAL: "hybrid",
    }
    return mapping.get(intent, "dense")


def _extract_keywords(query: str) -> List[str]:
    """从查询中提取关键词。
    
    Args:
        query: 查询文本
        
    Returns:
        List[str]: 关键词列表
    """
    keywords: List[str] = []
    
    # 提取中文词语（连续汉字，至少2个）
    zh_words = re.findall(r'[\u4e00-\u9fff]{2,}', query)
    keywords.extend(zh_words)
    
    # 提取英文单词（3字符以上）
    en_words = re.findall(r'[a-zA-Z]{3,}', query)
    keywords.extend(en_words)
    
    # 提取数字（2位以上）
    numbers = re.findall(r'\d{2,}', query)
    keywords.extend(numbers)
    
    # 去重并保持顺序
    seen = set()
    unique_keywords = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique_keywords.append(kw)
    
    return unique_keywords[:10]  # 最多10个关键词
