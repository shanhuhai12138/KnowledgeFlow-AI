<script setup lang="ts">
// 顶栏：面包屑 + 全局搜索 + 深浅色切换 + 通知 + 头像下拉（照任务书 T3.1）
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElDropdown, ElDropdownMenu, ElDropdownItem, ElMessage } from 'element-plus'
import { useThemeStore } from '@/stores/theme'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const theme = useThemeStore()
const auth = useAuthStore()

const title = computed(() => (route.meta.title as string) || '智能问答')
const searchText = ref('')

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
      <span>首页</span><span class="sep">/</span><span class="cur">{{ title }}</span>
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

      <button class="btn-icon plain" title="通知" @click="ElMessage.info('暂无新通知')">
        <svg width="20" height="20" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
      </button>

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
  height: var(--topbar-h);
  border-bottom: 1px solid var(--line);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
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
.topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: var(--input-radius);
  padding: 7px 12px;
  color: var(--text-muted);
  width: 220px;
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
  font-size: 13px;
  color: var(--ink);
}
.search-input::placeholder {
  color: var(--text-muted);
}
.btn-icon.plain {
  border: none;
}
.avatar-btn {
  width: 34px;
  height: 34px;
  border-radius: 6px;
  background: var(--btn-solid);
  color: #fff;
  border: none;
  cursor: pointer;
  font-weight: 700;
  font-size: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
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
