<script setup lang="ts">
// 侧边栏：品牌带 + 导航四页 + 知识库快捷列表 + 底部用户卡/退出（照美化版原型）
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getKbPageApi } from '@/api/kb'
import { useAuthStore } from '@/stores/auth'
import type { KnowledgeBase } from '@/types'

const emit = defineEmits<{ (e: 'close-mobile'): void }>()

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const navs = [
  { key: 'chat', label: '智能问答', icon: 'chat' },
  { key: 'documents', label: '文档管理', icon: 'doc' },
  { key: 'kb', label: '知识库', icon: 'kb' },
  { key: 'analytics', label: '分析看板', icon: 'chart' },
] as const

const kbs = ref<KnowledgeBase[]>([])

async function loadKbs() {
  try {
    const data = await getKbPageApi({ pageNo: 1, pageSize: 8 })
    kbs.value = data?.list || []
  } catch {
    kbs.value = []
  }
}

onMounted(loadKbs)

function go(path: string) {
  router.push(path)
  emit('close-mobile')
}

function goKbChat(kb: KnowledgeBase) {
  router.push({ path: '/chat', query: { kbId: String(kb.id), kbName: kb.name } })
  emit('close-mobile')
}

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <aside id="sidebar" class="sidebar">
    <!-- 深青品牌带 -->
    <div class="brand-band">
      <div class="brand brand-logo">KnowledgeFlow<span class="pd">.</span></div>
      <div class="brand-sub">企业级智能知识库</div>
    </div>

    <!-- 导航 -->
    <nav class="nav">
      <div
        v-for="n in navs"
        :key="n.key"
        class="nav-item"
        :class="{ active: route.path === `/${n.key}` || (n.key === 'chat' && route.path === '/') }"
        @click="go(`/${n.key}`)"
      >
        <svg v-if="n.icon === 'chat'" width="20" height="20" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <svg v-else-if="n.icon === 'doc'" width="20" height="20" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <svg v-else-if="n.icon === 'kb'" width="20" height="20" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
        </svg>
        <svg v-else width="20" height="20" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <span>{{ n.label }}</span>
      </div>
    </nav>

    <!-- 知识库快捷列表 -->
    <div class="kb-quick">
      <div class="kb-quick-title">知识库</div>
      <div v-if="kbs.length" class="kb-quick-list">
        <div v-for="kb in kbs" :key="kb.id" class="kb-quick-item" :title="kb.name" @click="goKbChat(kb)">
          <span class="kb-dot" :class="{ private: kb.isPrivate }"></span>
          <span class="kb-name">{{ kb.name }}</span>
          <span class="kb-count">{{ kb.documentCount }}</span>
        </div>
      </div>
      <div v-else class="kb-quick-empty">暂无知识库</div>
    </div>

    <!-- 用户卡 + 退出 -->
    <div class="user-band">
      <div class="user-row">
        <div class="avatar">{{ auth.displayName.slice(0, 1).toUpperCase() }}</div>
        <div class="user-meta">
          <div class="user-name">{{ auth.displayName }}</div>
          <div class="user-role">系统管理员</div>
        </div>
      </div>
      <button class="btn btn-secondary logout-btn" @click="logout">退出登录</button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: var(--sidebar-w);
  background: var(--paper-2);
  border-right: 1px solid var(--line);
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 55;
  transition: transform 0.3s ease;
}
/* 深青品牌带（Velar 配色，深浅色模式均固定） */
.brand-band {
  padding: var(--sp-comfortable);
  border-bottom: 1px solid var(--line);
  background: #213138;
  color: #f5f0ea;
  overflow: hidden;
  min-width: 0;
  flex-shrink: 0;
}
.brand-logo {
  font-size: 23px;
  color: #f5f0ea;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.brand-sub {
  font-size: 12px;
  color: rgba(245, 240, 234, 0.62);
  margin-top: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav {
  flex: 0 0 auto;
  padding: 12px 0;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  cursor: pointer;
  border-right: 3px solid transparent;
  transition: all 0.2s;
  font-weight: 500;
}
.nav-item:hover {
  background: color-mix(in oklab, var(--vermillion) 8%, transparent);
}
.nav-item.active {
  border-right-color: var(--vermillion);
  color: var(--vermillion);
}

.kb-quick {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
  border-top: 1px solid var(--line);
  margin-top: 8px;
}
.kb-quick-title {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text-muted);
  padding: 0 24px 8px;
}
.kb-quick-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 24px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-muted);
  transition: background 0.15s, color 0.15s;
}
.kb-quick-item:hover {
  background: color-mix(in oklab, var(--vermillion) 8%, transparent);
  color: var(--ink);
}
.kb-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--vermillion);
  flex-shrink: 0;
}
.kb-dot.private {
  background: var(--gold);
}
.kb-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.kb-count {
  font-size: 11px;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}
.kb-quick-empty {
  padding: 0 24px;
  font-size: 12px;
  color: var(--text-muted);
}

.user-band {
  padding: var(--sp-comfortable);
  border-top: 1px solid var(--line);
}
.user-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.avatar {
  width: 40px;
  height: 40px;
  border-radius: 6px;
  background: var(--btn-solid);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}
.user-name {
  font-weight: 600;
  line-height: 1.3;
}
.user-role {
  font-size: 12px;
  color: var(--text-muted);
}
.logout-btn {
  width: 100%;
  padding: 12px;
}

@media (max-width: 1024px) {
  .sidebar {
    transform: translateX(-100%);
  }
  .layout.mobile-open .sidebar {
    transform: translateX(0);
  }
}
</style>
