#!/usr/bin/env node
/**
 * T3.1 前端壳子验收截图脚本（playwright-core + 系统 Edge，无头）
 * 流程：登录页（浅色）→ 登录 admin/admin123 → 聊天页 → 深色切换 → 各路由页
 * 用法：node docs/verify/shot_t3.mjs [--headed]
 * 截图输出：docs/verify/shots/
 */
import { chromium } from 'playwright-core'
import { mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const OUT = join(__dirname, '..', '..', 'docs', 'verify', 'shots')
const EDGE = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
const BASE = 'http://localhost:5173'
const headed = process.argv.includes('--headed')

mkdirSync(OUT, { recursive: true })

const browser = await chromium.launch({
  executablePath: EDGE,
  headless: !headed,
})
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
const errors = []
page.on('console', (m) => {
  if (m.type() === 'error') errors.push(m.text())
})
page.on('pageerror', (e) => errors.push(String(e)))

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

// 1. 登录页（浅色，等待 preloader 升起）
await page.goto(`${BASE}/login`, { waitUntil: 'networkidle' })
await sleep(4200) // preloader 约 3.4s
await page.screenshot({ path: join(OUT, 't3.1-login-light.png'), fullPage: false })

// 2. 演示账号登录
await page.fill('input[placeholder="请输入用户名"]', 'admin')
await page.fill('input[placeholder="请输入密码"]', 'admin123')
await page.click('button.submit-btn')
await page.waitForURL('**/chat', { timeout: 10000 })
await sleep(800)
await page.screenshot({ path: join(OUT, 't3.1-chat-shell.png') })

// 3. 深色切换
await page.click('button[title="切换主题"]')
await sleep(600)
await page.screenshot({ path: join(OUT, 't3.1-chat-dark.png') })

// 4. 其余路由（SPA 内点击导航，避免整页 reload 重播 preloader）
for (const [label, name] of [
  ['文档管理', 'documents'],
  ['知识库', 'kb'],
  ['分析看板', 'analytics'],
]) {
  await page.click(`.nav-item:has-text("${label}")`)
  await sleep(900)
  await page.screenshot({ path: join(OUT, `t3.1-${name}-dark.png`) })
}

// 5. 切回浅色后回聊天页
await page.click('button[title="切换主题"]')
await sleep(400)
await page.click('.nav-item:has-text("智能问答")')
await sleep(600)
await page.screenshot({ path: join(OUT, 't3.1-chat-light.png') })

await browser.close()

console.log('console/page errors:', errors.length ? errors.slice(0, 10) : '无')
console.log('截图输出:', OUT)
