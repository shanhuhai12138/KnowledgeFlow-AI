# 智能检索系统实现 - 完整编码提示词

## 🎯 项目概述

**任务**：为 KnowledgeFlow-AI 项目实现智能检索算法推荐系统

**决策确认**：
1. ✅ BM25 实现：使用 `rank-bm25` 库
2. ✅ 意图识别：正则表达式优先 + LLM 可选兜底
3. ✅ 前端样式：完全匹配现有 UI 设计令牌
4. ✅ 测试数据：使用现有种子数据

---

## 👥 多 Agent 协作架构

```
┌─────────────────────────────────────────────────────────────┐
│                    主协调 Agent                              │
│         (负责任务分解、进度跟踪、代码审查)                      │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│  Backend Agent │ │ Frontend Agent │ │  Test Agent   │
│  (Python/RAG)  │ │  (Vue/TS)     │ │ (单元测试)     │
└───────────────┘ └───────────────┘ └───────────────┘
```

**协作流程**：
1. 主协调 Agent 分解任务
2. Backend Agent 实现后端逻辑
3. Frontend Agent 实现前端 UI
4. Test Agent 编写和运行测试
5. 主协调 Agent 集成和验证

---

## 📋 任务分解

### Phase 1: 后端实现（Backend Agent）

#### 1.1 安装依赖

**文件**: `ai-service/requirements.txt`

```txt
# 智能检索依赖（新增）
rank-bm25==0.2.2
```

**执行命令**:
```bash
cd D:\The World\KnowledgeFlow-AI\ai-service
pip install rank-bm25==0.2.2
```

---

#### 1.2 创建意图识别模块

**新建文件**: `ai-service/rag/intent_classifier.py`

**完整代码**:

```python
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
        r'\d{4}[.\/\-]\d{1,2}[.\/\-]\d{1,2}',  # 日期 2026.08.21
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
    
    # 提取中文词语（连续汉字）
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
```

---

#### 1.3 创建 BM25 检索器

**新建文件**: `ai-service/rag/bm25_retriever.py`

**完整代码**:

```python
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
```

---

#### 1.4 创建混合检索器

**新建文件**: `ai-service/rag/hybrid_retriever.py`

**完整代码**:

```python
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
```

---

#### 1.5 修改 Search API

**修改文件**: `ai-service/routers/search.py`

**改动说明**：
1. 导入新增模块
2. 新增 `mode` 和 `mode_override` 参数
3. 根据 mode 选择检索策略
4. 返回意图识别结果

**关键代码片段**:

```python
# 新增导入
from rag.intent_classifier import classify_intent, recommend_mode, QueryIntent
from rag.bm25_retriever import BM25Retriever
from rag.hybrid_retriever import HybridRetriever

# 新增响应字段
class SearchResponse(BaseModel):
    query: str
    mode: str
    intent: Optional[dict] = None  # 意图识别结果
    intentConfidence: Optional[float] = None
    tookMs: int
    results: List[SearchResult]

# 检索逻辑
mode = req.mode_override or req.mode

if mode == "auto":
    intent_result = classify_intent(req.query)
    recommended_mode = recommend_mode(intent_result.intent)
    intent_info = intent_result.to_dict()
    # 使用推荐模式检索
elif mode == "bm25":
    # BM25 检索
    bm25_retriever = BM25Retriever(documents)
    results = bm25_retriever.search(req.query, top_k, threshold)
elif mode == "hybrid":
    # 混合检索
    hybrid = HybridRetriever(client, bm25_retriever, rrf_k=60)
    results = hybrid.search(req.query, query_vector, top_k, threshold)
else:
    # Dense 检索（默认）
    results = search(client, query_vector, str(req.kbId), top_k, threshold)
```

---

#### 1.6 修改 Chat API

**修改文件**: `ai-service/routers/chat.py`

**改动说明**：
1. `ChatRequest` 新增 `mode` 参数
2. `_retrieve` 函数支持 mode 参数
3. 调用检索时使用指定模式

---

### Phase 2: 前端实现（Frontend Agent）

#### 2.1 创建查询分类工具

**新建文件**: `frontend/src/utils/queryClassifier.ts`

**完整代码**:

```typescript
/**
 * 查询意图分类工具
 * 
 * 基于正则表达式快速分类查询意图，用于前端推荐检索模式。
 */

export type QueryIntent = 'keyword' | 'semantic' | 'mixed' | 'analytical'
export type SearchMode = 'dense' | 'bm25' | 'hybrid' | 'auto'

export interface IntentResult {
  intent: QueryIntent
  confidence: number
  reason: string
  recommendedMode: SearchMode
  keywords: string[]
}

/** 正则模式定义 */
const PATTERNS: Record<QueryIntent, RegExp[]> = {
  keyword: [
    /\d{4}[.\/\-]\d{1,2}[.\/\-]\d{1,2}/,      // 日期
    /版本[vV]?\d+/,                             // 版本号
    /\d+年第\d+季度/,                           // 季度
    /\d+[万千万亿]+/,                           // 大数值
    /\d{6,}/,                                    // 长数字
    /[A-Z]{2,}\d+/,                             // 术语+数字
  ],
  semantic: [
    /如何.{2,}/,                                 // 如何...
    /为什么.{2,}/,                               // 为什么...
    /什么.{2,}/,                                 // 什么...
    /介绍.{2,}/,                                 // 介绍...
    /.{2,}情况.{0,}/,                           // 分析...情况
  ],
  analytical: [
    /.{2,}分析.{2,}/,                           // 分析...
    /.{2,}生成.{2,}/,                           // 生成...
    /.{2,}总结.{2,}/,                           // 总结...
    /.{2,}报告.{2,}/,                           // 报告...
  ],
  mixed: [],
}

/** 示例查询 */
export const EXAMPLE_QUERIES: Record<QueryIntent, string[]> = {
  keyword: [
    '2026年8月21日的版本号',
    '第三季度前5日的营收',
    'BGE-M3模型的维度',
    'Python 3.11 环境配置',
  ],
  semantic: [
    '如何搭建开发环境？',
    '销售目标达成情况如何？',
    '最新的产品需求规格是什么？',
  ],
  analytical: [
    '分析本月销售数据，生成报告',
    '总结三季度工作成果',
  ],
  mixed: [
    '第三季度销售数据分析',
  ],
}

/**
 * 分类查询意图
 */
export function classifyQuery(query: string): IntentResult {
  if (!query || !query.trim()) {
    return {
      intent: 'semantic',
      confidence: 0.5,
      reason: '空查询，使用默认语义检索',
      recommendedMode: 'dense',
      keywords: [],
    }
  }

  // 统计各模式匹配数
  const scores = {
    keyword: 0,
    semantic: 0,
    analytical: 0,
    mixed: 0,
  }

  for (const [intent, patterns] of Object.entries(PATTERNS) as [QueryIntent, RegExp[]][]) {
    for (const pattern of patterns) {
      if (pattern.test(query)) {
        scores[intent]++
      }
    }
  }

  // 提取关键词
  const keywords = extractKeywords(query)

  // 判断意图
  const maxScore = Math.max(...Object.values(scores))
  let intent: QueryIntent
  let confidence = 0.5
  let reason = ''

  if (maxScore === 0) {
    intent = 'semantic'
    confidence = 0.5
    reason = '未检测到特定模式，使用语义检索'
  } else if (scores.analytical >= 1 && maxScore === scores.analytical) {
    intent = 'analytical'
    confidence = Math.min(0.95, 0.6 + scores.analytical * 0.1)
    reason = '检测到分析型查询模式'
  } else if (scores.keyword >= scores.semantic) {
    intent = 'keyword'
    confidence = Math.min(0.95, 0.6 + scores.keyword * 0.1)
    reason = '检测到关键词/数值查询模式'
  } else {
    intent = 'semantic'
    confidence = Math.min(0.95, 0.6 + scores.semantic * 0.1)
    reason = '检测到自然语言查询模式'
  }

  // 推荐检索模式
  const recommendedMode = intentToMode(intent)

  return {
    intent,
    confidence,
    reason,
    recommendedMode,
    keywords,
  }
}

/**
 * 意图转检索模式
 */
function intentToMode(intent: QueryIntent): SearchMode {
  const mapping: Record<QueryIntent, SearchMode> = {
    keyword: 'bm25',
    semantic: 'dense',
    mixed: 'hybrid',
    analytical: 'hybrid',
  }
  return mapping[intent]
}

/**
 * 提取关键词
 */
function extractKeywords(query: string): string[] {
  const keywords: string[] = []
  
  // 中文词语
  const zhWords = query.match(/[\u4e00-\u9fff]{2,}/g)
  if (zhWords) keywords.push(...zhWords)
  
  // 英文单词
  const enWords = query.match(/[a-zA-Z]{3,}/g)
  if (enWords) keywords.push(...enWords)
  
  // 数字
  const numbers = query.match(/\d{2,}/g)
  if (numbers) keywords.push(...numbers)
  
  // 去重
  return [...new Set(keywords)].slice(0, 10)
}

/**
 * 获取意图标签样式类名
 */
export function getIntentStyleClass(intent: QueryIntent): string {
  return `intent-${intent}`
}

/**
 * 获取检索模式标签样式类名
 */
export function getModeStyleClass(mode: SearchMode): string {
  return `mode-${mode}`
}
```

---

#### 2.2 创建检索模式选择器组件

**新建文件**: `frontend/src/components/SearchModeSelector.vue`

**完整代码**:

```vue
<template>
  <div class="search-mode-selector">
    <!-- 智能推荐展示 -->
    <div v-if="showRecommendation && intentResult" class="recommendation">
      <span class="recommend-label">智能推荐</span>
      <span class="recommend-mode" :class="`mode-${intentResult.recommendedMode}`">
        {{ modeDescription(intentResult.recommendedMode) }}
      </span>
      <span class="recommend-reason">{{ intentResult.reason }}</span>
    </div>
    
    <!-- 模式选择按钮 -->
    <div class="mode-buttons">
      <button
        v-for="mode in modes"
        :key="mode.value"
        :class="['mode-btn', { active: selectedMode === mode.value }]"
        @click="$emit('change', mode.value)"
      >
        <span class="mode-icon">{{ mode.icon }}</span>
        <span class="mode-name">{{ mode.name }}</span>
      </button>
    </div>
    
    <!-- 示例查询 -->
    <div v-if="showExamples && currentExamples.length > 0" class="examples">
      <span class="example-label">示例查询：</span>
      <button
        v-for="example in currentExamples"
        :key="example"
        class="example-btn"
        @click="$emit('query', example)"
      >
        {{ example }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { classifyQuery, type IntentResult, type SearchMode, EXAMPLE_QUERIES } from '@/utils/queryClassifier'

interface Props {
  query?: string
  selectedMode?: SearchMode
  showRecommendation?: boolean
  showExamples?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  query: '',
  selectedMode: 'auto',
  showRecommendation: true,
  showExamples: true,
})

const emit = defineEmits<{
  (e: 'change', mode: SearchMode): void
  (e: 'query', query: string): void
}>()

// 模式列表
const modes = [
  { value: 'auto' as SearchMode, name: '智能', icon: '🤖' },
  { value: 'dense' as SearchMode, name: '向量', icon: '📊' },
  { value: 'bm25' as SearchMode, name: '关键词', icon: '🔍' },
  { value: 'hybrid' as SearchMode, name: '混合', icon: '⚡' },
] as const

// 当前意图结果
const intentResult = computed<IntentResult | null>(() => {
  if (!props.query) return null
  return classifyQuery(props.query)
})

// 当前示例查询
const currentExamples = computed<string[]>(() => {
  if (!intentResult.value) return []
  const intent = intentResult.value.intent
  return EXAMPLE_QUERIES[intent] || []
})

// 模式描述
function modeDescription(mode: SearchMode): string {
  const descriptions: Record<SearchMode, string> = {
    auto: '智能推荐',
    dense: '向量检索',
    bm25: '关键词检索',
    hybrid: '混合检索',
  }
  return descriptions[mode]
}
</script>

<style scoped>
.search-mode-selector {
  margin-top: 12px;
  padding: 12px;
  background: var(--card);
  border-radius: var(--card-radius);
  border: 1px solid var(--line);
  box-shadow: var(--shadow-card);
}

.recommendation {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: var(--paper-2);
  border-radius: var(--input-radius);
  font-size: 13px;
}

.recommend-label {
  color: var(--text-muted);
  font-weight: 500;
}

.recommend-mode {
  padding: 2px 8px;
  border-radius: var(--btn-radius);
  font-weight: 600;
  font-size: 12px;
}

.recommend-mode.mode-auto {
  background: rgba(33, 49, 56, 0.1);
  color: var(--vermillion);
}

.recommend-mode.mode-dense {
  background: rgba(31, 122, 77, 0.1);
  color: var(--success);
}

.recommend-mode.mode-bm25 {
  background: rgba(165, 131, 62, 0.1);
  color: var(--warning);
}

.recommend-mode.mode-hybrid {
  background: rgba(176, 71, 47, 0.1);
  color: var(--error);
}

.recommend-reason {
  color: var(--text-muted);
  font-size: 12px;
  margin-left: auto;
}

.mode-buttons {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.mode-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  border: 1px solid var(--line);
  border-radius: var(--input-radius);
  background: var(--paper);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 12px;
  color: var(--ink);
}

.mode-btn:hover {
  border-color: var(--vermillion);
  background: rgba(33, 49, 56, 0.05);
  transform: translateY(-1px);
}

.mode-btn.active {
  border-color: var(--vermillion);
  background: var(--vermillion);
  color: var(--paper);
}

.mode-icon {
  font-size: 18px;
}

.mode-name {
  font-weight: 500;
}

.examples {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.example-label {
  color: var(--text-muted);
  font-size: 12px;
}

.example-btn {
  padding: 4px 12px;
  border: 1px solid var(--line);
  border-radius: 20px;
  background: var(--paper);
  cursor: pointer;
  font-size: 12px;
  color: var(--ink);
  transition: all 0.2s ease;
}

.example-btn:hover {
  border-color: var(--vermillion);
  background: rgba(33, 49, 56, 0.05);
}
</style>
```

---

#### 2.3 修改 ChatView

**修改文件**: `frontend/src/views/ChatView.vue`

**改动说明**：
1. 引入 `SearchModeSelector` 组件
2. 添加 `searchMode` 状态
3. 发送消息时传递 `mode` 参数
4. 在查询输入框附近添加组件

**关键代码片段**:

```vue
<!-- 模板部分 -->
<template>
  <div class="chat-view">
    <!-- ... 其他内容 ... -->
    
    <div class="query-section">
      <!-- 检索模式选择器 -->
      <SearchModeSelector
        v-model:query="query"
        v-model:selected-mode="searchMode"
        @change="onModeChange"
        @query="onExampleQuery"
      />
      
      <!-- 查询输入框 -->
      <textarea
        v-model="query"
        placeholder="输入您的问题..."
        @keydown.enter.ctrl="sendMessage"
      />
      
      <button @click="sendMessage">发送</button>
    </div>
  </div>
</template>

<!-- Script 部分 -->
<script setup lang="ts">
import { ref } from 'vue'
import SearchModeSelector from '@/components/SearchModeSelector.vue'
import { chatStream } from '@/api/chat'
import type { SearchMode } from '@/utils/queryClassifier'

const query = ref('')
const searchMode = ref<SearchMode>('auto')

function onModeChange(mode: SearchMode) {
  searchMode.value = mode
}

function onExampleQuery(example: string) {
  query.value = example
}

async function sendMessage() {
  if (!query.value.trim()) return
  
  // 调用 API 时传入 searchMode
  await chatStream({
    sessionId: currentSessionId.value,
    kbId: currentKbId.value,
    message: query.value,
    mode: searchMode.value,
  })
}
</script>
```

---

### Phase 3: 测试实现（Test Agent）

#### 3.1 后端单元测试

**新建文件**: `ai-service/tests/test_intent_classifier.py`

```python
"""意图识别模块单元测试。"""
import pytest
from rag.intent_classifier import classify_intent, recommend_mode, QueryIntent


class TestClassifyIntent:
    """意图分类测试。"""
    
    def test_keyword_intent_date(self):
        """测试日期查询识别。"""
        result = classify_intent("2026年8月21日的版本号")
        assert result.intent == QueryIntent.KEYWORD
        assert result.confidence > 0.6
    
    def test_keyword_intent_version(self):
        """测试版本号查询识别。"""
        result = classify_intent("BGE-M3模型的维度")
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
        assert "版本" in result.keywords


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
```

---

#### 3.2 BM25 检索测试

**新建文件**: `ai-service/tests/test_bm25_retriever.py`

```python
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
```

---

## ✅ 验收标准

### 功能验收
- [ ] BM25 检索能正确匹配包含日期、版本、数值的查询
- [ ] 混合检索能融合 Dense 和 BM25 结果
- [ ] 智能推荐能正确识别查询意图
- [ ] 前端 UI 能显示推荐模式和示例查询
- [ ] API 向后兼容（mode 参数可选）

### 代码验收
- [ ] 所有函数有类型注解
- [ ] 所有公开函数有 docstring
- [ ] 有错误处理
- [ ] 代码符合 PEP 8 / TypeScript 规范
- [ ] 前端样式与项目设计令牌一致

### 测试验收
- [ ] 意图识别单元测试通过
- [ ] BM25 检索测试通过
- [ ] API 接口测试通过

---

## 📁 文件清单

### 新增文件
1. `ai-service/rag/intent_classifier.py`
2. `ai-service/rag/bm25_retriever.py`
3. `ai-service/rag/hybrid_retriever.py`
4. `ai-service/tests/test_intent_classifier.py`
5. `ai-service/tests/test_bm25_retriever.py`
6. `frontend/src/utils/queryClassifier.ts`
7. `frontend/src/components/SearchModeSelector.vue`

### 修改文件
1. `ai-service/requirements.txt`
2. `ai-service/routers/search.py`
3. `ai-service/routers/chat.py`
4. `frontend/src/views/ChatView.vue`
5. `frontend/src/api/chat.ts`

---

## 🚀 实施顺序

1. **Backend Agent** 先实现：
   - 安装依赖
   - intent_classifier.py
   - bm25_retriever.py
   - hybrid_retriever.py
   - 修改 search.py 和 chat.py

2. **Frontend Agent** 实现：
   - queryClassifier.ts
   - SearchModeSelector.vue
   - 修改 ChatView.vue

3. **Test Agent** 实现：
   - 单元测试
   - 集成测试

4. **主协调 Agent** 集成验证：
   - Docker 重建
   - API 测试
   - 前端构建

---

**现在开始实现，按照上述计划逐步完成。**
