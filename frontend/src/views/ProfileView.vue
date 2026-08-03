<script setup lang="ts">
// 个人中心：显示昵称/用户名，改昵称（含邮箱/手机），改密码
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { updatePasswordApi, updateProfileApi, type ProfileInfo } from '@/api/profile'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const profile = ref<ProfileInfo | null>(null)
const loading = ref(true)
const savingInfo = ref(false)
const savingPwd = ref(false)

const infoForm = reactive({ nickname: '', email: '', mobile: '' })
const pwdForm = reactive({ oldPassword: '', newPassword: '', confirm: '' })

async function load() {
  loading.value = true
  const p = await auth.loadProfileDetail()
  profile.value = p
  if (p) {
    infoForm.nickname = p.nickname || ''
    infoForm.email = p.email || ''
    infoForm.mobile = p.mobile || ''
  }
  loading.value = false
}

async function saveInfo() {
  const nick = infoForm.nickname.trim()
  if (!nick) {
    ElMessage.warning('昵称不能为空')
    return
  }
  savingInfo.value = true
  try {
    await updateProfileApi({
      nickname: nick,
      email: infoForm.email.trim() || undefined,
      mobile: infoForm.mobile.trim() || undefined,
    })
    auth.applyNickname(nick)
    ElMessage.success('个人信息已更新')
    await load()
  } catch {
    /* toast 已由拦截器处理 */
  } finally {
    savingInfo.value = false
  }
}

async function savePassword() {
  if (!pwdForm.oldPassword) {
    ElMessage.warning('请输入原密码')
    return
  }
  if (pwdForm.newPassword.length < 4 || pwdForm.newPassword.length > 16) {
    ElMessage.warning('新密码长度需为 4-16 位')
    return
  }
  if (pwdForm.newPassword !== pwdForm.confirm) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  if (pwdForm.newPassword === pwdForm.oldPassword) {
    ElMessage.warning('新密码不能与原密码相同')
    return
  }
  savingPwd.value = true
  try {
    await updatePasswordApi({ oldPassword: pwdForm.oldPassword, newPassword: pwdForm.newPassword })
    ElMessage.success('密码修改成功，下次登录请使用新密码')
    pwdForm.oldPassword = ''
    pwdForm.newPassword = ''
    pwdForm.confirm = ''
  } catch {
    /* toast 已由拦截器处理 */
  } finally {
    savingPwd.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="profile-page page-enter">
    <div class="page-head">
      <h1 class="serif page-title">个人中心</h1>
      <p class="page-sub">管理您的账号资料与登录密码。</p>
    </div>

    <div v-if="loading" class="loading-card card">加载中…</div>

    <template v-else>
      <!-- 基本信息 -->
      <div class="card info-card">
        <div class="profile-head">
          <div class="avatar-lg">{{ (infoForm.nickname || auth.username).slice(0, 1).toUpperCase() }}</div>
          <div>
            <div class="profile-nickname serif">{{ infoForm.nickname || '—' }}</div>
            <div class="profile-username">@{{ profile?.username || auth.username }}</div>
          </div>
        </div>
        <div class="form-grid">
          <div class="field">
            <label class="form-label">昵称</label>
            <input v-model="infoForm.nickname" class="form-input" placeholder="输入昵称" maxlength="30" />
          </div>
          <div class="field">
            <label class="form-label">用户名（不可修改）</label>
            <input :value="profile?.username || auth.username" class="form-input" disabled />
          </div>
          <div class="field">
            <label class="form-label">邮箱</label>
            <input v-model="infoForm.email" class="form-input" type="email" placeholder="example@corp.com" />
          </div>
          <div class="field">
            <label class="form-label">手机号</label>
            <input v-model="infoForm.mobile" class="form-input" placeholder="11 位手机号" maxlength="11" />
          </div>
        </div>
        <div class="actions">
          <button class="btn btn-primary" :disabled="savingInfo" @click="saveInfo">
            {{ savingInfo ? '保存中…' : '保存资料' }}
          </button>
        </div>
      </div>

      <!-- 修改密码 -->
      <div class="card pwd-card">
        <h3 class="serif pwd-title">修改密码</h3>
        <div class="form-grid">
          <div class="field">
            <label class="form-label">原密码</label>
            <input v-model="pwdForm.oldPassword" class="form-input" type="password" autocomplete="current-password" placeholder="请输入原密码" />
          </div>
          <div class="field">
            <label class="form-label">新密码</label>
            <input v-model="pwdForm.newPassword" class="form-input" type="password" autocomplete="new-password" placeholder="4-16 位" />
          </div>
          <div class="field">
            <label class="form-label">确认新密码</label>
            <input v-model="pwdForm.confirm" class="form-input" type="password" autocomplete="new-password" placeholder="再次输入新密码" />
          </div>
        </div>
        <div class="actions">
          <button class="btn btn-primary" :disabled="savingPwd" @click="savePassword">
            {{ savingPwd ? '提交中…' : '修改密码' }}
          </button>
        </div>
      </div>
    </template>
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
  text-align: center;
  color: var(--text-muted);
  padding: 64px;
}
.info-card,
.pwd-card {
  max-width: 640px;
  margin-bottom: var(--sp-comfortable);
}
.profile-head {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: var(--sp-comfortable);
  padding-bottom: var(--sp-base);
  border-bottom: 1px solid var(--line);
}
.avatar-lg {
  width: 64px;
  height: 64px;
  border-radius: 10px;
  background: var(--btn-solid);
  color: #fff;
  font-size: 26px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}
.profile-nickname {
  font-size: 22px;
}
.profile-username {
  font-size: 13px;
  color: var(--text-muted);
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--sp-snug);
}
.field {
  margin-bottom: var(--sp-snug);
}
.form-input:disabled {
  background: var(--paper-2);
  color: var(--text-muted);
  cursor: not-allowed;
}
.actions {
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid var(--line);
  padding-top: var(--sp-base);
  margin-top: 8px;
}
.pwd-title {
  font-size: 18px;
  margin-bottom: var(--sp-base);
}
@media (max-width: 480px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
