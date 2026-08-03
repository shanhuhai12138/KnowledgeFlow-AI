<script setup lang="ts">
// 登录页：双栏（品牌区 + 表单），登录/注册切换、演示账号、登录 loading（照美化版原型）
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { registerApi } from '@/api/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const mode = ref<'login' | 'register'>('login')
const username = ref('')
const password = ref('')
const email = ref('')
const remember = ref(true)
const loading = ref(false)

function switchAuth(login: boolean) {
  mode.value = login ? 'login' : 'register'
}

function fillDemo() {
  username.value = 'admin'
  password.value = 'admin123'
  doSubmit()
}

async function doSubmit() {
  const u = username.value.trim()
  if (!u) {
    ElMessage.warning('请输入用户名')
    return
  }
  if (!password.value) {
    ElMessage.warning('请输入密码')
    return
  }
  loading.value = true
  try {
    if (mode.value === 'login') {
      await auth.login(u, password.value)
    } else {
      // 注册成功一般返回 token 或需重新登录
      await registerApi(u, password.value, u)
      await auth.login(u, password.value)
    }
    ElMessage.success('欢迎回来')
    const redirect = (route.query.redirect as string) || '/chat'
    router.push(redirect)
  } catch (e) {
    const msg = (e as Error)?.message || '登录失败，请检查账号密码'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // 若已登录（如 token 残留），直接进入
  if (auth.isLoggedIn) router.replace('/chat')
})
</script>

<template>
  <div id="login-page" class="page-enter">
    <div class="login-wrap">
      <!-- 左：品牌区 -->
      <div class="login-panel">
        <div class="top-accent"></div>
        <div class="login-eyebrow brand">KNOWLEDGEFLOW<span class="pd">.</span></div>
        <h1 class="serif login-headline">让企业知识<br />开口说话</h1>
        <p class="login-sub">基于自有知识库的精准问答 · 全生命周期管理 · 数据安全隔离</p>
        <div class="login-features">
          <div class="card card-hover f-card">
            <div class="f-title">RAG智能问答</div>
            <div class="f-desc">基于自有知识库的精准回答</div>
          </div>
          <div class="card card-hover f-card">
            <div class="f-title">自动化管理</div>
            <div class="f-desc">文档上传、解析、索引自动化</div>
          </div>
          <div class="card card-hover f-card">
            <div class="f-title">数据分析看板</div>
            <div class="f-desc">洞察知识使用频率与热度</div>
          </div>
          <div class="card card-hover f-card">
            <div class="f-title">多租户隔离</div>
            <div class="f-desc">严谨的权限与多租户隔离</div>
          </div>
        </div>
      </div>

      <!-- 右：表单 -->
      <div class="login-form-side">
        <div class="card login-form-card">
          <div class="auth-tabs">
            <button class="auth-tab" :class="{ active: mode === 'login' }" @click="switchAuth(true)">
              登录
              <div v-if="mode === 'login'" class="tab-indicator"></div>
            </button>
            <button class="auth-tab" :class="{ active: mode === 'register' }" @click="switchAuth(false)">
              注册
              <div v-if="mode === 'register'" class="tab-indicator"></div>
            </button>
          </div>

          <form @submit.prevent="doSubmit">
            <div class="field">
              <label class="form-label">用户名</label>
              <input v-model="username" class="form-input" placeholder="请输入用户名" required autocomplete="username" />
            </div>
            <div v-if="mode === 'register'" class="field">
              <label class="form-label">邮箱地址</label>
              <input v-model="email" class="form-input" type="email" placeholder="example@corp.com" />
            </div>
            <div class="field">
              <label class="form-label">密码</label>
              <input v-model="password" class="form-input" type="password" placeholder="请输入密码" required autocomplete="current-password" />
            </div>
            <div v-if="mode === 'login'" class="login-options">
              <label class="remember"><input v-model="remember" type="checkbox" /> 记住我</label>
              <a href="#" @click.prevent="ElMessage.info('功能演示中')">忘记密码？</a>
            </div>
            <button type="submit" class="btn btn-primary submit-btn" :disabled="loading">
              {{ loading ? (mode === 'login' ? '登录中...' : '注册中...') : mode === 'login' ? '登录' : '注册' }}
            </button>
            <button v-if="mode === 'login'" type="button" class="btn btn-secondary demo-btn" :disabled="loading" @click="fillDemo">
              体验账号一键填充 (admin / admin123)
            </button>
          </form>

          <p class="copyright">© 2026 KnowledgeFlow AI · 企业级智能知识库</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-wrap {
  display: flex;
  min-height: 100vh;
}
/* 左品牌区 */
.login-panel {
  width: 45%;
  background: var(--paper-2);
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: var(--sp-loose);
  position: relative;
}
.top-accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, var(--vermillion), transparent);
}
.login-eyebrow {
  font-family: 'Syne', sans-serif;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  color: var(--vermillion);
  margin-bottom: 18px;
  opacity: 0;
}
body.ready .login-eyebrow {
  animation: rise 0.6s cubic-bezier(0.22, 1, 0.36, 1) 0.05s both;
}
.login-headline {
  font-size: 48px;
  font-weight: 900;
  line-height: 1.05;
  letter-spacing: -0.02em;
  margin-bottom: var(--sp-comfortable);
  opacity: 0;
}
body.ready .login-headline {
  animation: rise 0.7s cubic-bezier(0.22, 1, 0.36, 1) 0.12s both;
}
.login-sub {
  font-size: 20px;
  color: var(--text-muted);
  margin-bottom: var(--sp-loose);
  line-height: 1.6;
  opacity: 0;
}
body.ready .login-sub {
  animation: rise 0.7s cubic-bezier(0.22, 1, 0.36, 1) 0.2s both;
}
.login-features {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--sp-base);
  margin-top: var(--sp-loose);
}
.login-features > .f-card {
  opacity: 0;
}
body.ready .login-features > .f-card {
  animation: rise 0.7s cubic-bezier(0.22, 1, 0.36, 1) both;
}
body.ready .login-features > .f-card:nth-child(1) { animation-delay: 0.3s; }
body.ready .login-features > .f-card:nth-child(2) { animation-delay: 0.38s; }
body.ready .login-features > .f-card:nth-child(3) { animation-delay: 0.46s; }
body.ready .login-features > .f-card:nth-child(4) { animation-delay: 0.54s; }
.f-title {
  font-weight: 700;
  margin-bottom: 4px;
}
.f-desc {
  font-size: 12px;
  color: var(--text-muted);
}

/* 右表单区 */
.login-form-side {
  width: 55%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--sp-loose);
}
.login-form-card {
  width: 100%;
  max-width: 420px;
  opacity: 0;
}
body.ready .login-form-card {
  animation: rise 0.8s cubic-bezier(0.22, 1, 0.36, 1) 0.5s both;
}
.auth-tabs {
  display: flex;
  margin-bottom: var(--sp-comfortable);
  border-bottom: 1px solid var(--line);
}
.auth-tab {
  flex: 1;
  padding: 12px;
  text-align: center;
  cursor: pointer;
  border: none;
  background: none;
  color: var(--text-muted);
  font-weight: 600;
  position: relative;
  transition: color 0.2s;
}
.auth-tab.active {
  color: var(--ink);
}
.tab-indicator {
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--vermillion);
}
.field {
  margin-bottom: var(--sp-base);
}
.login-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--sp-comfortable);
  font-size: 12px;
  color: var(--text-muted);
}
.remember {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}
.remember input {
  accent-color: var(--vermillion);
}
.submit-btn {
  width: 100%;
  padding: 12px;
}
.demo-btn {
  width: 100%;
  margin-top: 12px;
  padding: 12px;
}
.copyright {
  margin-top: var(--sp-comfortable);
  text-align: center;
  font-size: 12px;
  color: var(--text-muted);
}

/* 响应式 */
@media (max-width: 768px) {
  .login-brand {
    display: none;
  }
  .login-wrap {
    flex-direction: column;
  }
  .login-panel {
    display: none;
  }
  .login-form-side {
    width: 100%;
  }
}
</style>
