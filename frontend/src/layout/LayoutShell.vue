<script setup lang="ts">
// 布局壳：侧边栏 240px + 顶栏 56px（照美化版原型）
import { onBeforeUnmount, onMounted, ref } from 'vue'
import Sidebar from './Sidebar.vue'
import Topbar from './Topbar.vue'

const mobileOpen = ref(false)

function toggleMobileMenu() {
  mobileOpen.value = !mobileOpen.value
}

function handleResize() {
  if (window.innerWidth > 1024) mobileOpen.value = false
}

onMounted(() => window.addEventListener('resize', handleResize))
onBeforeUnmount(() => window.removeEventListener('resize', handleResize))
</script>

<template>
  <div class="layout" :class="{ 'mobile-open': mobileOpen }">
    <button class="menu-toggle" aria-label="菜单" @click="toggleMobileMenu">
      <svg width="24" height="24" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
        <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
      </svg>
    </button>
    <Sidebar @close-mobile="mobileOpen = false" />
    <main id="main-content">
      <Topbar />
      <div id="content-area">
        <router-view v-slot="{ Component }">
          <component :is="Component" class="page-enter" />
        </router-view>
      </div>
    </main>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
}
#main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-left: var(--sidebar-w);
  transition: margin 0.3s ease;
  min-height: 100vh;
}
#content-area {
  flex: 1;
  overflow-y: auto;
  padding: var(--sp-comfortable);
}
.menu-toggle {
  display: none;
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  color: var(--text-muted);
  position: fixed;
  top: 8px;
  left: 8px;
  z-index: 100;
}

@media (max-width: 1024px) {
  .layout:not(.mobile-open) #main-content {
    margin-left: 0;
  }
  .menu-toggle {
    display: block;
  }
}
@media (max-width: 768px) {
  #content-area {
    padding: var(--sp-snug);
  }
}
</style>
