import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    chunkSizeWarningLimit: 4000,
    rollupOptions: {
      output: {
        manualChunks(id) {
          // Monaco Editor — 最大 chunk（~3MB），单独拆分
          if (id.includes('monaco-editor')) {
            return 'monaco'
          }
          // Vue Flow — DAG 画布依赖
          if (id.includes('@vue-flow')) {
            return 'vue-flow'
          }
          // Arco Design — UI 组件库
          if (id.includes('@arco-design')) {
            return 'arco'
          }
          // ECharts — 图表库
          if (id.includes('echarts')) {
            return 'echarts'
          }
          // xlsx — Excel 处理
          if (id.includes('xlsx')) {
            return 'xlsx'
          }
          // 其余 node_modules 拆为 vendor
          if (id.includes('node_modules')) {
            return 'vendor'
          }
        },
      },
    },
  },
})
