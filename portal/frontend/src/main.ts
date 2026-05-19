import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ArcoVue from '@arco-design/web-vue'
import '@arco-design/web-vue/dist/arco.css'
import './styles/global.css'
import App from './App.vue'
import router from './router'
import { setupPermissionDirective } from './directives/permission'
import { reportFrontendError } from './api'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ArcoVue)
setupPermissionDirective(app)

// ─── 全局错误捕获 ──────────────────────────────────────────────────────────
app.config.errorHandler = (err, _instance, info) => {
  const message = err instanceof Error ? err.message : String(err)
  reportFrontendError('error', message, {
    source: 'vue-runtime',
    stack: err instanceof Error ? err.stack : undefined,
    info,
  })
}

window.addEventListener('error', (event) => {
  reportFrontendError('error', event.message, {
    source: 'window',
    stack: event.error?.stack,
  })
})

window.addEventListener('unhandledrejection', (event) => {
  const message = event.reason instanceof Error ? event.reason.message : String(event.reason)
  reportFrontendError('error', message, {
    source: 'unhandledrejection',
    stack: event.reason instanceof Error ? event.reason.stack : undefined,
  })
})

app.mount('#app')
