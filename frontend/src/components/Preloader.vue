<script setup lang="ts">
// 电影感预加载器：Syne 字标逐字浮现 → 整体上滑离场（照美化版原型逻辑迁移）
import { onMounted, ref } from 'vue'

const show = ref(true)
const lifted = ref(false)

const CHAR = 110
const START = 500
const EXTRA = 650

let timers: number[] = []

onMounted(() => {
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (reduced) {
    show.value = false
    document.body.classList.add('ready')
    return
  }
  const letters = 'KnowledgeFlow.'.split('')
  const LIFT_AT = START + letters.length * CHAR + EXTRA
  letters.forEach((_, i) => {
    timers.push(
      window.setTimeout(() => {
        const el = document.getElementById(`pl-${i}`)
        if (el) el.style.opacity = '1'
      }, START + i * CHAR),
    )
  })
  timers.push(
    window.setTimeout(() => {
      lifted.value = true
      document.body.classList.add('ready')
    }, LIFT_AT),
  )
  timers.push(window.setTimeout(() => (show.value = false), LIFT_AT + 1900))
})
</script>

<template>
  <div
    v-if="show"
    id="preloader"
    class="preloader"
    :class="{ lifted }"
    aria-hidden="true"
  >
    <div id="preloader-text">
      <span class="w">
        <template v-for="(ch, i) in 'KnowledgeFlow.'.split('')" :key="i">
          <span :id="`pl-${i}`" :class="{ pd: ch === '.' }">{{ ch }}</span>
        </template>
      </span>
      <span id="preloader-cursor"></span>
    </div>
    <div class="preloader-sign" aria-hidden="true">- by shanhuhai12138</div>
  </div>
</template>

<style scoped>
.preloader {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: #213138;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 1.5s cubic-bezier(0.45, 0, 0.15, 1);
}
.preloader.lifted {
  transform: translateY(-100%);
}
#preloader-text {
  display: flex;
  align-items: center;
  font-family: 'Syne', sans-serif;
  font-size: 2.6rem;
  color: #fff;
  letter-spacing: -0.02em;
  line-height: 1;
}
#preloader-text .w span {
  opacity: 0;
  transition: opacity 0.15s ease;
  font-weight: 700;
}
#preloader-text .w span.pd {
  font-weight: 900;
}
#preloader-cursor {
  display: inline-block;
  width: 3px;
  height: 1.1em;
  border-radius: 999px;
  background: #fff;
  margin-left: 3px;
  animation: blink 0.7s step-end infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
.preloader-sign {
  position: absolute;
  right: 28px;
  bottom: 20px;
  font-family: 'Syne', 'Inter', sans-serif;
  font-size: 12px;
  letter-spacing: 0.08em;
  color: rgba(245, 240, 234, 0.55);
  transition: opacity 0.4s ease;
  user-select: none;
}
.preloader.lifted .preloader-sign {
  opacity: 0;
}
</style>
