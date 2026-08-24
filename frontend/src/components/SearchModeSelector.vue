<template>
  <div class="search-mode-selector">
    <!-- 顶部提示 -->
    <div class="selector-header">
      <span class="header-icon">
        <svg width="14" height="14" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </span>
      <span class="header-text">智能推荐检索模式，可根据查询类型手动切换</span>
    </div>

    <!-- 智能推荐展示 -->
    <div v-if="showRecommendation && intentResult" class="recommendation">
      <span class="recommend-label">推荐模式</span>
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
        @mouseenter="showTooltip = mode.value"
        @mouseleave="showTooltip = null"
      >
        <svg class="mode-icon" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8" fill="none">
          <path v-if="mode.value === 'auto'" stroke-linecap="round" stroke-linejoin="round" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          <path v-else-if="mode.value === 'dense'" stroke-linecap="round" stroke-linejoin="round" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 14c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4z" />
          <path v-else-if="mode.value === 'bm25'" stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          <path v-else-if="mode.value === 'hybrid'" stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <span class="mode-name">{{ mode.name }}</span>
        
        <!-- Tooltip 提示框 -->
        <transition name="tooltip-fade">
          <div v-if="showTooltip === mode.value" class="mode-tooltip" :class="`tooltip-${mode.value}`">
            <div class="tooltip-title">{{ mode.tooltipTitle }}</div>
            <div class="tooltip-desc">{{ mode.tooltipDesc }}</div>
            <div class="tooltip-examples">
              <div class="tooltip-label">适用场景：</div>
              <ul>
                <li v-for="(ex, i) in mode.examples" :key="i">{{ ex }}</li>
              </ul>
            </div>
          </div>
        </transition>
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
import { ref, computed } from 'vue'
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

// 当前显示的 tooltip
const showTooltip = ref<SearchMode | null>(null)

// 模式定义（包含 tooltip 信息）
const modes = [
  {
    value: 'auto' as SearchMode,
    name: '智能',
    tooltipTitle: '智能推荐 (Auto)',
    tooltipDesc: '系统自动识别查询意图，推荐最优检索模式',
    examples: ['系统会根据您的查询内容自动判断使用哪种检索方式'],
  },
  {
    value: 'dense' as SearchMode,
    name: '向量',
    tooltipTitle: '向量检索 (Dense)',
    tooltipDesc: '基于语义理解，适合自然语言查询和概念匹配',
    examples: ['如何搭建开发环境？', '销售目标达成情况如何？', '介绍公司的规章制度'],
  },
  {
    value: 'bm25' as SearchMode,
    name: '关键词',
    tooltipTitle: '关键词检索 (BM25)',
    tooltipDesc: '基于精确匹配，适合日期、版本、数值等固定格式查询',
    examples: ['2026年8月21日的版本号', '第三季度前5日的营收', 'Python 3.11 环境配置'],
  },
  {
    value: 'hybrid' as SearchMode,
    name: '混合',
    tooltipTitle: '混合检索 (Hybrid)',
    tooltipDesc: '结合语义理解和关键词匹配，使用 RRF 算法融合结果',
    examples: ['分析本月销售数据', '生成季度工作报告', '总结项目技术要点'],
  },
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
  position: relative;
}

/* 顶部提示 */
.selector-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  margin-bottom: 10px;
  background: var(--paper-2);
  border-radius: var(--input-radius);
  font-size: 12px;
  color: var(--text-muted);
}

.header-icon {
  color: var(--vermillion);
  flex-shrink: 0;
}

.header-text {
  line-height: 1.4;
}

.recommendation {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: rgba(33, 49, 56, 0.04);
  border-radius: var(--input-radius);
  font-size: 13px;
  border: 1px solid rgba(33, 49, 56, 0.08);
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
  position: relative;
}

.mode-btn {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 14px;
  border: 1px solid var(--line);
  border-radius: var(--input-radius);
  background: var(--paper);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 12px;
  color: var(--ink);
  min-width: 64px;
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

.mode-btn.active .mode-icon {
  stroke: var(--paper);
}

.mode-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  stroke: var(--ink);
  transition: stroke 0.2s ease;
}

.mode-name {
  font-weight: 500;
}

/* Tooltip 样式 */
.mode-tooltip {
  position: absolute;
  top: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  min-width: 220px;
  max-width: 280px;
  padding: 12px;
  background: var(--card);
  border: 1px solid var(--line-strong);
  border-radius: var(--card-radius);
  box-shadow: var(--shadow-hover);
  z-index: 1000;
  font-size: 12px;
  line-height: 1.5;
  color: var(--ink);
}

/* Tooltip 箭头 */
.mode-tooltip::before {
  content: '';
  position: absolute;
  top: -6px;
  left: 50%;
  transform: translateX(-50%);
  border-left: 6px solid transparent;
  border-right: 6px solid transparent;
  border-bottom: 6px solid var(--line-strong);
}

/* Tooltip 标题 */
.tooltip-title {
  font-weight: 600;
  font-size: 13px;
  margin-bottom: 6px;
  color: var(--vermillion);
}

/* Tooltip 描述 */
.tooltip-desc {
  color: var(--text-muted);
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--line);
}

/* Tooltip 示例 */
.tooltip-examples {
  margin-top: 8px;
}

.tooltip-label {
  font-weight: 500;
  color: var(--ink);
  margin-bottom: 4px;
}

.tooltip-examples ul {
  margin: 0;
  padding: 0 0 0 16px;
  list-style-type: disc;
}

.tooltip-examples li {
  color: var(--text-muted);
  margin-bottom: 2px;
}

/* Tooltip 颜色主题 */
.tooltip-auto .tooltip-title { color: var(--vermillion); }
.tooltip-dense .tooltip-title { color: var(--success); }
.tooltip-bm25 .tooltip-title { color: var(--warning); }
.tooltip-hybrid .tooltip-title { color: var(--error); }

/* Tooltip 动画 */
.tooltip-fade-enter-active,
.tooltip-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.tooltip-fade-enter-from,
.tooltip-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-4px);
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

/* 响应式 */
@media (max-width: 640px) {
  .mode-btn {
    min-width: 56px;
    padding: 6px 10px;
  }
  
  .mode-tooltip {
    min-width: 180px;
    max-width: 220px;
  }
}
</style>
