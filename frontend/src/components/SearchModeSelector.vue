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
        <svg class="mode-icon" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8" fill="none">
          <path v-if="mode.value === 'auto'" stroke-linecap="round" stroke-linejoin="round" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          <path v-else-if="mode.value === 'dense'" stroke-linecap="round" stroke-linejoin="round" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 14c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4z" />
          <path v-else-if="mode.value === 'bm25'" stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          <path v-else-if="mode.value === 'hybrid'" stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
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
  { value: 'auto' as SearchMode, name: '智能' },
  { value: 'dense' as SearchMode, name: '向量' },
  { value: 'bm25' as SearchMode, name: '关键词' },
  { value: 'hybrid' as SearchMode, name: '混合' },
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
  background: rgba(33, 49, 56, 0.08);
  color: var(--vermillion);
}

.recommend-mode.mode-dense {
  background: rgba(31, 122, 77, 0.08);
  color: var(--success);
}

.recommend-mode.mode-bm25 {
  background: rgba(165, 131, 62, 0.08);
  color: var(--warning);
}

.recommend-mode.mode-hybrid {
  background: rgba(176, 71, 47, 0.08);
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
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
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
}

.mode-btn.active {
  border-color: var(--vermillion);
  background: var(--vermillion);
  color: var(--paper);
}

.mode-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
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
