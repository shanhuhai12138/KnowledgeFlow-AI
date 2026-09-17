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
    /\d{4}[.\/\-]\d{1,2}[.\/\-]\d{1,2}/,      // 日期（数字分隔）
    /\d{1,2}月\d{1,2}日/,                           // 中文日期（8月21日）
    /\d{4}年/,                                       // 含年份（2026年）
    /版本号|版本[vV]?\d+/,                      // 版本号（含「版本号」词本身）
    /[A-Za-z]{2,}\d+[A-Za-z]*/,                 // 术语+数字（Knife4j / BGE-M3 / v2）
    /\d+年第\d+季度/,                           // 季度
    /\d+[万千万亿]+/,                           // 大数值
    /\d{6,}/,                                    // 长数字
    /[A-Z]{2,}\d+/,                             // 术语+数字
  ],
  semantic: [
    /如何.{2,}/,                                 // 如何...
    /为什么.{2,}/,                               // 为什么...
    /^什么.{2,}|什么是/,                        // 什么...（句首或「什么是」，避免「…的是什么」误报）
    /介绍.{2,}/,                                 // 介绍...
    /.{2,}情况.{0,}/,                           // 分析...情况
  ],
  analytical: [
    /分析.{2,}|.{2,}分析.{2,}/,                 // 分析（含句首「分析…」）
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

  // 强关键词信号（日期/版本号/季度/大数值）权重 ×2：对冲语义类弱正则误报
  // 如「…的版本号是什么」中「什么」会误触 semantic 的 /什么.{2,}/
  const strongKeyword = PATTERNS.keyword.slice(0, 4)
  for (const [intent, patterns] of Object.entries(PATTERNS) as [QueryIntent, RegExp[]][]) {
    const weight = intent === 'keyword' && patterns === strongKeyword ? 2 : 1
    for (const pattern of patterns) {
      if (pattern.test(query)) {
        scores[intent] += weight
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
