<script setup lang="ts">
// 知识库页：卡片网格（私有/共享徽标、文档数/成员数、hover 微升）+ 新建/编辑对话框 + 成员管理对话框
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  addKbMemberApi,
  createKbApi,
  deleteKbApi,
  getKbPageApi,
  getSystemUserPageApi,
  listKbMembersApi,
  removeKbMemberApi,
  updateKbApi,
  type KbMember,
} from '@/api/kb'
import { formatDateTime } from '@/utils/format'
import type { KnowledgeBase } from '@/types'

// ---------- 列表 ----------
const kbs = ref<KnowledgeBase[]>([])
const loading = ref(false)
const keyword = ref('')

async function loadKbs() {
  loading.value = true
  try {
    const data = await getKbPageApi({ pageNo: 1, pageSize: 100, name: keyword.value || undefined })
    kbs.value = data?.list || []
  } catch {
    kbs.value = []
  } finally {
    loading.value = false
  }
}

let searchTimer: ReturnType<typeof setTimeout> | undefined
function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(loadKbs, 300)
}

// ---------- 新建 / 编辑 ----------
const modalVisible = ref(false)
const saving = ref(false)
const editId = ref<number | null>(null)
const form = reactive({
  name: '',
  description: '',
  isPrivate: false,
})

function openCreate() {
  editId.value = null
  form.name = ''
  form.description = ''
  form.isPrivate = false
  modalVisible.value = true
}

function openEdit(kb: KnowledgeBase) {
  editId.value = kb.id
  form.name = kb.name
  form.description = kb.description || ''
  form.isPrivate = !!kb.isPrivate
  modalVisible.value = true
}

async function saveKb() {
  const name = form.name.trim()
  if (!name) {
    ElMessage.warning('请输入知识库名称')
    return
  }
  saving.value = true
  try {
    if (editId.value === null) {
      await createKbApi({ name, description: form.description.trim(), isPrivate: form.isPrivate })
      ElMessage.success('知识库创建成功')
    } else {
      await updateKbApi({ id: editId.value, name, description: form.description.trim(), isPrivate: form.isPrivate })
      ElMessage.success('知识库已更新')
    }
    modalVisible.value = false
    loadKbs()
  } catch {
    /* toast 已由拦截器处理 */
  } finally {
    saving.value = false
  }
}

async function removeKb(kb: KnowledgeBase) {
  try {
    await ElMessageBox.confirm(`确定删除知识库「${kb.name}」？该库下 ${kb.documentCount} 个文档将一并删除。`, '删除知识库', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteKbApi(kb.id)
    ElMessage.success('删除成功')
    loadKbs()
  } catch {
    /* toast 已由拦截器处理 */
  }
}

// ---------- 成员管理 ----------
const memberVisible = ref(false)
const memberKb = ref<KnowledgeBase | null>(null)
const members = ref<KbMember[]>([])
const userMap = ref<Record<number, { username: string; nickname: string }>>({})

// 添加成员
const addVisible = ref(false)
const addUserId = ref<number | undefined>()
const addRole = ref('VIEWER')
const userOptions = ref<Array<{ id: number; username: string; nickname: string }>>([])
const userKeyword = ref('')
const adding = ref(false)

async function loadUserMap() {
  try {
    const data = await getSystemUserPageApi({ pageNo: 1, pageSize: 200 })
    const map: Record<number, { username: string; nickname: string }> = {}
    for (const u of data?.list || []) map[u.id] = { username: u.username, nickname: u.nickname }
    userMap.value = map
  } catch {
    /* ignore */
  }
}

async function searchUsers() {
  try {
    const data = await getSystemUserPageApi({
      pageNo: 1,
      pageSize: 20,
      username: userKeyword.value || undefined,
    })
    userOptions.value = data?.list || []
  } catch {
    userOptions.value = []
  }
}

function openMember(kb: KnowledgeBase) {
  memberKb.value = kb
  memberVisible.value = true
  members.value = []
  loadMembers()
}

async function loadMembers() {
  if (!memberKb.value) return
  try {
    const data = await listKbMembersApi(memberKb.value.id)
    members.value = data?.list || []
  } catch {
    members.value = []
  }
}

async function submitAddMember() {
  if (!memberKb.value || !addUserId.value) {
    ElMessage.warning('请选择用户')
    return
  }
  adding.value = true
  try {
    await addKbMemberApi({ kbId: memberKb.value.id, userId: addUserId.value, role: addRole.value })
    ElMessage.success('成员已添加')
    addVisible.value = false
    addUserId.value = undefined
    addRole.value = 'VIEWER'
    loadMembers()
    loadKbs()
  } catch {
    /* toast 已处理 */
  } finally {
    adding.value = false
  }
}

async function removeMember(m: KbMember) {
  try {
    await ElMessageBox.confirm('确定移除该成员？', '移除成员', { type: 'warning' })
  } catch {
    return
  }
  try {
    await removeKbMemberApi(m.id)
    ElMessage.success('已移除')
    loadMembers()
    loadKbs()
  } catch {
    /* toast 已处理 */
  }
}

const ROLE_LABEL: Record<string, string> = { ADMIN: '管理员', EDITOR: '编辑者', VIEWER: '查看者' }

const memberDisplay = computed(() =>
  members.value.map((m) => ({
    ...m,
    displayName: userMap.value[m.userId]?.nickname || userMap.value[m.userId]?.username || `用户 #${m.userId}`,
    username: userMap.value[m.userId]?.username || '',
  })),
)

onMounted(() => {
  loadKbs()
  loadUserMap()
})
</script>

<template>
  <div class="kb-page page-enter">
    <div class="page-head">
      <div>
        <h1 class="serif page-title">知识库管理</h1>
        <p class="page-sub">管理您的企业知识库，设置成员访问权限及同步策略。</p>
      </div>
      <button class="btn btn-primary" @click="openCreate">
        <svg width="16" height="16" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
        </svg>新建知识库
      </button>
    </div>

    <div class="search-wrap">
      <svg width="18" height="18" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
        <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <input v-model="keyword" class="form-input kb-search" placeholder="搜索知识库名称或描述…" @input="onSearch" />
    </div>

    <div v-if="loading" class="kb-loading">加载中…</div>
    <div v-else-if="!kbs.length" class="kb-empty">
      暂无知识库，点击右上角「新建知识库」开始搭建您的企业知识库。
    </div>
    <div v-else class="kb-grid">
      <div v-for="kb in kbs" :key="kb.id" class="card card-hover kb-card">
        <div class="kb-head">
          <span class="kb-name serif">{{ kb.name }}</span>
          <span class="kb-badge" :class="kb.isPrivate ? 'private' : 'shared'">
            <svg v-if="kb.isPrivate" width="11" height="11" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <svg v-else width="11" height="11" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
              <path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            {{ kb.isPrivate ? '私有' : '共享' }}
          </span>
        </div>
        <p class="kb-desc">{{ kb.description || '暂无描述' }}</p>
        <div class="kb-stats">
          <span class="stat"><span class="stat-num">{{ kb.documentCount }}</span> 文档</span>
          <span class="stat"><span class="stat-num">{{ kb.memberCount }}</span> 成员</span>
          <span class="kb-time">{{ formatDateTime(kb.updatedAt) }}</span>
        </div>
        <div class="kb-actions">
          <button class="btn btn-secondary kb-action" @click="openEdit(kb)">编辑</button>
          <button class="btn btn-secondary kb-action" @click="openMember(kb)">成员</button>
          <button class="btn btn-secondary kb-action danger" @click="removeKb(kb)">删除</button>
        </div>
      </div>
    </div>

    <!-- 新建/编辑模态（照原型 kb-modal） -->
    <div v-if="modalVisible" class="modal-mask" @click.self="modalVisible = false">
      <div class="card modal-card">
        <div class="modal-head">
          <h3 class="serif">{{ editId === null ? '新建知识库' : '编辑知识库' }}</h3>
          <button class="btn-icon" @click="modalVisible = false">
            <svg width="20" height="20" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="field">
            <label class="form-label">名称</label>
            <input v-model="form.name" class="form-input" placeholder="如：研发技术文档" />
          </div>
          <div class="field">
            <label class="form-label">描述</label>
            <textarea v-model="form.description" class="form-input" rows="3" placeholder="简单描述一下知识库的用途…" style="resize: vertical"></textarea>
          </div>
          <div class="field">
            <label class="form-label">可见性</label>
            <div class="vis-grid">
              <label class="vis-option" :class="{ checked: !form.isPrivate }">
                <input v-model="form.isPrivate" type="radio" :value="false" />
                <div>
                  <div class="vis-title">团队共享</div>
                  <div class="vis-desc">所有人可见</div>
                </div>
              </label>
              <label class="vis-option" :class="{ checked: form.isPrivate }">
                <input v-model="form.isPrivate" type="radio" :value="true" />
                <div>
                  <div class="vis-title">私有库</div>
                  <div class="vis-desc">仅选定人员可见</div>
                </div>
              </label>
            </div>
          </div>
        </div>
        <div class="modal-foot">
          <button class="btn btn-secondary" @click="modalVisible = false">取消</button>
          <button class="btn btn-primary" :disabled="saving" @click="saveKb">
            {{ saving ? '保存中…' : editId === null ? '确认创建' : '保存修改' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 成员管理模态 -->
    <div v-if="memberVisible && memberKb" class="modal-mask" @click.self="memberVisible = false">
      <div class="card modal-card member-card">
        <div class="modal-head">
          <h3 class="serif">成员管理 · {{ memberKb.name }}</h3>
          <button class="btn-icon" @click="memberVisible = false">
            <svg width="20" height="20" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="member-list">
          <div v-if="!members.length" class="member-empty">暂无成员，点击下方「添加成员」</div>
          <div v-for="m in memberDisplay" :key="m.id" class="member-row">
            <div class="member-avatar">{{ m.displayName.slice(0, 1).toUpperCase() }}</div>
            <div class="member-info">
              <div class="member-name">{{ m.displayName }}</div>
              <div class="member-user">{{ m.username || `ID ${m.userId}` }}</div>
            </div>
            <span class="role-pill">{{ ROLE_LABEL[m.role] || m.role }}</span>
            <button class="btn-icon" title="移除成员" @click="removeMember(m)">
              <svg width="15" height="15" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>

        <!-- 添加成员 -->
        <div v-if="addVisible" class="add-member">
          <div class="add-row">
            <input v-model="userKeyword" class="form-input" placeholder="搜索用户名…" @input="searchUsers" />
            <div class="user-options">
              <button
                v-for="u in userOptions"
                :key="u.id"
                class="user-option"
                :class="{ selected: addUserId === u.id }"
                @click="addUserId = u.id"
              >
                {{ u.nickname || u.username }} <span class="user-sub">@{{ u.username }}</span>
              </button>
              <div v-if="!userOptions.length" class="user-none">无匹配用户</div>
            </div>
          </div>
          <div class="add-row">
            <div class="role-select">
              <button v-for="r in ['VIEWER', 'EDITOR', 'ADMIN']" :key="r" class="role-opt" :class="{ active: addRole === r }" @click="addRole = r">
                {{ ROLE_LABEL[r] }}
              </button>
            </div>
            <button class="btn btn-primary" :disabled="adding || !addUserId" @click="submitAddMember">
              {{ adding ? '添加中…' : '确认添加' }}
            </button>
          </div>
        </div>
        <div class="modal-foot">
          <button v-if="!addVisible" class="btn btn-secondary" @click="addVisible = true; searchUsers()">
            <svg width="14" height="14" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" fill="none">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
            </svg>添加成员
          </button>
          <button v-else class="btn btn-secondary" @click="addVisible = false; addUserId = undefined">取消添加</button>
          <button class="btn btn-primary" @click="memberVisible = false">完成</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--sp-comfortable);
  flex-wrap: wrap;
  gap: 16px;
}
.page-title {
  font-size: 39px;
  margin-bottom: 8px;
}
.page-sub {
  color: var(--text-muted);
}

.search-wrap {
  position: relative;
  margin-bottom: var(--sp-comfortable);
}
.search-wrap svg {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
}
.kb-search {
  padding-left: 40px;
  background: var(--paper-2);
}

.kb-loading,
.kb-empty {
  padding: 64px 0;
  text-align: center;
  color: var(--text-muted);
}

.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--sp-comfortable);
}
.kb-card {
  display: flex;
  flex-direction: column;
  padding: var(--sp-comfortable);
}
.kb-card:hover {
  transform: translateY(-2px);
}
.kb-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.kb-name {
  font-size: 20px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.kb-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 999px;
  flex-shrink: 0;
}
.kb-badge.shared {
  color: var(--success);
  background: rgba(31, 122, 77, 0.1);
}
.kb-badge.private {
  color: var(--gold);
  background: rgba(165, 131, 62, 0.14);
}
.kb-desc {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: var(--sp-snug);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 38px;
}
.kb-stats {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: var(--sp-snug);
  border-top: 1px solid var(--line);
  padding-top: var(--sp-snug);
}
.stat-num {
  font-weight: 700;
  color: var(--ink);
  font-variant-numeric: tabular-nums;
}
.kb-time {
  margin-left: auto;
  font-size: 11px;
}
.kb-actions {
  display: flex;
  gap: 8px;
  margin-top: auto;
}
.kb-action {
  flex: 1;
  padding: 8px 0;
  font-size: 12px;
  justify-content: center;
}
.kb-action.danger:hover {
  color: var(--error);
  border-color: var(--error);
}

/* 模态 */
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(10, 10, 10, 0.5);
  display: flex;
  z-index: 1000;
  /* 内容超高时整层可滚动（配合子项 margin:auto，溢出时顶部可达，不被裁切） */
  padding: 24px;
  overflow-y: auto;
}
.modal-card {
  margin: auto; /* flex 居中；内容超高时自动对齐到起点，可随遮罩滚动 */
  width: 100%;
  max-width: 480px;
  padding: var(--sp-comfortable);
}
.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--sp-comfortable);
}
.modal-head h3 {
  font-size: 18px;
}
.field {
  margin-bottom: var(--sp-base);
}
.vis-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.vis-option {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--paper-2);
  border: 1px solid var(--line);
  border-radius: 6px;
  cursor: pointer;
  transition: border-color 0.2s;
}
.vis-option.checked {
  border-color: var(--vermillion);
}
.vis-option input {
  accent-color: var(--vermillion);
}
.vis-title {
  font-weight: 600;
  margin-bottom: 2px;
}
.vis-desc {
  font-size: 11px;
  color: var(--text-muted);
}
.modal-foot {
  display: flex;
  gap: 12px;
  margin-top: var(--sp-comfortable);
  justify-content: flex-end;
}

/* 成员 */
.member-card {
  max-width: 520px;
}
.member-list {
  max-height: 320px;
  overflow-y: auto;
  border-top: 1px solid var(--line);
}
.member-empty {
  padding: 24px 0;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
}
.member-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--line);
}
.member-avatar {
  width: 34px;
  height: 34px;
  border-radius: 6px;
  background: var(--btn-solid);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}
.member-info {
  flex: 1;
  min-width: 0;
}
.member-name {
  font-weight: 600;
  font-size: 14px;
}
.member-user {
  font-size: 11px;
  color: var(--text-muted);
}
.role-pill {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(33, 49, 56, 0.08);
  color: var(--vermillion);
}
.add-member {
  margin-top: var(--sp-snug);
  border-top: 1px solid var(--line);
  padding-top: var(--sp-snug);
}
.add-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 10px;
}
.user-options {
  max-height: 160px;
  overflow-y: auto;
  border: 1px solid var(--line);
  border-radius: var(--input-radius);
  background: var(--paper-2);
}
.user-option {
  display: flex;
  width: 100%;
  text-align: left;
  padding: 8px 12px;
  background: none;
  border: none;
  border-bottom: 1px solid var(--line);
  cursor: pointer;
  font-size: 13px;
  color: var(--ink);
}
.user-option:last-child {
  border-bottom: none;
}
.user-option:hover,
.user-option.selected {
  background: rgba(33, 49, 56, 0.08);
}
.user-sub {
  color: var(--text-muted);
  margin-left: 6px;
  font-size: 11px;
}
.user-none {
  padding: 12px;
  text-align: center;
  color: var(--text-muted);
  font-size: 12px;
}
.role-select {
  display: flex;
  gap: 8px;
}
.role-opt {
  flex: 1;
  padding: 8px 0;
  border: 1px solid var(--line);
  border-radius: var(--input-radius);
  background: var(--paper-2);
  cursor: pointer;
  font-size: 12px;
  color: var(--text-muted);
  transition: all 0.2s;
}
.role-opt.active {
  background: var(--vermillion);
  color: #fff;
  border-color: var(--vermillion);
}
</style>
