import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

/**
 * 将时间字符串转为相对日期显示
 * 今天 02:01 / 昨天 08:30 / 明天 02:00 / 05-12 10:00
 */
export function relativeDate(t: string | null | undefined): string {
  if (!t) return '—'
  const d = dayjs(t)
  if (!d.isValid()) return '—'
  const now = dayjs()
  if (d.isSame(now, 'day')) return `今天 ${d.format('HH:mm')}`
  if (d.isSame(now.subtract(1, 'day'), 'day')) return `昨天 ${d.format('HH:mm')}`
  if (d.isSame(now.add(1, 'day'), 'day')) return `明天 ${d.format('HH:mm')}`
  if (d.isSame(now, 'year')) return d.format('MM-DD HH:mm')
  return d.format('YYYY-MM-DD HH:mm')
}

/**
 * 将秒数转为人类可读的耗时格式
 * 45 → "45s" / 192 → "3m12s" / 3900 → "1h5m"
 */
export function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return '—'
  if (seconds < 0) return '—'
  if (seconds < 60) return `${seconds}s`
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  if (m < 60) return s ? `${m}m${s}s` : `${m}m`
  const h = Math.floor(m / 60)
  const rm = m % 60
  return rm ? `${h}h${rm}m` : `${h}h`
}
