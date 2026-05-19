<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { getDSInstanceDetail, getDSTaskLog, rerunDSInstance } from '../api'

interface DqcResult {
  task_name: string
  task_state: string
  rule_id: number
  rule_name: string
  is_strong: boolean
  passed: boolean | null
  actual_value: any
  expected_value: any
  sample_data: any
  checked_at: string
}

interface Task {
  id: number
  name: string
  state: string
  type?: string
  startTime: string
  endTime: string
  duration: string
}

interface InstanceInfo {
  id: number
  state: string
  start_time: string
  end_time: string
  duration: number
  process_definition_code: number
  workflow_id: number | null
}

const route = useRoute()
const router = useRouter()
const instanceId = Number(route.params.id)

const instance = ref<InstanceInfo | null>(null)
const tasks = ref<Task[]>([])
const dqcResults = ref<DqcResult[]>([])
const loading = ref(false)
const logVisible = ref(false)
const logContent = ref('')
const logLoading = ref(false)
const logTaskName = ref('')
const rerunLoading = ref(false)
const forcePassLoading = ref(false)

const STATE_MAP: Record<string, { text: string; color: string; bg: string }> = {
  SUCCESS:           { text: '成功',   color: '#00b42a', bg: '#e8ffea' },
  FAILURE:           { text: '失败',   color: '#f53f3f', bg: '#ffece8' },
  RUNNING_EXECUTION: { text: '运行中', color: '#165dff', bg: '#e8f3ff' },
  STOP:              { text: '停止',   color: '#86909c', bg: '#f2f3f5' },
  KILL:              { text: '已终止', color: '#ff7d00', bg: '#fff7e8' },
  NEED_FAULT_TOLERANCE: { text: '容错中', color: '#ff7d00', bg: '#fff7e8' },
}

const hasStrongFailure = computed(() => {
  return dqcResults.value.some(r => r.is_strong && r.passed === false)
})

const dqcPassedCount = computed(() => dqcResults.value.filter(r => r.passed === true).length)
const dqcFailedCount = computed(() => dqcResults.value.filter(r => r.passed === false).length)
const dqcPendingCount = computed(() => dqcResults.value.filter(r => r.passed === null).length)

onMounted(() => loadData())

async function loadData() {
  loading.value = true
  try {
    const res: any = await getDSInstanceDetail(instanceId)
    instance.value = res.instance
    const list = res.tasks || []
    tasks.value = list.map((t: any) => ({
      id: t.id,
      name: t.name,
      state: t.state,
      type: t.type,
      startTime: t.start_time ? formatTime(t.start_time) : '-',
      endTime: t.end_time ? formatTime(t.end_time) : '-',
      duration: t.duration != null ? formatDuration(t.duration) : '-',
    }))
    dqcResults.value = res.dqc_results || []
  } catch {
    Message.error('加载实例详情失败')
  } finally { loading.value = false }
}

async function viewLog(taskId: number, taskName: string) {
  logLoading.value = true
  logVisible.value = true
  logContent.value = ''
  logTaskName.value = taskName
  try {
    const res: any = await getDSTaskLog(taskId)
    logContent.value = res.log || res.message || res.data || '暂无日志'
  } catch { logContent.value = '获取日志失败' }
  finally { logLoading.value = false }
}

async function handleRerun() {
  rerunLoading.value = true
  try {
    await rerunDSInstance(instanceId)
    Message.success('已触发重跑')
    setTimeout(loadData, 1500)
  } catch (e: any) {
    Message.error(e?.response?.data?.detail || '重跑失败')
  } finally { rerunLoading.value = false }
}

async function handleForcePass() {
  forcePassLoading.value = true
  try {
    // TODO: 调用强制通过 API（当前版本仅做前端提示）
    Message.success('已标记强制通过（请在 DolphinScheduler 中手动处理阻塞任务）')
  } catch (e: any) {
    Message.error(e?.response?.data?.detail || '操作失败')
  } finally { forcePassLoading.value = false }
}

function stateInfo(state: string) {
  return STATE_MAP[state] || { text: state, color: '#86909c', bg: '#f2f3f5' }
}

function formatTime(ts: string): string {
  const d = new Date(ts)
  if (isNaN(d.getTime())) return ts
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function formatDuration(s: number): string {
  if (s < 60) return `${s}s`
  const m = Math.floor(s / 60)
  return m < 60 ? `${m}m${s % 60}s` : `${Math.floor(m / 60)}h${m % 60}m`
}

function goWorkflow() {
  if (instance.value?.workflow_id) {
    router.push(`/workflows/${instance.value.workflow_id}/edit`)
  }
}
</script>

<template>
  <div class="detail-page">
    <!-- 顶部导航 -->
    <div class="detail-header">
      <a-button type="text" @click="router.back()">← 返回</a-button>
      <span class="detail-title">实例详情 #{{ instanceId }}</span>
      <div class="detail-actions">
        <a-button v-if="hasStrongFailure" type="outline" status="warning" size="small"
          :loading="forcePassLoading" @click="handleForcePass">
          强制通过
        </a-button>
        <a-button type="primary" size="small" :loading="rerunLoading" @click="handleRerun">重跑</a-button>
      </div>
    </div>

    <!-- 实例概览卡片 -->
    <div v-if="instance" class="instance-card">
      <div class="instance-card__header">
        <span class="instance-state" :style="{ color: stateInfo(instance.state).color, background: stateInfo(instance.state).bg }">
          {{ stateInfo(instance.state).text }}
        </span>
        <span v-if="hasStrongFailure" class="dqc-alert">质量异常</span>
        <a-button v-if="instance.workflow_id" type="text" size="mini" @click="goWorkflow">
          查看工作流 →
        </a-button>
      </div>
      <div class="instance-card__meta">
        <span>开始 {{ instance.start_time ? formatTime(instance.start_time) : '-' }}</span>
        <span>结束 {{ instance.end_time ? formatTime(instance.end_time) : '-' }}</span>
        <span>耗时 {{ instance.duration != null ? formatDuration(instance.duration) : '-' }}</span>
      </div>
    </div>

    <!-- DQC 质量检查结果 -->
    <div v-if="dqcResults.length" class="dqc-section">
      <div class="section-title">
        质量检查结果
        <span class="dqc-badge dqc-badge--pass">通过 {{ dqcPassedCount }}</span>
        <span v-if="dqcFailedCount" class="dqc-badge dqc-badge--fail">失败 {{ dqcFailedCount }}</span>
        <span v-if="dqcPendingCount" class="dqc-badge dqc-badge--pending">待检 {{ dqcPendingCount }}</span>
      </div>
      <div class="dqc-list">
        <div v-for="r in dqcResults" :key="r.rule_id" class="dqc-item"
          :class="{ 'dqc-item--fail': r.passed === false, 'dqc-item--pass': r.passed === true }">
          <div class="dqc-item__header">
            <span class="dqc-item__name">{{ r.rule_name }}</span>
            <span class="dqc-item__tag" :class="r.is_strong ? 'tag-strong' : 'tag-weak'">
              {{ r.is_strong ? '强' : '弱' }}
            </span>
            <span class="dqc-item__status" :class="r.passed === true ? 'status-pass' : r.passed === false ? 'status-fail' : 'status-pending'">
              {{ r.passed === true ? '通过' : r.passed === false ? '失败' : '未知' }}
            </span>
          </div>
          <div class="dqc-item__body">
            <div class="dqc-item__metric">
              <span class="metric-label">实际值</span>
              <span class="metric-value">{{ r.actual_value ?? '-' }}</span>
            </div>
            <div class="dqc-item__metric">
              <span class="metric-label">期望值</span>
              <span class="metric-value">{{ r.expected_value ?? '-' }}</span>
            </div>
            <div class="dqc-item__metric">
              <span class="metric-label">检查时间</span>
              <span class="metric-value">{{ r.checked_at ? formatTime(r.checked_at) : '-' }}</span>
            </div>
          </div>
          <!-- 失败采样 -->
          <div v-if="r.sample_data && r.sample_data.length" class="dqc-sample">
            <div class="dqc-sample__title">失败采样（{{ r.sample_data.length }} 条）</div>
            <div class="dqc-sample__scroll">
              <table class="dqc-sample__table">
                <thead>
                  <tr>
                    <th v-for="col in Object.keys(r.sample_data[0])" :key="col">{{ col }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, idx) in r.sample_data" :key="idx">
                    <td v-for="col in Object.keys(r.sample_data[0])" :key="col">{{ row[col] }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 任务时间线 -->
    <div class="detail-body">
      <div class="section-title">执行节点</div>
      <div v-if="loading" class="section-empty"><a-spin /></div>
      <div v-else-if="!tasks.length" class="section-empty">
        <a-empty description="暂无节点数据" />
      </div>
      <div v-else class="timeline">
        <div v-for="(task, idx) in tasks" :key="task.id" class="tl-item">
          <div class="tl-left">
            <div class="tl-dot"
              :style="{ background: stateInfo(task.state).color }"
              :class="{ 'tl-dot--pulse': task.state === 'RUNNING_EXECUTION' }">
            </div>
            <div v-if="idx < tasks.length - 1" class="tl-line"></div>
          </div>
          <div class="tl-card" :class="{ 'tl-card--dqc': task.name.startsWith('DQC:') }">
            <div class="tl-card__header">
              <span class="tl-name">{{ task.name }}</span>
              <span v-if="task.name.startsWith('DQC:')" class="tl-dqc-tag">DQC</span>
              <span class="tl-badge"
                :style="{ color: stateInfo(task.state).color, background: stateInfo(task.state).bg }">
                {{ stateInfo(task.state).text }}
              </span>
            </div>
            <div class="tl-card__meta">
              <span>开始 {{ task.startTime }}</span>
              <span>结束 {{ task.endTime }}</span>
              <span>耗时 {{ task.duration }}</span>
            </div>
            <div class="tl-card__actions">
              <a-button type="text" size="mini" @click="viewLog(task.id, task.name)">查看日志</a-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 日志弹窗 -->
    <a-modal v-model:visible="logVisible" :title="`任务日志 - ${logTaskName}`" :width="860" :footer="false">
      <a-spin :loading="logLoading" style="width:100%; min-height:200px">
        <pre class="log-pre">{{ logContent || '加载中...' }}</pre>
      </a-spin>
    </a-modal>
  </div>
</template>

<style scoped>
.detail-page { padding: 20px; max-width: 960px; }

.detail-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.detail-title { font-size: 18px; font-weight: 600; flex: 1; }
.detail-actions { display: flex; gap: 8px; }

/* 实例概览卡片 */
.instance-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px 20px; margin-bottom: 20px; }
.instance-card__header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.instance-state { padding: 3px 10px; border-radius: 10px; font-size: 12px; font-weight: 500; }
.dqc-alert { padding: 3px 10px; border-radius: 10px; font-size: 12px; font-weight: 500; color: #f53f3f; background: #ffece8; }
.instance-card__meta { display: flex; gap: 20px; font-size: 13px; color: #86909c; }

/* DQC 区域 */
.dqc-section { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
.dqc-badge { padding: 2px 8px; border-radius: 8px; font-size: 11px; font-weight: 500; margin-left: 8px; }
.dqc-badge--pass { color: #00b42a; background: #e8ffea; }
.dqc-badge--fail { color: #f53f3f; background: #ffece8; }
.dqc-badge--pending { color: #86909c; background: #f2f3f5; }

.dqc-list { display: flex; flex-direction: column; gap: 12px; margin-top: 16px; }
.dqc-item { border: 1px solid #e5e7eb; border-radius: 8px; padding: 14px 16px; }
.dqc-item--pass { border-left: 3px solid #00b42a; }
.dqc-item--fail { border-left: 3px solid #f53f3f; background: #fffafa; }
.dqc-item__header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.dqc-item__name { font-size: 14px; font-weight: 600; flex: 1; }
.dqc-item__tag { padding: 1px 6px; border-radius: 4px; font-size: 11px; font-weight: 500; }
.tag-strong { color: #f53f3f; background: #ffece8; }
.tag-weak { color: #86909c; background: #f2f3f5; }
.dqc-item__status { padding: 1px 8px; border-radius: 4px; font-size: 11px; font-weight: 500; }
.status-pass { color: #00b42a; background: #e8ffea; }
.status-fail { color: #f53f3f; background: #ffece8; }
.status-pending { color: #86909c; background: #f2f3f5; }

.dqc-item__body { display: flex; gap: 24px; flex-wrap: wrap; }
.dqc-item__metric { display: flex; flex-direction: column; gap: 2px; }
.metric-label { font-size: 11px; color: #86909c; }
.metric-value { font-size: 13px; font-weight: 500; color: #1d2129; }

.dqc-sample { margin-top: 12px; }
.dqc-sample__title { font-size: 12px; font-weight: 500; color: #4e5969; margin-bottom: 6px; }
.dqc-sample__scroll { overflow-x: auto; }
.dqc-sample__table { width: 100%; border-collapse: collapse; font-size: 12px; }
.dqc-sample__table th, .dqc-sample__table td { padding: 6px 10px; text-align: left; border: 1px solid #e5e7eb; white-space: nowrap; }
.dqc-sample__table th { background: #f7f8fa; font-weight: 500; color: #4e5969; }
.dqc-sample__table td { color: #1d2129; }

/* 时间线 */
.detail-body { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 24px; }
.section-title { font-size: 14px; font-weight: 600; color: #4e5969; margin-bottom: 20px; display: flex; align-items: center; }
.section-empty { display: flex; align-items: center; justify-content: center; height: 120px; }

.timeline { display: flex; flex-direction: column; }
.tl-item { display: flex; gap: 16px; }
.tl-left { display: flex; flex-direction: column; align-items: center; width: 20px; flex-shrink: 0; }
.tl-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; margin-top: 6px; }
.tl-dot--pulse { animation: pulse 1.5s ease-out infinite; }
.tl-line { flex: 1; width: 2px; background: #e5e7eb; min-height: 20px; margin: 4px 0; }

.tl-card { flex: 1; padding-bottom: 20px; }
.tl-card--dqc { background: #fafbfc; border-radius: 6px; padding: 10px 14px; margin-bottom: 10px; }
.tl-card__header { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
.tl-name { font-size: 14px; font-weight: 600; }
.tl-dqc-tag { padding: 1px 6px; border-radius: 4px; font-size: 11px; font-weight: 500; color: #165dff; background: #e8f3ff; }
.tl-badge { padding: 2px 10px; border-radius: 10px; font-size: 12px; font-weight: 500; }
.tl-card__meta { display: flex; gap: 16px; font-size: 12px; color: #86909c; margin-bottom: 8px; }
.tl-card__actions { display: flex; gap: 8px; }

@keyframes pulse {
  0%   { box-shadow: 0 0 0 0 rgba(22, 93, 255, 0.4); }
  70%  { box-shadow: 0 0 0 8px rgba(22, 93, 255, 0); }
  100% { box-shadow: 0 0 0 0 rgba(22, 93, 255, 0); }
}

.log-pre { margin: 0; font-size: 12px; line-height: 1.7; white-space: pre-wrap; word-break: break-all; background: #1a1a2e; color: #e2e8f0; padding: 16px; border-radius: 6px; max-height: 520px; overflow-y: auto; font-family: 'JetBrains Mono', Consolas, monospace; }
</style>
