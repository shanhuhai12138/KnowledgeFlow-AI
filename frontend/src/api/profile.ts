import request from './request'

/** 若依用户个人中心接口（已核对后端真实路径） */

export interface ProfileInfo {
  id: number
  username: string
  nickname: string
  email?: string
  mobile?: string
  sex?: number
  avatar?: string
}

/** GET /admin-api/system/user/profile/get */
export function getProfileApi() {
  return request.get<unknown, ProfileInfo>('/admin-api/system/user/profile/get')
}

/** PUT /admin-api/system/user/profile/update */
export function updateProfileApi(data: { nickname?: string; email?: string; mobile?: string; sex?: number; avatar?: string }) {
  return request.put<unknown, boolean>('/admin-api/system/user/profile/update', data)
}

/** PUT /admin-api/system/user/profile/update-password */
export function updatePasswordApi(data: { oldPassword: string; newPassword: string }) {
  return request.put<unknown, boolean>('/admin-api/system/user/profile/update-password', data)
}
