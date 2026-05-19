<template>
  <div class="page">
    <div class="glass-card page-header">
      <div>
        <h3 class="page-title">系统监控</h3>
        <p class="page-desc">平台服务运行状态 · 实时探测</p>
      </div>
      <a-button @click="refreshAll" :loading="loading">
        <template #icon><icon-refresh /></template>
        刷新
      </a-button>
    </div>

    <!-- 服务健康状态 -->
    <div class="glass-card services-section">
      <h3 class="section-title">服务健康</h3>
      <div class="service-row">
        <div v-for="svc in services" :key="svc.key" class="service-chip" :class="{ online: svc.online, offline: !svc.online }">
          <span class="svc-dot"></span>
          <div class="svc-info">
            <span class="svc-name">{{ svc.name }}</span>
            <span class="svc-port">:{{ svc.port }}</span>
          </div>
        </div>
      </div>
      <div class="service-summary">
        <span class="summary-ok">{{ services.filter(s => s.online).length }}/{{ services.length }} 服务正常</span>
        <span v-if="services.some(s => !s.online)" class="summary-warn">{{ services.filter(s => !s.online).length }} 个异常</span>
      </div>
    </div>

    <!-- 调度引擎资源监控 -->
    <div class="glass-card ds-section">
      <h3 class="section-title">调度引擎</h3>
      <div v-if="dsMonitor.healthy" class="ds-content">
        <div class="ds-status-row">
          <div class="ds-status-item" v-for="item in dsStatusItems" :key="item.label">
            <span class="ds-label">{{ item.label }}</span>
            <span class="ds-value" :class="item.status">{{ item.value }}</span>
          </div>
        </div>
        <div class="ds-metrics">
          <div class="metric-item">
            <div class="metric-header">
              <span class="metric-label">CPU</span>
              <span class="metric-value" :style="{ color: metricColor(dsMonitor.cpuUsage) }">{{ dsMonitor.cpuUsage }}%</span>
            </div>
            <div class="metric-bar">
              <div class="metric-fill" :style="{ width: dsMonitor.cpuUsage + '%', background: metricColor(dsMonitor.cpuUsage) }"></div>
            </div>
          </div>
          <div class="metric-item">
            <div class="metric-header">
              <span class="metric-label">内存</span>
              <span class="metric-value" :style="{ color: metricColor(dsMonitor.memoryUsage) }">
                {{ dsMonitor.memoryUsage }}%
                <span class="metric-sub">{{ formatBytes(dsMonitor.memoryUsed) }} / {{ formatBytes(dsMonitor.memoryMax) }}</span>
              </span>
            </div>
            <div class="metric-bar">
              <div class="metric-fill" :style="{ width: dsMonitor.memoryUsage + '%', background: metricColor(dsMonitor.memoryUsage) }"></div>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="ds-unavailable">
        <span class="svc-dot offline"></span>
        <span>调度引擎服务不可用</span>
      </div>
    </div>

    <!-- 平台信息 -->
    <div class="glass-card info-section">
      <h3 class="section-title">平台信息</h3>
      <div class="info-grid" v-if="sysInfo">
        <div class="info-item">
          <span class="info-label">操作系统</span>
          <span class="info-value mono">{{ sysInfo.os }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">CPU</span>
          <span class="info-value mono">{{ sysInfo.cpu_count }} 核</span>
        </div>
        <div class="info-item">
          <span class="info-label">内存</span>
          <span class="info-value mono">{{ sysInfo.memory_total }}（可用 {{ sysInfo.memory_available }}）</span>
        </div>
        <div class="info-item">
          <span class="info-label">磁盘</span>
          <span class="info-value mono">{{ sysInfo.disk_used }} / {{ sysInfo.disk_total }}（{{ sysInfo.disk_usage_pct }}%）</span>
        </div>
        <div class="info-item">
          <span class="info-label">运行时间</span>
          <span class="info-value mono">{{ sysInfo.uptime }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">部署模式</span>
          <span class="info-value">{{ sysInfo.deploy_mode }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">对外端口</span>
          <span class="info-value mono">:{{ sysInfo.public_port }} (Nginx)</span>
        </div>
      </div>
      <a-spin v-else dot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { IconRefresh } from '@arco-design/web-vue/es/icon'
import { getDSMonitor, getSystemServices } from '../api'
import api from '../api'

const loading = ref(false)
const services = ref<any[]>([])
const sysInfo = ref<any>(null)

const dsMonitor = reactive({
  healthy: false,
  cpuUsage: 0,
  memoryUsage: 0,
  memoryMax: 0,
  memoryUsed: 0,
  masterStatus: '-',
  workerStatus: '-',
  dbStatus: '-',
})

const dsStatusItems = computed(() => [
  { label: 'Master', value: dsMonitor.masterStatus, status: dsMonitor.masterStatus === 'UP' ? 'up' : 'down' },
  { label: 'Worker', value: dsMonitor.workerStatus, status: dsMonitor.workerStatus === 'UP' ? 'up' : 'down' },
  { label: '数据库', value: dsMonitor.dbStatus, status: dsMonitor.dbStatus === 'UP' ? 'up' : 'down' },
  { label: '模式', value: 'Standalone', status: 'up' },
])

function metricColor(val: number) {
  if (val < 60) return '#00B42A'
  if (val < 80) return '#FF7D00'
  return '#F53F3F'
}

function formatBytes(bytes: number) {
  if (!bytes) return '-'
  const gb = bytes / (1024 * 1024 * 1024)
  return gb >= 1 ? `${gb.toFixed(1)} GB` : `${(bytes / (1024 * 1024)).toFixed(0)} MB`
}

async function loadServices() {
  try {
    const res: any = await getSystemServices()
    services.value = res.services || []
  } catch { services.value = [] }
}

async function loadDSMonitor() {
  try {
    const res: any = await getDSMonitor()
    Object.assign(dsMonitor, res)
  } catch { dsMonitor.healthy = false }
}

async function loadSysInfo() {
  try {
    const res: any = await api.get('/system/info')
    sysInfo.value = res
  } catch {}
}

async function refreshAll() {
  loading.value = true
  await Promise.all([loadServices(), loadDSMonitor(), loadSysInfo()])
  loading.value = false
}

onMounted(() => { refreshAll() })
</script>

<style scoped>
.page { animation: fadeIn 0.3s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.page-header { padding: 20px 24px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { margin: 0; font-size: 18px; font-weight: 600; color: #1D2129; }
.page-desc { margin: 4px 0 0; font-size: 13px; color: #86909C; }
.section-title { margin: 0 0 16px; font-size: 15px; font-weight: 600; color: #1D2129; }

.services-section { padding: 20px; margin-bottom: 16px; }
.service-row { display: flex; gap: 12px; flex-wrap: wrap; }
.service-chip {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 16px; border-radius: 8px; border: 1px solid #E5E8ED;
  background: #FAFBFC; min-width: 140px; transition: all 0.15s;
}
.service-chip.online { border-color: #B7EB8F; background: #F6FFED; }
.service-chip.offline { border-color: #FFA39E; background: #FFF1F0; }
.svc-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.service-chip.online .svc-dot { background: #00B42A; box-shadow: 0 0 6px rgba(0,180,42,0.4); }
.service-chip.offline .svc-dot { background: #F53F3F; box-shadow: 0 0 6px rgba(245,63,63,0.4); }
.svc-info { display: flex; flex-direction: column; }
.svc-name { font-size: 13px; font-weight: 500; color: #1D2129; }
.svc-port { font-size: 11px; color: #86909C; font-family: 'JetBrains Mono', monospace; }
.service-summary { margin-top: 12px; font-size: 12px; display: flex; gap: 12px; }
.summary-ok { color: #00B42A; }
.summary-warn { color: #F53F3F; font-weight: 500; }

.ds-section { padding: 20px; margin-bottom: 16px; }
.ds-content { display: flex; flex-direction: column; gap: 16px; }
.ds-status-row { display: flex; gap: 24px; }
.ds-status-item { display: flex; flex-direction: column; gap: 4px; }
.ds-label { font-size: 11px; color: #86909C; }
.ds-value { font-size: 13px; font-weight: 600; }
.ds-value.up { color: #00B42A; }
.ds-value.down { color: #F53F3F; }
.ds-metrics { display: flex; flex-direction: column; gap: 12px; }
.metric-item { display: flex; flex-direction: column; gap: 6px; }
.metric-header { display: flex; justify-content: space-between; align-items: center; }
.metric-label { font-size: 13px; color: #4E5969; }
.metric-value { font-size: 14px; font-weight: 600; }
.metric-sub { font-size: 11px; font-weight: 400; color: #86909C; margin-left: 4px; }
.metric-bar { height: 6px; background: #F2F3F5; border-radius: 3px; overflow: hidden; }
.metric-fill { height: 100%; border-radius: 3px; transition: width 0.3s; }
.ds-unavailable { display: flex; align-items: center; gap: 8px; color: #86909C; font-size: 13px; }
.ds-unavailable .svc-dot { background: #F53F3F; }

.info-section { padding: 20px; }
.info-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px 32px; }
.info-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #F2F3F5; }
.info-label { font-size: 13px; color: #86909C; }
.info-value { font-size: 13px; color: #1D2129; font-weight: 500; }
.mono { font-family: 'JetBrains Mono', monospace; }
</style>
