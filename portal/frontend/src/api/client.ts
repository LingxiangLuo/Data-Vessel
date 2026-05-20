import axios from 'axios'
import { Message } from '@arco-design/web-vue'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  withCredentials: true,
})

function reportFrontendError(level: 'error' | 'warn' | 'info', message: string, extra?: Record<string, unknown>) {
  try {
    const payload = {
      level,
      message: message.slice(0, 2000),
      url: window.location.href,
      user_agent: navigator.userAgent,
      source: extra?.source || 'vue-runtime',
      stack: extra?.stack ? String(extra.stack).slice(0, 4000) : undefined,
    }
    if (navigator.sendBeacon) {
      navigator.sendBeacon('/api/log/frontend', new Blob([JSON.stringify(payload)], { type: 'application/json' }))
    } else {
      fetch('/api/log/frontend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        keepalive: true,
      }).catch(() => {})
    }
  } catch {
    // 上报失败静默处理，避免递归
  }
}

function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp('(?:^|; )' + name.replace(/([.$?*|{}()[\]\\/+^])/g, '\\$1') + '=([^;]*)'))
  return match ? decodeURIComponent(match[1]) : null
}

api.interceptors.request.use((config) => {
  // 非只读请求自动携带 CSRF token（cookie 认证场景）
  if (config.method && !['get', 'head', 'options'].includes(config.method.toLowerCase())) {
    const csrf = getCookie('csrf_token')
    if (csrf) {
      config.headers = config.headers || {}
      config.headers['X-CSRF-Token'] = csrf
    }
  }
  return config
})

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const msg = error.response?.data?.detail || '请求失败'
    if (error.response?.status === 401) {
      import('../stores/user').then(({ useUserStore }) => {
        useUserStore().logout()
      })
      window.location.href = '/login'
    } else if (error.response?.status >= 500) {
      reportFrontendError('error', `API ${error.config?.method?.toUpperCase()} ${error.config?.url} failed: ${msg}`, {
        source: 'axios',
      })
      Message.error(msg)
    } else {
      Message.error(msg)
    }
    return Promise.reject(error)
  }
)

export { api, reportFrontendError }
