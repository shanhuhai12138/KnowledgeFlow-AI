import { defineStore } from 'pinia'
import { loginAndSave, getUserInfoApi } from '@/api/auth'
import { getProfileApi } from '@/api/profile'
import { clearToken, getToken } from '@/api/request'

const USERNAME_KEY = 'kf_username'
const NICKNAME_KEY = 'kf_nickname'
const ROLES_KEY = 'kf_roles'

interface AuthState {
  token: string
  username: string
  nickname: string
  roles: string[]
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: getToken(),
    username: localStorage.getItem(USERNAME_KEY) || '',
    nickname: localStorage.getItem(NICKNAME_KEY) || '',
    roles: JSON.parse(localStorage.getItem(ROLES_KEY) || '[]'),
  }),
  getters: {
    isLoggedIn: (s) => !!s.token,
    displayName: (s) => s.nickname || s.username || 'Admin',
    /** 仅 super_admin 可见 AI 设置入口（后端 @PreAuthorize hasRole('super_admin')） */
    isAdmin: (s) => s.roles.includes('super_admin'),
  },
  actions: {
    setRoles(roles: string[]) {
      this.roles = roles
      localStorage.setItem(ROLES_KEY, JSON.stringify(roles))
    },
    async login(username: string, password: string) {
      await loginAndSave(username, password)
      this.token = getToken()
      this.username = username
      this.nickname = username
      localStorage.setItem(USERNAME_KEY, username)
      localStorage.setItem(NICKNAME_KEY, username)
      await this.refreshProfile()
    },
    /** 拉取用户信息（昵称 + 角色），登录后与个人中心改昵称后调用 */
    async refreshProfile() {
      try {
        const info = await getUserInfoApi()
        const nick = info?.user?.nickname
        if (nick) {
          this.nickname = nick
          localStorage.setItem(NICKNAME_KEY, nick)
        }
        this.username = info?.user?.username || this.username
        localStorage.setItem(USERNAME_KEY, this.username)
        if (Array.isArray(info?.roles)) this.setRoles(info.roles)
      } catch {
        /* 失败不阻塞，尽力而为 */
      }
    },
    /** 个人中心改昵称成功后同步本地，避免缓存旧昵称 */
    applyNickname(nickname: string) {
      this.nickname = nickname
      localStorage.setItem(NICKNAME_KEY, nickname)
    },
    async loadProfileDetail() {
      try {
        const p = await getProfileApi()
        if (p?.nickname) {
          this.nickname = p.nickname
          localStorage.setItem(NICKNAME_KEY, p.nickname)
        }
        if (p?.username) {
          this.username = p.username
          localStorage.setItem(USERNAME_KEY, p.username)
        }
        return p
      } catch {
        return null
      }
    },
    logout() {
      this.token = ''
      this.username = ''
      this.nickname = ''
      this.roles = []
      clearToken()
      localStorage.removeItem(USERNAME_KEY)
      localStorage.removeItem(NICKNAME_KEY)
      localStorage.removeItem(ROLES_KEY)
    },
  },
})
