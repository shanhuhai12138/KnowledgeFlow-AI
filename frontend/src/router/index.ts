import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true, title: '登录' },
    },
    {
      path: '/',
      component: () => import('@/layout/LayoutShell.vue'),
      redirect: '/chat',
      children: [
        { path: 'chat', name: 'chat', component: () => import('@/views/ChatView.vue'), meta: { title: '智能问答' } },
        { path: 'documents', name: 'documents', component: () => import('@/views/DocumentsView.vue'), meta: { title: '文档管理' } },
        { path: 'kb', name: 'kb', component: () => import('@/views/KbView.vue'), meta: { title: '知识库管理' } },
        { path: 'analytics', name: 'analytics', component: () => import('@/views/AnalyticsView.vue'), meta: { title: '分析看板' } },
        { path: 'settings/ai', name: 'ai-settings', component: () => import('@/views/AiSettingsView.vue'), meta: { title: 'AI 设置' } },
        { path: 'profile', name: 'profile', component: () => import('@/views/ProfileView.vue'), meta: { title: '个人中心' } },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/chat' },
  ],
})

// 路由守卫：无 token 跳登录；已登录访问 /login 跳 /chat
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isLoggedIn) return { path: '/login', query: { redirect: to.fullPath } }
  if (to.path === '/login' && auth.isLoggedIn) return '/chat'
  return true
})

router.afterEach((to) => {
  const title = (to.meta.title as string) || ''
  document.title = title ? `${title} · KnowledgeFlow AI` : 'KnowledgeFlow AI - 企业级智能知识库'
})

export default router
