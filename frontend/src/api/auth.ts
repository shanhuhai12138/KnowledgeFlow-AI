import request, { setToken } from './request'
import type { LoginResult, UserInfo } from '@/types'

/** 登录：POST /admin-api/system/auth/login */
export function loginApi(username: string, password: string) {
  return request.post<unknown, LoginResult>('/admin-api/system/auth/login', { username, password })
}

/** 注册：POST /admin-api/system/auth/register（若依内置） */
export function registerApi(username: string, password: string, nickname?: string) {
  return request.post<unknown, LoginResult>('/admin-api/system/auth/register', {
    username,
    password,
    nickname,
  })
}

/** 获取用户信息：GET /admin-api/system/auth/get-permission-info */
export function getUserInfoApi() {
  return request.get<unknown, UserInfo>('/admin-api/system/auth/get-permission-info')
}

export async function loginAndSave(username: string, password: string) {
  const data = await loginApi(username, password)
  setToken(data.accessToken)
  return data
}
