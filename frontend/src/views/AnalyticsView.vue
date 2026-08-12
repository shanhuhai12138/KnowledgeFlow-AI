<script setup lang="ts">
// 看板页（T3.3）：4 统计卡接 /stat/overview（保留数字滚动）、7日趋势 /stat/trend 折线图（lieflat 单色）、
// 文档类型 /stat/doc-types 环形图、热门查询 /stat/hot 排行（进度条+tooltip）
// 降级：接口未就绪（后端开发中）→ 占位 + 重试，不白屏不报错；就绪后自动切真实数据
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getDocTypesApi,
  getHotApi,
  getOverviewApi,
  getTrendApi,
  type StatDocType,
  type StatHotItem,
  type StatOverview,
  type StatTrendItem,
} from '@/api/stat'

type LoadState = 'loading' | 'ok' | 'empty' | 'failed'

// ---------- 数据与状态 ----------
const overview = ref<StatOverview | null>(null)
const trend = ref<StatTrendItem[]>([])
const docTypes = ref<StatDocType[]>([])
const hot = ref<StatHotItem[]>([])
const status = reactive<Record<string, LoadState>>({
  overview: 'loading',
  trend: 'loading',
  docTypes: 'loading',
  hot: 'loading',
})

const STAT_CARDS = [
  { key: 'documentCount', label: '文档向量化' },
  { key: 'queryCount', label: '总查询次数' },
  { key: 'llmCallCount', label: 'LLM 调用次数' },
  { key: 'kbCount', label: '活跃知识库' },
] as const
type StatKey = (typeof STAT_CARDS)[number]['key']

// 数字滚动（overview 就绪时从 0 滚到真实值）
const displayed = reactive<Record<StatKey, string>>({ documentCount: '0', queryCount: '0', llmCallCount: '0', kbCount: '0' })
const statEls = reactive<Partial<Record<StatKey, HTMLElement>>>({})
const reducedMotion = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

function setStatEl(key: StatKey) {
  return (el: unknown) => {
    if (el instanceof HTMLElement) statEls[key] = el
  }
}

function animateStat(data: StatOverview) {
  for (const card of STAT_CARDS) {
    const key = card.key
    const to = data[key] ?? 0
    const el = statEls[key]
    if (!el || reducedMotion) {
      displayed[key] = to.toLocaleString()
      continue
    }
    const start = performance.now()
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / 1500)
      const e = 1 - Math.pow(1 - t, 3)
      displayed[key] = Math.round(to * e).toLocaleString()
      if (t < 1) requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  }
}

// ---------- 加载（全量） ----------
async function loadAll() {
  ;(Object.keys(status) as Array<keyof typeof status>).forEach((k) => (status[k] = 'loading'))
  const [ov, tr, dt, ht] = await Promise.all([getOverviewApi(), getTrendApi(7), getDocTypesApi(), getHotApi(5)])

  if (ov) {
    overview.value = ov
    animateStat(ov)
    status.overview = 'ok'
  } else {
    status.overview = 'failed'
  }

  if (tr && tr.length) {
    trend.value = tr
    status.trend = 'ok'
  } else {
    trend.value = []
    status.trend = tr && !tr.length ? 'empty' : 'failed'
  }

  if (dt && dt.length) {
    docTypes.value = dt
    status.docTypes = 'ok'
  } else {
    docTypes.value = []
    status.docTypes = dt && !dt.length ? 'empty' : 'failed'
  }

  if (ht && ht.length) {
    hot.value = ht
    status.hot = 'ok'
  } else {
    hot.value = []
    status.hot = ht && !ht.length ? 'empty' : 'failed'
  }
}

// ---------- 导出报表（CSV） ----------
const exporting = ref(false)

function exportCSV() {
  if (exporting.value) return
  exporting.value = true
  try {
    // 生成 CSV 数据
    const headers = ['时间', '查询次数', '平均耗时(ms)', '命中率']
    const rows = trend.value.map(t => [
      t.date || t.time,
      t.count,
      t.avgTime || '-',
      t.hitRate ? `${(t.hitRate * 100).toFixed(1)}%` : '-',
    ])

    // 添加汇总行
    if (overview.value) {
      rows.push([])
      rows.push(['汇总统计', '', '', ''])
      rows.push(['总文档数', overview.value.documentCount || 0, '', ''])
      rows.push(['总查询次数', overview.value.queryCount || 0, '', ''])
      rows.push(['LLM 调用次数', overview.value.llmCallCount || 0, '', ''])
      rows.push(['活跃知识库数', overview.value.kbCount || 0, '', ''])
    }

    // 添加文档类型数据
    if (docTypes.value.length) {
      rows.push([])
      rows.push(['文档类型分布', '', '', ''])
      rows.push(['类型', '数量', '占比', ''])
      docTypes.value.forEach(d => {
        const pct = overview.value?.documentCount
          ? `${(d.count / overview.value.documentCount * 100).toFixed(1)}%`
          : '-'
        rows.push([d.type || d.name, d.count, pct, ''])
      })
    }

    // 添加热门查询
    if (hot.value.length) {
      rows.push([])
      rows.push(['热门查询 TOP 10', '', '', ''])
      rows.push(['排名', '查询词', '次数', ''])
      hot.value.slice(0, 10).forEach((h, i) => {
        rows.push([String(i + 1), h.query, h.count, ''])
      })
    }

    // 转换为 CSV 字符串
    const csvContent = [headers, ...rows]
      .map(row => row.map(cell => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(','))
      .join('\n')

    // 添加 BOM 以支持 Excel 打开
    const BOM = '\uFEFF'
    const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `知识库报表_${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    ElMessage.success('报表导出成功')
  } catch (error: any) {
    ElMessage.error(`导出失败: ${error?.message || '未知错误'}`)
  } finally {
    exporting.value = false
  }
}

// ---------- 折线图（SVG，lieflat 单色：深墨蓝折线 + 细线坐标网格，无渐变） ----------
const hoverIdx = ref(-1)
const W = 640
const H = 220
const PAD = { l: 40, r: 16, t: 14, b: 30 }

function niceMax(v: number) {
  if (!v || v <= 0) return 10
  const pow = Math.pow(10, Math.floor(Math.log10(v)))
  const n = v / pow
  const nice = n <= 1 ? 1 : n <= 2 ? 2 : n <= 5 ? 5 : 10
  return nice * pow
}

const chart = computed(() => {
  const n = trend.value.length
  if (!n) return null
  const max = niceMax(Math.max(...trend.value.map((t) => t.count)))
  const iw = W - PAD.l - PAD.r
  const ih = H - PAD.t - PAD.b
  const step = iw / Math.max(n - 1, 1)
  const px = (i: number) => PAD.l + i * step
  const py = (v: number) => PAD.t + ih - (v / max) * ih
  const points = trend.value.map((t, i) => ({ x: px(i), y: py(t.count), ...t }))
  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')
  const gridLines = [0, 1, 2, 3, 4].map((g) => {
    const y = PAD.t + (ih * g) / 4
    return { y, label: Math.round((max * (4 - g)) / 4) }
  })
  return { n, max, step, points, linePath, gridLines }
})

// tooltip 水平定位：按百分比近似（容器 100% 宽 + SVG viewBox 等比），足够演示精度
const tipLeftSimple = computed(() => {
  const c = chart.value
  if (!c || hoverIdx.value < 0) return '0%'
  const pct = (hoverIdx.value / Math.max(c.n - 1, 1)) * 100
  return `calc(${PAD.l}px + ${pct}% * ${(100 - (PAD.l + PAD.r) / 10) / 100})`
})

// ---------- 环形图（conic-gradient 按真实比例） ----------
const PIE_COLORS = ['var(--vermillion)', 'var(--success)', 'var(--gold)']
const pieStyle = computed(() => {
  const total = docTypes.value.reduce((s, d) => s + (d.count || 0), 0)
  if (!total) return {}
  let acc = 0
  const segs = docTypes.value.map((d, i) => {
    const start = acc
    acc += ((d.count || 0) / total) * 360
    return `${PIE_COLORS[i % PIE_COLORS.length]} ${start}deg ${acc}deg`
  })
  return { background: `conic-gradient(${segs.join(',')})` }
})
const docTotal = computed(() => docTypes.value.reduce((s, d) => s + (d.count || 0), 0))

// ---------- 热门查询 ----------
const hotTipIdx = ref(-1)
const MAX_HOT = computed(() => Math.max(...hot.value.map((h) => h.count || 0), 1))
function hotWidth(count: number) {
  return Math.round((count / MAX_HOT.value) * 100) + '%'
}

// 最近查询（契约暂无此接口，保留演示数据并标注）
const recentQueries = [
  { query: '如何配置 OAuth2 鉴权？', kbName: '产品手册库', tookMs: 45, time: '刚刚' },
  { query: '差旅报销标准是什么？', kbName: '财务报销指南', tookMs: 32, time: '5分钟前' },
  { query: '远程办公周三需要到岗吗？', kbName: '人力资源政策', tookMs: 28, time: '12分钟前' },
]

onMounted(loadAll)
</script>

<template>
  <div class="analytics-page page-enter">
    <div class="page-head">
      <h1 class="serif page-title">分析看板</h1>
      <div class="head-actions">
        <button class="btn btn-secondary" @click="loadAll">
          <svg width="16" height="16" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>刷新
        </button>
        <button class="btn btn-secondary" @click="exportCSV" :disabled="exporting">
          <svg width="16" height="16" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          {{ exporting ? '导出中…' : '导出报表' }}
        </button>
    </div>

    <!-- 统计卡（深色带 + 数字滚动） -->
    <div class="stats-grid">
      <div v-if="status.overview === 'failed'" class="card stat-card stats-fallback">
        <div class="stat-label">统计接口未就绪</div>
        <div class="stats-retry">
          <p>后端 /stat/overview 尚未返回数据</p>
          <button class="btn btn-secondary" @click="loadAll">重试</button>
        </div>
      </div>
      <template v-else>
        <div v-for="card in STAT_CARDS" :key="card.key" class="card stat-card">
          <div class="stat-label">{{ card.label }}</div>
          <div class="stat-change">
            <span class="live-dot"></span>实时
          </div>
          <div :ref="setStatEl(card.key)" class="stat-value">{{ displayed[card.key] }}</div>
        </div>
      </template>
    </div>

    <!-- 图表区 -->
    <div class="charts-row">
      <!-- 7 日趋势折线图 -->
      <div class="card chart-card">
        <div class="chart-title">
          <svg width="18" height="18" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
            <path stroke-linecap="round" stroke-linejoin="round" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
          </svg>
          7日搜索趋势
        </div>
        <div v-if="status.trend === 'failed'" class="chart-placeholder">
          <p>后端 /stat/trend 尚未返回数据</p>
          <button class="btn btn-secondary" @click="loadAll">重试</button>
        </div>
        <div v-else-if="status.trend === 'empty'" class="chart-placeholder">
          <p>暂无趋势数据</p>
        </div>
        <div v-else class="trend-box" @mouseleave="hoverIdx = -1">
          <svg :viewBox="`0 0 ${W} ${H}`" class="trend-svg" preserveAspectRatio="none">
            <!-- 网格线 -->
            <g v-if="chart">
              <line
                v-for="g in chart.gridLines"
                :key="g.y"
                :x1="PAD.l" :y1="g.y" :x2="W - PAD.r" :y2="g.y"
                stroke="var(--line)" stroke-width="1"
              />
              <text
                v-for="g in chart.gridLines"
                :key="'l' + g.y"
                :x="PAD.l - 8" :y="g.y + 3"
                text-anchor="end" font-size="9" fill="var(--text-muted)"
              >{{ g.label }}</text>
            </g>
            <!-- 折线 + 点 -->
            <template v-if="chart">
              <path :d="chart.linePath" fill="none" stroke="var(--vermillion)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />
              <circle
                v-for="(p, i) in chart.points"
                :key="i" :cx="p.x" :cy="p.y" r="3"
                fill="var(--card)" stroke="var(--vermillion)" stroke-width="2"
              />
              <!-- hover 热区 -->
              <rect
                v-for="(p, i) in chart.points"
                :key="'h' + i"
                :x="p.x - chart.step / 2" :y="PAD.t" :width="chart.step" :height="H - PAD.t - PAD.b"
                fill="transparent"
                @mouseenter="hoverIdx = i"
              />
              <!-- hover 竖线 -->
              <line
                v-if="hoverIdx >= 0 && chart.points[hoverIdx]"
                :x1="chart.points[hoverIdx].x" :y1="PAD.t"
                :x2="chart.points[hoverIdx].x" :y2="H - PAD.b"
                stroke="var(--line-strong)" stroke-width="1" stroke-dasharray="3 3"
              />
              <!-- x 轴日期 -->
              <text
                v-for="(p, i) in chart.points"
                :key="'x' + i"
                :x="p.x" :y="H - 10" text-anchor="middle" font-size="9" fill="var(--text-muted)"
              >{{ String(p.date).slice(-5) }}</text>
            </template>
          </svg>
          <!-- tooltip -->
          <div v-if="hoverIdx >= 0 && chart && chart.points[hoverIdx]" class="trend-tip" :style="{ left: tipLeftSimple }">
            <div class="tip-date">{{ chart.points[hoverIdx].date }}</div>
            <div class="tip-val">{{ chart.points[hoverIdx].count }} 次</div>
          </div>
        </div>
      </div>

      <!-- 文档类型分布 -->
      <div class="card chart-card">
        <div class="chart-title">
          <svg width="18" height="18" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          文档类型分布
        </div>
        <div v-if="status.docTypes === 'failed'" class="chart-placeholder">
          <p>后端 /stat/doc-types 尚未返回数据</p>
          <button class="btn btn-secondary" @click="loadAll">重试</button>
        </div>
        <div v-else-if="status.docTypes === 'empty'" class="chart-placeholder">
          <p>暂无文档类型数据</p>
        </div>
        <template v-else>
          <div class="pie-wrap">
            <div class="pie" :style="pieStyle">
              <div class="pie-center">
                <div class="pie-total">{{ docTotal.toLocaleString() }}</div>
                <div class="pie-label">文档总数</div>
              </div>
            </div>
          </div>
          <div class="pie-legend">
            <div v-for="(d, i) in docTypes" :key="d.type" class="pie-item">
              <span class="pie-dot" :style="{ background: PIE_COLORS[i % PIE_COLORS.length] }"></span>
              <span class="pie-type">{{ d.type }}</span>
              <span class="pie-count">{{ d.count }}</span>
            </div>
          </div>
        </template>
      </div>
    </div>

    <div class="bottom-charts">
      <!-- 最近查询（演示数据，契约暂无此接口） -->
      <div class="card chart-card pad0">
        <div class="chart-head">
          <div class="chart-title">
            <svg width="18" height="18" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            最近查询
          </div>
          <span class="demo-tag">演示数据</span>
        </div>
        <div class="query-list">
          <div v-for="q in recentQueries" :key="q.query" class="query-row">
            <div class="query-text">“{{ q.query }}”</div>
            <div class="query-meta">
              <span class="kb-pill">{{ q.kbName }}</span>
              <span class="query-time">
                <svg width="12" height="12" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {{ q.time }} · {{ q.tookMs }}ms
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 热门查询排行（/stat/hot，进度条 + tooltip） -->
      <div class="card chart-card pad0">
        <div class="chart-head">
          <div class="chart-title">
            <svg width="18" height="18" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            热门查询
          </div>
          <span class="demo-tag" v-if="status.hot === 'ok'">Top {{ hot.length }}</span>
        </div>
        <div v-if="status.hot === 'failed'" class="chart-placeholder pad">
          <p>后端 /stat/hot 尚未返回数据</p>
          <button class="btn btn-secondary" @click="loadAll">重试</button>
        </div>
        <div v-else-if="status.hot === 'empty'" class="chart-placeholder pad">
          <p>暂无查询数据</p>
        </div>
        <div v-else class="hot-list">
          <div
            v-for="(h, i) in hot"
            :key="h.query"
            class="hot-row"
            @mouseenter="hotTipIdx = i"
            @mouseleave="hotTipIdx = -1"
          >
            <span class="hot-rank">{{ String(i + 1).padStart(2, '0') }}</span>
            <div class="hot-main">
              <div class="hot-head">
                <span class="hot-name" :title="h.query">{{ h.query }}</span>
                <span class="hot-count">{{ h.count }} 次</span>
              </div>
              <div class="pop-bar"><div class="pop-fill" :style="{ width: hotWidth(h.count) }"></div></div>
            </div>
            <div v-if="hotTipIdx === i" class="hot-tip">{{ h.count }} 次</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--sp-comfortable);
  flex-wrap: wrap;
  gap: 16px;
}
.head-actions {
  display: flex;
  gap: 8px;
}
.page-title {
  font-size: 39px;
  margin-bottom: 0;
}

/* 统计卡（深色带，Velar 近黑段） */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--sp-comfortable);
  margin-bottom: var(--sp-comfortable);
}
.stat-card {
  background: var(--dark-bg);
  border-color: #2a2a2a;
  color: var(--dark-fg);
  box-shadow: 0 10px 32px rgba(0, 0, 0, 0.22);
  animation: cardIn 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
}
.stat-card:nth-child(1) { animation-delay: 0.04s; }
.stat-card:nth-child(2) { animation-delay: 0.12s; }
.stat-card:nth-child(3) { animation-delay: 0.2s; }
.stat-card:nth-child(4) { animation-delay: 0.28s; }
.stat-card:hover {
  box-shadow: 0 16px 44px rgba(0, 0, 0, 0.3);
}
.stat-label {
  font-size: 12px;
  color: rgba(232, 228, 223, 0.55);
  margin-bottom: 8px;
}
.stat-change {
  font-size: 11px;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  color: rgba(232, 228, 223, 0.45);
}
.live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #57b889;
  display: inline-block;
}
.stat-value {
  font-family: 'Syne', 'Inter', sans-serif;
  font-size: clamp(30px, 3.2vw, 46px);
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.12;
  font-variant-numeric: tabular-nums;
}
.stats-fallback {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  gap: 12px;
}
.stats-retry {
  text-align: center;
  color: rgba(232, 228, 223, 0.55);
  font-size: 13px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  align-items: center;
}
.stats-retry .btn {
  border-color: rgba(232, 228, 223, 0.3);
  color: var(--dark-fg);
}

/* 图表区 */
.charts-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--sp-comfortable);
  margin-bottom: var(--sp-comfortable);
}
.bottom-charts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sp-comfortable);
}
.chart-card {
  padding: var(--sp-comfortable);
}
.chart-card.pad0 {
  padding: 0;
}
.chart-title {
  font-size: 16px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  color: var(--ink);
}
.chart-title svg {
  color: var(--vermillion);
}

/* 占位（接口未就绪/空数据） */
.chart-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 64px 16px;
  color: var(--text-muted);
  font-size: 13px;
  text-align: center;
  border: 1px dashed var(--line);
  border-radius: var(--input-radius);
  min-height: 160px;
}
.chart-placeholder.pad {
  margin: 16px;
}

/* 折线图 */
.trend-box {
  position: relative;
}
.trend-svg {
  width: 100%;
  height: auto;
  display: block;
}
.trend-tip {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  background: var(--ink);
  color: var(--card);
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 11px;
  line-height: 1.4;
  pointer-events: none;
  white-space: nowrap;
  z-index: 5;
}
.tip-date {
  opacity: 0.7;
}
.tip-val {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

/* 环形图 */
.pie-wrap {
  display: flex;
  justify-content: center;
  margin: 16px 0 32px;
}
.pie {
  width: 180px;
  height: 180px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.pie-center {
  width: 132px;
  height: 132px;
  border-radius: 50%;
  background: var(--card);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}
.pie-total {
  font-size: 25px;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.pie-label {
  font-size: 12px;
  color: var(--text-muted);
}
.pie-legend {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.pie-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: var(--ink);
}
.pie-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 8px;
  display: inline-block;
}
.pie-type {
  flex: 1;
}
.pie-count {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

/* 最近查询 / 热门查询 */
.chart-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--line);
}
.chart-head .chart-title {
  margin-bottom: 0;
}
.demo-tag {
  font-size: 10px;
  color: var(--text-muted);
  background: var(--paper-2);
  border: 1px solid var(--line);
  padding: 2px 8px;
  border-radius: 999px;
}
.query-row {
  padding: 16px;
  border-bottom: 1px solid var(--line);
  cursor: pointer;
  transition: background 0.2s;
}
.query-row:last-child {
  border-bottom: none;
}
.query-row:hover {
  background: var(--paper-2);
}
.query-text {
  font-weight: 600;
  margin-bottom: 4px;
}
.query-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: var(--text-muted);
}
.kb-pill {
  background: rgba(33, 49, 56, 0.08);
  color: var(--vermillion);
  padding: 2px 6px;
  border-radius: 999px;
  font-size: 10px;
}
.query-time {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.hot-list {
  padding: 16px;
  position: relative;
}
.hot-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
  position: relative;
}
.hot-row:last-child {
  margin-bottom: 0;
}
.hot-rank {
  font-family: 'Syne', 'Inter', sans-serif;
  font-size: 13px;
  font-weight: 800;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
  width: 24px;
  flex-shrink: 0;
}
.hot-main {
  flex: 1;
  min-width: 0;
}
.hot-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  font-size: 12px;
}
.hot-name {
  font-weight: 600;
  max-width: 70%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.hot-count {
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}
.pop-bar {
  height: 4px;
  background: var(--paper-2);
  border-radius: 2px;
  overflow: hidden;
}
.pop-fill {
  height: 100%;
  background: var(--vermillion);
  border-radius: 2px;
  transition: width 0.5s;
}
.hot-tip {
  position: absolute;
  right: 0;
  top: -8px;
  transform: translateY(-100%);
  background: var(--ink);
  color: var(--card);
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  pointer-events: none;
  white-space: nowrap;
  z-index: 5;
}

/* 响应式 */
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .charts-row,
  .bottom-charts {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
