<script setup lang="ts">
// AI 设置页（FR-11 / DR-13）：API Key 永不明文回显；保存/清除/测试连接
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAiConfig, saveAiConfig, type AiConfig } from '@/api/aiConfig'
import { chatApi } from '@/api/chat'
import { getKbPageApi } from '@/api/kb'

const loading = ref(true)
const forbidden = ref(false)
const saving = ref(false)
const testing = ref(false)
const config = ref<AiConfig | null>(null)

const form = reactive({
  apiKey: '',
  baseUrl: 'https://api.deepseek.com',
  model: 'deepseek-chat',
})

async function load() {
  loading.value = true
  forbidden.value = false
  const res = await getAiConfig()
  if (res.forbidden) {
    forbidden.value = true
  } else if (res.ok && res.data) {
    config.value = res.data
    form.baseUrl = res.data.baseUrl || 'https://api.deepseek.com'
    form.model = res.data.model || 'deepseek-chat'
  }
  loading.value = false
}

async function doSave() {
  if (!form.baseUrl.trim()) {
    ElMessage.warning('请输入 Base URL')
    return
  }
  if (!form.model.trim()) {
    ElMessage.warning('请输入模型名')
    return
  }
  saving.value = true
  try {
    const key = form.apiKey.trim()
    const res = await saveAiConfig({
      apiKey: key || undefined, // 空 = 保留现有 Key（清除走单独按钮）
      baseUrl: form.baseUrl.trim(),
      model: form.model.trim(),
    })
    if (res.forbidden) {
      forbidden.value = true
      ElMessage.warning('无权限：仅超级管理员可修改 AI 配置')
      return
    }
    if (res.ok) {
      ElMessage.success(key ? '配置已保存' : '配置已更新（Key 保持不变）')
      form.apiKey = ''
      await load()
    } else {
      ElMessage.error(res.message || '保存失败')
    }
  } finally {
    saving.value = false
  }
}

async function doClear() {
  try {
    await ElMessageBox.confirm('确定清除已保存的 API Key？清除后问答将无法调用 LLM。', '清除 API Key', {
      confirmButtonText: '清除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  saving.value = true
  try {
    const res = await saveAiConfig({ apiKey: '', baseUrl: form.baseUrl.trim(), model: form.model.trim() })
    if (res.ok) {
      ElMessage.success('API Key 已清除')
      form.apiKey = ''
      await load()
    } else if (res.forbidden) {
      ElMessage.warning('无权限：仅超级管理员可修改 AI 配置')
    } else {
      ElMessage.error(res.message || '清除失败')
    }
  } finally {
    saving.value = false
  }
}

async function doTest() {
  testing.value = true
  try {
    // 取任一可见知识库 id（chatApi 需 kbId，否则后端 400「知识库编号不能为空」）
    let kbId = 1
    const kbRes = await getKbPageApi({ pageNo: 1, pageSize: 1 })
    if (kbRes?.list?.length) {
      kbId = kbRes.list[0].id
    }
    const res = await chatApi({ sessionId: 'conn-test', kbId, message: '请回复：连接正常' })
    if (res?.content) {
      ElMessage.success('连接正常，模型已响应')
    } else {
      ElMessage.warning('连接可用，但模型未返回内容')
    }
  } catch (e) {
    ElMessage.error(`连接失败：${(e as Error)?.message || '未知错误'}`)
  } finally {
    testing.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="ai-settings-page page-enter">
    <div class="page-head">
      <div>
        <h1 class="serif page-title">AI 设置</h1>
        <p class="page-sub">配置模型 API Key 与接口地址，部署者开箱即用；Key 经加密存储，永不明文回显。</p>
      </div>
    </div>

    <!-- 无权限 -->
    <div v-if="forbidden" class="card no-perm">
      <div class="no-perm-icon">
        <svg width="28" height="28" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      </div>
      <h3 class="serif">无权限访问</h3>
      <p>AI 配置仅超级管理员可用，如需配置请联系管理员。</p>
      <button class="btn btn-secondary" @click="load">重试</button>
    </div>

    <!-- 加载中 -->
    <div v-else-if="loading" class="card loading-card">加载配置中…</div>

    <!-- 表单 -->
    <div v-else class="card settings-card">
      <div class="section">
        <label class="form-label">API Key</label>
        <input v-model="form.apiKey" type="password" class="form-input" placeholder="留空则保留当前 Key" autocomplete="new-password" />
        <p class="field-hint">
          <template v-if="config?.hasKey">当前已配置：<span class="masked">{{ config.maskedKey }}</span>（仅显示掩码）</template>
          <template v-else>尚未配置 Key，问答将无法调用 LLM</template>
        </p>
      </div>

      <div class="section">
        <label class="form-label">Base URL</label>
        <input v-model="form.baseUrl" class="form-input" placeholder="https://api.deepseek.com" />
      </div>

      <div class="section">
        <label class="form-label">模型名</label>
        <input v-model="form.model" class="form-input" placeholder="deepseek-chat" />
        <p class="field-hint">默认 deepseek-chat；当前后端配置为 {{ config?.model || '—' }}</p>
      </div>

      <div class="actions">
        <button class="btn btn-primary" :disabled="saving" @click="doSave">
          {{ saving ? '保存中…' : '保存' }}
        </button>
        <button class="btn btn-secondary" :disabled="saving || !config?.hasKey" @click="doClear">
          清除 Key
        </button>
        <button class="btn btn-secondary" :disabled="testing" @click="doTest">
          {{ testing ? '测试中…' : '测试连接' }}
        </button>
      </div>
      <p class="foot-note">清除 Key 后建议点击「测试连接」确认链路；保存后无需重启服务。</p>
    </div>
  </div>
</template>

<style scoped>
.page-head {
  margin-bottom: var(--sp-comfortable);
}
.page-title {
  font-size: 39px;
  margin-bottom: 8px;
}
.page-sub {
  color: var(--text-muted);
}
.loading-card {
  color: var(--text-muted);
  text-align: center;
  padding: 64px;
}
.settings-card {
  max-width: 560px;
  padding: var(--sp-comfortable);
}
.section {
  margin-bottom: var(--sp-base);
}
.field-hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-muted);
}
.masked {
  font-family: 'JetBrains Mono', Consolas, monospace;
  background: var(--paper-2);
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 1px 6px;
  color: var(--ink);
}
.actions {
  display: flex;
  gap: 12px;
  margin-top: var(--sp-comfortable);
  border-top: 1px solid var(--line);
  padding-top: var(--sp-base);
}
.foot-note {
  margin-top: var(--sp-snug);
  font-size: 11px;
  color: var(--text-muted);
}
.no-perm {
  max-width: 560px;
  text-align: center;
  padding: 64px var(--sp-comfortable);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.no-perm-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: rgba(33, 49, 56, 0.08);
  color: var(--vermillion);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}
.no-perm h3 {
  font-size: 20px;
}
.no-perm p {
  color: var(--text-muted);
  font-size: 13px;
  margin-bottom: 8px;
}
</style>
