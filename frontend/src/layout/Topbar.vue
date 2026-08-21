<script setup lang="ts">
// 顶栏：面包屑 + 全局搜索 + 深浅色切换 + 通知 + 头像下拉（照任务书 T3.1）
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElDropdown, ElDropdownMenu, ElDropdownItem } from 'element-plus'
import { useThemeStore } from '@/stores/theme'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const theme = useThemeStore()
const auth = useAuthStore()

const searchText = ref('')

// ---------- 导航菜单 ----------
const menuItems = [
  { key: 'chat', label: '问答', path: '/chat' },
  { key: 'agent', label: 'Agent', path: '/agent' },
  { key: 'documents', label: '文档', path: '/documents' },
  { key: 'kb', label: '库', path: '/kb' },
  { key: 'analytics', label: '看板', path: '/analytics' },
]

function isActive(path: string) {
  return route.path === path || (path === '/chat' && (route.path === '/' || route.path === ''))
}

// ---------- 通知 ----------
const notifVisible = ref(false)
const notifLoading = ref(false)
const notifications = ref<Array<{ id: number; type: 'doc' | 'member' | 'system'; title: string; content: string; time: string; read: boolean }>>([])
const unreadCount = ref(0)

async function loadNotifications() {
  notifLoading.value = true
  try {
    // 模拟通知数据（后端通知 API 待实现）
    await new Promise(r => setTimeout(r, 500))
    notifications.value = [
      { id: 1, type: 'doc', title: '文档处理完成', content: '「开发环境搭建SOP.md」已成功向量化', time: '10分钟前', read: false },
      { id: 2, type: 'member', title: '成员变更', content: 'admin 已将您添加为「技术文档库」成员', time: '1小时前', read: false },
      { id: 3, type: 'system', title: '系统更新', content: 'KnowledgeFlow AI v2.0 已发布', time: '2小时前', read: true },
    ]
    unreadCount.value = notifications.value.filter(n => !n.read).length
  } catch {
    notifications.value = []
  } finally {
    notifLoading.value = false
  }
}

function markRead(id: number) {
  const n = notifications.value.find(x => x.id === id)
  if (n) n.read = true
  unreadCount.value = notifications.value.filter(x => !x.read).length
}

function markAllRead() {
  notifications.value.forEach(n => n.read = true)
  unreadCount.value = 0
}

function removeNotif(id: number) {
  notifications.value = notifications.value.filter(n => n.id !== id)
  unreadCount.value = notifications.value.filter(n => !n.read).length
}

function getNotifIcon(type: string) {
  const icons: Record<string, string> = {
    doc: '📄',
    member: '👤',
    system: '⚙️',
  }
  return icons[type] || '🔔'
}

onMounted(loadNotifications)

function onSearch() {
  const kw = searchText.value.trim()
  router.push({ path: '/documents', query: kw ? { kw } : {} })
}

function onCommand(cmd: string) {
  if (cmd === 'profile') {
    router.push('/profile')
  } else if (cmd === 'settings') {
    router.push('/settings/ai')
  } else if (cmd === 'logout') {
    auth.logout()
    router.push('/login')
  }
}
</script>

<template>
  <header class="topbar">
    <!-- 编辑感渐变装饰线 -->
    <div class="topbar-accent"></div>
    <nav class="breadcrumb">
      <!-- 顶部导航菜单 -->
      <div class="top-nav">
        <button
          v-for="item in menuItems"
          :key="item.key"
          class="top-nav-item"
          :class="{ active: isActive(item.path) }"
          @click="router.push(item.path)"
        >
          {{ item.label }}
        </button>
      </div>
    </nav>
    <div class="topbar-right">
      <div class="search-box">
        <svg width="15" height="15" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          v-model="searchText"
          class="search-input"
          placeholder="全局搜索文档…"
          @keyup.enter="onSearch"
        />
      </div>

      <button class="btn-icon plain" title="切换主题" @click="theme.toggle()">
        <svg v-if="!theme.isDark" width="20" height="20" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
          <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
        <svg v-else width="20" height="20" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      </button>

      <button class="btn-icon plain" title="通知" @click="notifVisible = !notifVisible">
        <svg width="20" height="20" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        <span v-if="unreadCount > 0" class="notif-badge">{{ unreadCount > 9 ? '9+' : unreadCount }}</span>
      </button>

      <!-- 通知面板 -->
      <div v-if="notifVisible" class="notif-panel" @click.stop>
        <div class="notif-header">
          <span class="notif-title">通知</span>
          <button class="notif-clear" @click="markAllRead" :disabled="unreadCount === 0">全部已读</button>
        </div>
        <div class="notif-list">
          <div v-if="notifLoading" class="notif-loading">加载中…</div>
          <div v-else-if="!notifications.length" class="notif-empty">暂无通知</div>
          <div v-for="n in notifications" :key="n.id" class="notif-item" :class="{ read: n.read }" @click="markRead(n.id)">
            <div class="notif-icon">{{ getNotifIcon(n.type) }}</div>
            <div class="notif-body">
              <div class="notif-title-text">{{ n.title }}</div>
              <div class="notif-content">{{ n.content }}</div>
              <div class="notif-time">{{ n.time }}</div>
            </div>
            <button class="notif-del" @click="removeNotif(n.id)">✕</button>
          </div>
        </div>
        <div class="notif-footer">
          <button class="btn btn-secondary btn-full" @click="notifVisible = false">关闭</button>
        </div>
      </div>

      <el-dropdown trigger="click" @command="onCommand">
        <button class="avatar-btn" title="用户菜单">
          {{ auth.displayName.slice(0, 1).toUpperCase() }}
        </button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">个人中心</el-dropdown-item>
            <el-dropdown-item v-if="auth.isAdmin" command="settings">AI 设置</el-dropdown-item>
            <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<style scoped>
.topbar {
  position: relative;
  height: 48px;
  border-bottom: 1px solid var(--line);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: var(--paper);
  position: sticky;
  top: 0;
  z-index: 10;
  flex-shrink: 0;
}
.topbar-accent {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, var(--vermillion), transparent);
  opacity: 0.9;
}

/* ---------- 通知徽章 ---------- */
.notif-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  border-radius: 9px;
  background: var(--vermillion);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  line-height: 18px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

/* ---------- 通知面板 ---------- */
.notif-panel {
  position: absolute;
  top: calc(var(--topbar-h) - 4px);
  right: 80px;
  width: 360px;
  max-height: 480px;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
  display: flex;
  flex-direction: column;
  z-index: 100;
  overflow: hidden;
}

.notif-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--line);
}

.notif-header .notif-title {
  font-weight: 600;
  font-size: 15px;
  color: var(--ink);
}

.notif-clear {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 12px;
  color: var(--vermillion);
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.notif-clear:hover:not(:disabled) {
  background: color-mix(in oklab, var(--vermillion) 8%, transparent);
}

.notif-clear:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.notif-list {
  flex: 1;
  overflow-y: auto;
  min-height: 60px;
}

.notif-loading,
.notif-empty {
  padding: 32px 16px;
  text-align: center;
  color: var(--text-muted);
  font-size: 14px;
}

.notif-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--line);
  cursor: pointer;
  transition: background 0.15s;
}

.notif-item:hover {
  background: color-mix(in oklab, var(--vermillion) 4%, transparent);
}

.notif-item.read {
  opacity: 0.6;
}

.notif-icon {
  font-size: 20px;
  flex-shrink: 0;
  width: 28px;
  text-align: center;
}

.notif-body {
  flex: 1;
  min-width: 0;
}

.notif-title-text {
  font-weight: 500;
  font-size: 14px;
  color: var(--ink);
  margin-bottom: 4px;
}

.notif-content {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.4;
  margin-bottom: 6px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notif-time {
  font-size: 12px;
  color: var(--text-quiet);
}

.notif-del {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-muted);
  font-size: 14px;
  padding: 4px;
  border-radius: 4px;
  flex-shrink: 0;
  transition: all 0.15s;
}

.notif-del:hover {
  color: var(--vermillion);
  background: color-mix(in oklab, var(--vermillion) 10%, transparent);
}

.notif-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--line);
}

.btn-full {
  width: 100%;
}
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-muted);
}
.breadcrumb .cur {
  color: var(--ink);
  font-weight: 600;
}

/* ---------- 顶部导航菜单 ---------- */
.top-nav {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-right: auto;
}
.top-nav-item {
  padding: 4px 12px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-muted);
  border-radius: 4px;
  transition: all 0.2s;
  position: relative;
}
.top-nav-item:hover {
  color: var(--ink);
}
.top-nav-item.active {
  color: var(--vermillion);
  font-weight: 500;
}
.top-nav-item.active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 50%;
  transform: translateX(-50%);
  width: 16px;
  height: 2px;
  background: var(--vermillion);
  border-radius: 1px;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--input-radius);
  padding: 6px 10px;
  color: var(--text-muted);
  width: 160px;
  transition: border-color 0.2s;
}
.search-box:focus-within {
  border-color: var(--vermillion);
  box-shadow: 0 0 0 3px rgba(33, 49, 56, 0.08);
}
.search-input {
  border: none;
  background: none;
  outline: none;
  flex: 1;
  font-size: 12px;
  color: var(--ink);
}
.search-input::placeholder {
  color: var(--text-muted);
}
.btn-icon.plain {
  border: none;
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  background: none;
  cursor: pointer;
  color: var(--text-muted);
  transition: all 0.2s;
}
.btn-icon.plain:hover {
  background: color-mix(in oklab, var(--vermillion) 8%, transparent);
  color: var(--ink);
}
.avatar-btn {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: var(--btn-solid);
  color: #fff;
  border: none;
  cursor: pointer;
  font-weight: 700;
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.avatar-btn:hover {
  background: var(--btn-solid-2);
}

@media (max-width: 768px) {
  .topbar {
    padding: 0 16px;
  }
  .search-box {
    display: none;
  }
}
</style>
