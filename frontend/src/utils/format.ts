import dayjs from 'dayjs'

/** 后端时间字段兼容两种格式：毫秒时间戳(number) / ISO 字符串(string) */
export function formatDateTime(v?: number | string | null): string {
  if (v === undefined || v === null || v === '') return '-'
  return dayjs(v).format('YYYY-MM-DD HH:mm')
}

export function formatDate(v?: number | string | null): string {
  if (v === undefined || v === null || v === '') return '-'
  return dayjs(v).format('YYYY-MM-DD')
}

export function formatTime(v?: number | string | null): string {
  if (v === undefined || v === null || v === '') return '-'
  return dayjs(v).format('HH:mm')
}

/** 文件大小：字节 → 人类可读 */
export function formatFileSize(bytes?: number | null): string {
  if (bytes === undefined || bytes === null) return '-'
  if (bytes < 1024) return `${bytes} B`
  const units = ['KB', 'MB', 'GB']
  let n = bytes
  let u = -1
  do {
    n /= 1024
    u++
  } while (n >= 1024 && u < units.length - 1)
  return `${n.toFixed(n >= 100 ? 0 : 1)} ${units[u]}`
}
