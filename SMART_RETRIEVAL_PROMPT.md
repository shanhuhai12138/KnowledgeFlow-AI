# 智能检索系统实现 - AI 提示词

## 角色定位
你是一名资深 Python/TypeScript 全栈工程师，负责实现 KnowledgeFlow-AI 项目的智能检索系统。

## 项目背景
KnowledgeFlow-AI 是一个企业级 RAG（检索增强生成）知识库系统，当前已实现：
- 后端：Spring Boot 2.7.18 + Java 17
- 前端：Vue 3 + TypeScript + Vite
- AI服务：Python FastAPI + LangGraph
- 向量库：Qdrant
- 对象存储：MinIO

**当前检索能力**：
- ✅ Dense 向量检索（Cosine 相似度）
- ❌ BM25 关键词检索
- ❌ Hybrid 混合检索
- ❌ 智能检索推荐

## 实现目标
实现智能检索算法推荐系统，根据用户查询类型自动选择最优检索算法。

---

## 代码规范

### Python 代码规范
1. **类型注解**：所有函数必须包含类型注解
2. **文档字符串**：每个公开函数必须有 docstring
3. **异常处理**：使用 try-except 处理外部依赖错误
4. **配置管理**：使用 pydantic-settings 管理配置
5. **代码风格**：遵循 PEP 8，使用 black 格式化

### TypeScript 代码规范
1. **严格模式**：使用 TypeScript 严格模式
2. **类型安全**：所有 API 响应必须定义接口
3. **组件设计**：使用 Composition API + `<script setup>`
4. **样式隔离**：使用 scoped CSS 或 CSS Modules

---

## 实现步骤

### Step 1: 后端依赖安装

**文件**: `ai-service/requirements.txt`

添加以下依赖：
```
rank-bm25==0.2.2
jieba==0.42.1
```

执行安装：
```bash
cd ai-service
pip install -r requirements.txt
```

---

### Step 2: 创建意图识别模块

**新建文件**: `ai-service/rag/intent_classifier.py`

实现内容：
1. 定义 `QueryIntent` 枚举：KEYWORD, SEMANTIC, MIXED, ANALYTICAL
2. 实现 `classify_intent(query: str) -> IntentResult` 函数
3. 实现 `recommend_mode(intent) -> str` 函数
4. 使用正则表达式匹配查询特征：
   - KEYWORD: 日期(YYYY.MM.DD)、版本(v1.0)、数值(100万)、季度(Q3)
   - SEMANTIC: 如何...、为什么...、什么...、介绍...
   - ANALYTICAL: 分析...、生成...、总结...、报告...

关键代码结构：
```python
from enum import Enum
from typing import List, Optional

class QueryIntent(str, Enum):
    KEYWORD = "keyword"
    SEMANTIC = "semantic"
    MIXED = "mixed"
    ANALYTICAL = "analytical"

class IntentResult:
    def __init__(self, intent, confidence, keywords, reason):
        self.intent = intent
        self.confidence = confidence
        self.keywords = keywords
        self.reason = reason

def classify_intent(query: str) -> IntentResult:
    # 正则匹配
    # 统计各模式分数
    # 返回最高分模式
    pass

def recommend_mode(intent: QueryIntent) -> str:
    # KEYWORD -> "bm25"
    # SEMANTIC -> "dense"
    # MIXED/ANALYTICAL -> "hybrid"
    pass
```

---

### Step 3: 创建 BM25 检索器

**新建文件**: `ai-service/rag/bm25_retriever.py`

实现内容：
1. `BM25Retriever` 类
2. 构造函数接收文档列表
3. `_tokenize(text)` 方法：中英文混合分词
4. `search(query, top_k, threshold)` 方法：返回 BM25 结果

关键代码结构：
```python
from rank_bm25 import BM25Okapi
import re

class BM25Retriever:
    def __init__(self, documents: List[dict]):
        # documents: [{"id": str, "content": str, "metadata": dict}, ...]
        self.documents = documents
        self.tokenized_docs = [self._tokenize(doc["content"]) for doc in documents]
        self.bm25 = BM25Okapi(self.tokenized_docs)
    
    def _tokenize(self, text: str) -> List[str]:
        # 中文：连续汉字按字符分
        # 英文：连续字母按单词分
        # 数字：连续数字作为一个token
        tokens = []
        # 提取中文词语
        zh_words = re.findall(r'[\u4e00-\u9fff]{2,}', text)
        for word in zh_words:
            tokens.extend(list(word))
        # 提取英文单词
        en_words = re.findall(r'[a-zA-Z]{3,}', text)
        tokens.extend([w.lower() for w in en_words])
        # 提取数字
        numbers = re.findall(r'\d{2,}', text)
        tokens.extend(numbers)
        return tokens
    
    def search(self, query: str, top_k: int = 5, threshold: float = 0.0) -> List[dict]:
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        scores = self.bm25.get_scores(query_tokens)
        results = []
        for idx in scores.argsort()[::-1][:top_k]:
            score = float(scores[idx])
            if score >= threshold:
                results.append({
                    "id": self.documents[idx]["id"],
                    "score": score,
                    "content": self.documents[idx]["content"],
                    **self.documents[idx].get("metadata", {})
                })
        return results
```

---

### Step 4: 创建混合检索器

**新建文件**: `ai-service/rag/hybrid_retriever.py`

实现内容：
1. `HybridRetriever` 类
2. 接收 dense retriever 和 sparse retriever
3. 实现 RRF (Reciprocal Rank Fusion) 融合算法
4. `search(query, vector, top_k, threshold)` 方法

RRF 融合公式：
```
score(doc) = Σ 1/(k + rank(doc) + 1)
```
其中 k 是常数，通常取 60。

关键代码结构：
```python
class HybridRetriever:
    def __init__(self, dense_retriever, sparse_retriever, rrf_k=60):
        self.dense = dense_retriever
        self.sparse = sparse_retriever
        self.rrf_k = rrf_k
    
    def search(self, query, vector, top_k=5, threshold=0.0):
        # 双路检索
        dense_results = self.dense.search(vector, top_k=top_k*2, threshold=threshold)
        sparse_results = self.sparse.search(query, top_k=top_k*2, threshold=threshold)
        
        # RRF 融合
        rrf_scores = {}
        for i, hit in enumerate(dense_results):
            doc_id = hit["documentId"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1/(self.rrf_k + i + 1)
        
        for i, hit in enumerate(sparse_results):
            doc_id = hit["id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1/(self.rrf_k + i + 1)
        
        # 排序并返回
        sorted_results = sorted(rrf_scores.items(), key=lambda x: -x[1])[:top_k]
        return [...]
```

---

### Step 5: 修改 Search API

**修改文件**: `ai-service/routers/search.py`

添加内容：
1. 新增 `mode` 参数（auto/dense/bm25/hybrid）
2. 新增 `mode_override` 参数（用户手动覆盖）
3. 根据 mode 选择检索策略
4. 返回意图识别结果（当 mode=auto 时）

关键改动：
```python
class SearchRequest(BaseModel):
    query: str
    kbId: str | int
    topK: Optional[int] = None
    threshold: Optional[float] = None
    mode: str = "auto"  # 新增
    mode_override: Optional[str] = None  # 新增

@router.post("/ai/search", response_model=SearchResponse)
def search_endpoint(req: SearchRequest):
    # 根据 mode 执行不同检索
    if mode == "auto":
        intent = classify_intent(req.query)
        recommended_mode = recommend_mode(intent.intent)
        # 使用推荐模式检索
    elif mode == "bm25":
        # BM25 检索
    elif mode == "hybrid":
        # 混合检索
    else:
        # Dense 检索（默认）
    
    return SearchResponse(
        query=req.query,
        mode=mode,
        intent=intent_info,  # 当 mode=auto 时返回
        tookMs=took_ms,
        results=results
    )
```

---

### Step 6: 修改 Chat API

**修改文件**: `ai-service/routers/chat.py`

添加内容：
1. `ChatRequest` 新增 `mode` 参数
2. `_retrieve` 函数支持 mode 参数
3. 调用检索时使用指定模式

关键改动：
```python
class ChatRequest(BaseModel):
    sessionId: str
    kbId: str | int
    message: str
    history: Optional[List[ChatHistoryItem]] = None
    mode: str = "auto"  # 新增

def _retrieve(kb_id, query, top_k, mode="auto"):
    # 根据 mode 执行不同检索
    # 返回 (results, confidence)
```

---

### Step 7: 前端工具函数

**新建文件**: `frontend/src/utils/queryClassifier.ts`

实现内容：
1. `QueryIntent` 类型
2. `IntentResult` 接口
3. `classifyQuery(query)` 函数
4. 示例查询数据

关键代码结构：
```typescript
export type QueryIntent = 'keyword' | 'semantic' | 'mixed' | 'analytical'
export type SearchMode = 'dense' | 'bm25' | 'hybrid' | 'auto'

export interface IntentResult {
  intent: QueryIntent
  confidence: number
  reason: string
  recommendedMode: SearchMode
  keywords: string[]
}

export function classifyQuery(query: string): IntentResult {
  // 与后端相同的正则逻辑
  // 返回意图结果
}

export const EXAMPLE_QUERIES = {
  keyword: ['2026年8月21日的版本号', '第三季度前5日的营收', ...],
  semantic: ['如何搭建开发环境？', '销售目标达成情况如何？', ...],
  analytical: ['分析本月销售数据，生成报告', ...],
}
```

---

### Step 8: 前端组件

**新建文件**: `frontend/src/components/SearchModeSelector.vue`

实现内容：
1. 智能推荐展示（当有 query 时）
2. 模式选择按钮（auto/dense/bm25/hybrid）
3. 示例查询快捷按钮
4. 样式与项目设计令牌一致

使用项目令牌：
- `--ink`: #213138
- `--paper`: #FAFAFA
- `--card`: #FFFFFF
- `--accent`: #E34234
- `--border`: #E5E7EB

---

### Step 9: 修改 ChatView

**修改文件**: `frontend/src/views/ChatView.vue`

添加内容：
1. 引入 `SearchModeSelector` 组件
2. 添加 `searchMode` 状态
3. 发送消息时传递 `mode` 参数
4. 显示检索模式信息

---

## 验收标准

### 功能验收
- [ ] BM25 检索能正确匹配包含日期、版本、数值的查询
- [ ] 混合检索能融合 Dense 和 BM25 结果
- [ ] 智能推荐能正确识别查询意图
- [ ] 前端 UI 能显示推荐模式和示例查询

### 代码验收
- [ ] 所有函数有类型注解
- [ ] 所有公开函数有 docstring
- [ ] 有错误处理
- [ ] 代码符合 PEP 8 / TypeScript 规范

### 测试验收
- [ ] 意图识别单元测试通过
- [ ] BM25 检索测试通过
- [ ] 混合检索测试通过
- [ ] API 接口测试通过

---

## 文件清单

### 新增文件
1. `ai-service/rag/intent_classifier.py`
2. `ai-service/rag/bm25_retriever.py`
3. `ai-service/rag/hybrid_retriever.py`
4. `frontend/src/utils/queryClassifier.ts`
5. `frontend/src/components/SearchModeSelector.vue`

### 修改文件
1. `ai-service/requirements.txt`
2. `ai-service/routers/search.py`
3. `ai-service/routers/chat.py`
4. `frontend/src/views/ChatView.vue`
5. `frontend/src/api/chat.ts`

---

## 注意事项

1. **向后兼容**：新增参数为可选，默认值为 `auto`
2. **错误降级**：BM25 检索失败时自动降级到 Dense
3. **性能优化**：BM25 索引只需构建一次，可缓存
4. **测试数据**：确保 Qdrant 中有测试文档

---

**现在开始实现，按照上述步骤逐一完成。**
