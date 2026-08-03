import axios, { type AxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'

const TOKEN_KEY = 'kf_access_token'
const TENANT_ID = '1'

export function getToken(): string {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

/**
 * API 基础地址：容器构建时经 VITE_API_BASE 注入（相对路径 /admin-api 由 nginx 反代）；
 * 本地开发默认直连后端 48080
 */
export const API_BASE: string = import.meta.env.VITE_API_BASE ?? 'http://localhost:48080'

const request = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
})

// 请求拦截：统一 Authorization + tenant-id
request.interceptors.request.use((config) => {
  config.headers['tenant-id'] = TENANT_ID
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 响应拦截：解包若依统一响应 {code, data, message}
request.interceptors.response.use(
  (res) => {
    const body = res.data
    if (body && typeof body === 'object' && 'code' in body) {
      if (body.code === 0) return body.data
      if (body.code === 401) {
        handleUnauthorized()
        return Promise.reject(new Error(body.message || '未登录或登录已过期'))
      }
      ElMessage.error(body.message || '请求失败')
      return Promise.reject(new Error(body.message || '请求失败'))
    }
    return body
  },
  (err) => {
    const status = err?.response?.status
    if (status === 401) {
      handleUnauthorized()
    } else {
      const msg = err?.response?.data?.message || err?.message || '网络异常'
      ElMessage.error(msg)
    }
    return Promise.reject(err)
  },
)

function handleUnauthorized() {
  clearToken()
  // 避免重复跳转
  if (!location.pathname.startsWith('/login')) {
    location.href = '/login'
  }
}

/** 上传类接口需要返回完整响应体（含自定义进度），单独导出原始 axios */
export function requestRaw<T = unknown>(config: AxiosRequestConfig): Promise<T> {
  return axios
    .request({
      ...config,
      baseURL: API_BASE,
    } as AxiosRequestConfig)
    .then((res) => res.data) as Promise<T>
}

export default request
