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
