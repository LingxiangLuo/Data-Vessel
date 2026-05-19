<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { getScheduledWorkflows, scheduleWorkflowOnline, scheduleWorkflowOffline } from '../api'

interface ScheduledItem {
  id: number
  name: string
  cron_expression: string
  schedule_status: string
  status: string
  next_fire_time: string | null
  ds_process_code: number | null
}

const router = useRouter()
const items = ref<ScheduledItem[]>([])
const loading = ref(false)
const switchLoading = ref<Record<number, boolean>>({})

const WF_STATUS_MAP: Record<string, { text: string; color: string }> = {
  draft:   { text: '草稿',  color: '#86909c' },
  tested:  { text: '已测试', color: '#ff7d00' },
  online:  { text: '已上线', color: '#00b42a' },
  offline: { text: '已下线', color: '#f53f3f' },
}

onMounted(() => loadData())

async function loadData() {
  loading.value = true
  try {
    const res: any = await getScheduledWorkflows()
    items.value = res.items || []
  } catch (e: any) {
    Message.error('加载调度任务失败：' + (e?.response?.data?.detail || e?.message || '未知错误'))
    items.value = []
  } finally {
    loading.value = false }
}

async function toggleSchedule(item: ScheduledItem) {
  if (item.status !== 'online') {
    Message.warning('请先发布工作流，才能开启调度')
    return
  }
  switchLoading.value[item.id] = true
  try {
    if (item.schedule_status === 'ONLINE') {
      await scheduleWorkflowOffline(item.id)
      item.schedule_status = 'OFFLINE'
      Message.success('调度已关闭')
    } else {
      await scheduleWorkflowOnline(item.id)
      item.schedule_status = 'ONLINE'
      Message.success('调度已开启')
    }
  } catch (e: any) {
    Message.error(e?.response?.data?.detail || '操作失败')
  } finally {
    switchLoading.value[item.id] = false
  }
}

function goToEditor(item: ScheduledItem) {
  router.push(`/workflows/${item.id}/edit`)
}

function formatNextFireTime(t: string | null): string {
  if (!t) return '-'
  const d = new Date(t)
  if (isNaN(d.getTime())) return t
  const now = new Date()
  const diff = d.getTime() - now.getTime()
  const hh = d.getHours().toString().padStart(2, '0')
  const mm = d.getMinutes().toString().padStart(2, '0')
  if (diff < 0) return `${hh}:${mm}（已过期）`
  const days = Math.floor(diff / 86400000)
  if (days === 0) return `今天 ${hh}:${mm}`
  if (days === 1) return `明天 ${hh}:${mm}`
  return `${d.getMonth()+1}/${d.getDate()} ${hh}:${mm}`
}
</script>

<template>
  <div class="tasks-page">
    <div class="tasks-header">
      <div>
        <h2 class="tasks-title">调度任务</h2>
        <p class="tasks-desc">管理所有配置了定时调度的工作流</p>
      </div>
      <a-button @click="loadData" :loading="loading" size="small">刷新</a-button>
    </div>

    <div class="tasks-table-wrap">
      <div v-if="loading && !items.length" class="tasks-empty"><a-spin /></div>
      <div v-else-if="!items.length" class="tasks-empty">
        <a-empty description="暂无调度任务，请在工作流编辑器中配置 CRON 表达式" />
      </div>
      <table v-else class="tasks-table">
        <thead>
          <tr>
            <th>工作流名称</th>
            <th style="width:160px">CRON 表达式</th>
            <th style="width:140px">下次执行</th>
            <th style="width:100px">工作流状态</th>
            <th style="width:90px">调度开关</th>
            <th style="width:80px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id" class="task-row">
            <td class="name-cell">{{ item.name }}</td>
            <td>
              <code class="cron-code">{{ item.cron_expression }}</code>
            </td>
            <td class="next-time-cell">{{ formatNextFireTime(item.next_fire_time) }}</td>
            <td>
              <span
                class="wf-status"
                :style="{ color: WF_STATUS_MAP[item.status]?.color || '#86909c' }"
              >
                <span class="wf-status__dot" :style="{ background: WF_STATUS_MAP[item.status]?.color || '#86909c' }"></span>
                {{ WF_STATUS_MAP[item.status]?.text || item.status }}
              </span>
            </td>
            <td>
              <a-tooltip :content="item.status !== 'online' ? '请先发布工作流' : ''" :disabled="item.status === 'online'">
                <a-switch
                  :model-value="item.schedule_status === 'ONLINE'"
                  :disabled="item.status !== 'online'"
                  :loading="switchLoading[item.id]"
                  @change="toggleSchedule(item)"
                />
              </a-tooltip>
            </td>
            <td>
              <a-button type="text" size="mini" @click="goToEditor(item)">编辑</a-button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.tasks-page { padding: 20px; }
.tasks-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; }
.tasks-title { margin: 0 0 4px; font-size: 18px; font-weight: 600; }
.tasks-desc { margin: 0; color: #86909c; font-size: 13px; }

.tasks-table-wrap { border: 1px solid #e5e7eb; border-radius: 8px; background: #fff; overflow: hidden; }
.tasks-empty { display: flex; align-items: center; justify-content: center; height: 200px; }

.tasks-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.tasks-table thead tr { background: #f7f8fa; }
.tasks-table th { padding: 10px 16px; text-align: left; font-weight: 500; color: #4e5969; border-bottom: 1px solid #e5e7eb; white-space: nowrap; }
.tasks-table td { padding: 12px 16px; border-bottom: 1px solid #f2f3f5; vertical-align: middle; }
.task-row:last-child td { border-bottom: none; }
.task-row:hover { background: #f7f8fa; }

.name-cell { font-weight: 500; }
.cron-code { font-size: 12px; background: #f2f3f5; padding: 3px 8px; border-radius: 4px; font-family: 'JetBrains Mono', Consolas, monospace; color: #1d2129; }
.next-time-cell { color: #4e5969; font-size: 13px; }

.wf-status { display: flex; align-items: center; gap: 5px; font-size: 13px; }
.wf-status__dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
</style>
