<template>
  <div class="page">
    <div class="glass-card page-header">
      <div>
        <h3 class="page-title">工作流开发</h3>
        <p class="page-desc">DAG 工作流 — 组合多个组件形成可调度的有向无环图</p>
      </div>
      <a-space>
        <a-input-search
          v-model="searchVal"
          placeholder="搜索工作流名"
          style="width: 200px;"
          @search="loadData"
          allow-clear
          @clear="loadData"
        />
        <a-button type="primary" @click="openCreate">
          <template #icon><icon-plus /></template>
          新建工作流
        </a-button>
      </a-space>
    </div>

    <!-- 状态筛选 -->
    <div class="filter-tabs">
      <div class="tab-item" :class="{ active: statusFilter === '' }" @click="setStatus('')">全部 {{ total }}</div>
      <div class="tab-item" :class="{ active: statusFilter === 'draft' }" @click="setStatus('draft')">草稿</div>
      <div class="tab-item" :class="{ active: statusFilter === 'tested' }" @click="setStatus('tested')">已测试</div>
      <div class="tab-item online" :class="{ active: statusFilter === 'online' }" @click="setStatus('online')">已上线</div>
      <div class="tab-item" :class="{ active: statusFilter === 'offline' }" @click="setStatus('offline')">已下线</div>
    </div>

    <!-- 标签筛选 -->
    <div v-if="allTags.length" class="tag-filter-bar">
      <span class="tag-filter-label">标签：</span>
      <span class="tag-chip" :class="{ active: tagFilter === '' }" @click="setTag('')">全部</span>
      <span v-for="t in allTags" :key="t" class="tag-chip" :class="{ active: tagFilter === t }" @click="setTag(t)">{{ t }}</span>
    </div>

    <!-- 表格 -->
    <div class="glass-card table-card">
      <a-table :data="items" :loading="loading" :bordered="false" :pagination="false" stripe :scroll="{ x: 1100 }">
        <template #columns>
          <a-table-column title="工作流名" :width="200">
            <template #cell="{ record }">
              <a-tooltip :content="record.description || '无描述'" position="top" mini>
                <span class="wf-name-link" @click="openEdit(record)">{{ record.name }}</span>
              </a-tooltip>
              <span class="wf-version">v{{ record.version }}</span>
            </template>
          </a-table-column>
          <a-table-column title="优先级" :width="70">
            <template #cell="{ record }">
              <span :class="'priority-badge p' + (record.priority || 3)">{{ priorityLabel(record.priority) }}</span>
            </template>
          </a-table-column>
          <a-table-column title="状态" :width="100">
            <template #cell="{ record }">
              <span class="combined-status">
                <a-tag :color="statusColor(record.status)" size="small">{{ statusLabel(record.status) }}</a-tag>
                <span v-if="record.status === 'online' && record.schedule_status === 'ONLINE'" class="schedule-dot active" title="调度中"></span>
                <span v-else-if="record.status === 'online'" class="schedule-dot" title="调度停"></span>
              </span>
            </template>
          </a-table-column>
          <a-table-column title="最近运行" :width="150">
            <template #cell="{ record }">
              <span v-if="record.last_run_status" class="run-cell">
                <span :class="'run-icon ' + runClass(record.last_run_status)">{{ runSymbol(record.last_run_status) }}</span>
                <span class="mono text-muted">{{ relativeDate(record.last_run_time) }}</span>
              </span>
              <span v-else class="text-muted">— 从未运行</span>
            </template>
          </a-table-column>
          <a-table-column title="耗时" :width="80">
            <template #cell="{ record }">
              <span class="mono text-muted">{{ fmtDuration(record.last_run_duration) }}</span>
            </template>
          </a-table-column>
          <a-table-column title="下次执行" :width="120">
            <template #cell="{ record }">
              <span class="mono text-muted">{{ relativeDate(record.next_fire_time) }}</span>
            </template>
          </a-table-column>
          <a-table-column title="标签" :width="130">
            <template #cell="{ record }">
              <a-space :size="4" wrap>
                <a-tag v-for="t in (record.tags || [])" :key="t" size="small" color="arcoblue">{{ t }}</a-tag>
                <span v-if="!record.tags?.length" class="text-muted">—</span>
              </a-space>
            </template>
          </a-table-column>
          <a-table-column title="操作" :width="200" fixed="right">
            <template #cell="{ record }">
              <a-space :size="4">
                <a-button type="text" size="mini" @click="openEdit(record)">编辑</a-button>
                <a-button type="text" size="mini" status="success" @click="runWf(record)" :disabled="!record.ds_process_code">运行</a-button>
                <a-dropdown>
                  <a-button type="text" size="mini">更多</a-button>
                  <template #content>
                    <a-doption @click="testWf(record)" :disabled="!canTest(record)">测试</a-doption>
                    <a-doption v-if="record.status !== 'online'" @click="publishWf(record)" :disabled="!canPublish(record)">发布</a-doption>
                    <a-doption v-else @click="offlineWf(record)">下线</a-doption>
                    <a-doption v-if="record.status === 'online' && record.schedule_status !== 'ONLINE'" @click="scheduleOn(record)">开启调度</a-doption>
                    <a-doption v-if="record.schedule_status === 'ONLINE'" @click="scheduleOff(record)">关闭调度</a-doption>
                    <a-doption :disabled="!canDelete(record)" @click="deleteWf(record)">删除</a-doption>
                  </template>
                </a-dropdown>
              </a-space>
            </template>
          </a-table-column>
        </template>
        <template #empty>
          <div class="empty-state">
            <p>暂无工作流</p>
            <p class="text-muted">点击「新建工作流」串联已发布的组件成一条流水线</p>
          </div>
        </template>
      </a-table>
      <div class="pagination-wrap" v-if="total > pageSize">
        <a-pagination v-model:current="page" :total="total" :page-size="pageSize" show-total @change="loadData" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Message, Modal } from '@arco-design/web-vue'
import { IconPlus } from '@arco-design/web-vue/es/icon'
import {
  getWorkflows, deleteWorkflow,
  testWorkflow, publishWorkflow, offlineWorkflow, runWorkflow,
  scheduleWorkflowOnline, scheduleWorkflowOffline,
} from '../api'
import { relativeDate, formatDuration } from '../utils/time'

interface Workflow {
  id: number
  name: string
  description?: string
  tags?: string[]
  status: string
  version: number
  priority?: number
  schedule_status: string
  cron_expression?: string
  last_run_status?: string
  last_run_time?: string
  last_run_duration?: number
  next_fire_time?: string
  ds_process_code?: number | null
}

const router = useRouter()
const loading = ref(false)
const items = ref<Workflow[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const searchVal = ref('')
const statusFilter = ref('')
const tagFilter = ref('')
const allTags = ref<string[]>([])

// ===== 工具函数 =====
function priorityLabel(p?: number) {
  return ({ 1: 'P1', 2: 'P2', 3: 'P3' } as any)[p || 3] || 'P3'
}
function statusColor(s: string) {
  return ({ draft: 'gray', tested: 'cyan', online: 'green', offline: 'orange' } as any)[s] || 'gray'
}
function statusLabel(s?: string) {
  if (!s) return '未知'
  return ({ draft: '草稿', tested: '已测试', online: '已上线', offline: '已下线' } as any)[s] || s
}
function runSymbol(s?: string) {
  if (!s) return ''
  if (s === 'SUCCESS') return '✓'
  if (s === 'FAILURE') return '✗'
  return '●'
}
function runClass(s?: string) {
  if (s === 'SUCCESS') return 'success'
  if (s === 'FAILURE') return 'failure'
  return 'running'
}
function fmtDuration(s?: number | null) {
  return formatDuration(s ?? null)
}

function canTest(w: Workflow) { return w.status === 'draft' || w.status === 'tested' }
function canPublish(w: Workflow) { return w.status === 'tested' }
function canDelete(w: Workflow) { return w.status === 'draft' || w.status === 'offline' }

function setStatus(s: string) { statusFilter.value = s; loadData() }
function setTag(t: string) { tagFilter.value = t; loadData() }

// ===== 数据加载 =====
async function loadData() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (searchVal.value) params.keyword = searchVal.value
    if (statusFilter.value) params.status = statusFilter.value
    if (tagFilter.value) params.tag = tagFilter.value
    const res: any = await getWorkflows(params)
    items.value = res?.items || []
    total.value = res?.total || 0
    if (res?.all_tags) allTags.value = res.all_tags
  } catch {
    items.value = []
    total.value = 0
    Message.error('加载工作流列表失败')
  }
  loading.value = false
}

// ===== 操作 =====
function openCreate() { router.push('/workflows/new/edit') }
function openEdit(w: Workflow) { router.push(`/workflows/${w.id}/edit`) }

function testWf(w: Workflow) {
  Modal.confirm({
    title: '测试工作流',
    content: '将检查所有组件状态并触发试运行,确认?',
    onOk: async () => {
      try { await testWorkflow(w.id); Message.success('测试通过'); loadData() } catch {}
    },
  })
}

function publishWf(w: Workflow) {
  Modal.confirm({
    title: '发布工作流',
    content: `「${w.name}」将发布上线,确认?`,
    onOk: async () => {
      try { await publishWorkflow(w.id); Message.success('已发布'); loadData() } catch {}
    },
  })
}

function offlineWf(w: Workflow) {
  Modal.confirm({
    title: '下线工作流',
    content: `确认下线「${w.name}」?调度也会自动停止`,
    onOk: async () => {
      try { await offlineWorkflow(w.id); Message.success('已下线'); loadData() } catch {}
    },
  })
}

function runWf(w: Workflow) {
  Modal.confirm({
    title: '手动运行',
    content: `立即运行「${w.name}」?`,
    onOk: async () => {
      try { await runWorkflow(w.id); Message.success('已触发运行'); loadData() } catch {}
    },
  })
}

function scheduleOn(w: Workflow) {
  if (!w.cron_expression) { Message.info('请先配置调度'); router.push(`/workflows/${w.id}/edit`); return }
  Modal.confirm({
    title: '开启调度',
    content: `按 CRON「${w.cron_expression}」开启自动调度?`,
    onOk: async () => {
      try { await scheduleWorkflowOnline(w.id); Message.success('调度已开启'); loadData() } catch {}
    },
  })
}

function scheduleOff(w: Workflow) {
  Modal.confirm({
    title: '关闭调度',
    content: `关闭「${w.name}」的自动调度?`,
    onOk: async () => {
      try { await scheduleWorkflowOffline(w.id); Message.success('调度已关闭'); loadData() } catch {}
    },
  })
}

function deleteWf(w: Workflow) {
  Modal.confirm({
    title: '删除工作流',
    content: `确认删除「${w.name}」?该操作不可恢复`,
    onOk: async () => {
      try { await deleteWorkflow(w.id); Message.success('已删除'); loadData() } catch {}
    },
  })
}

onMounted(() => { loadData() })
</script>

<style scoped>
.page { animation: fadeIn 0.3s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

.page-header { padding: 20px 24px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { margin: 0; font-size: 18px; font-weight: 600; color: #1D2129; }
.page-desc { margin: 4px 0 0; font-size: 13px; color: #86909C; }

.filter-tabs { display: flex; gap: 4px; margin-bottom: 8px; }
.tab-item {
  padding: 6px 16px; border-radius: 6px; font-size: 13px; cursor: pointer;
  color: #4E5969; background: #F7F8FA; transition: all 0.15s;
}
.tab-item:hover { background: #EFF4FF; color: #2B5AED; }
.tab-item.active { background: #2B5AED; color: #FFFFFF; }
.tab-item.online.active { background: #00B42A; }
.tag-filter-bar { display: flex; align-items: center; gap: 6px; margin-bottom: 16px; flex-wrap: wrap; }
.tag-filter-label { font-size: 12px; color: #86909c; }
.tag-chip { padding: 3px 10px; border-radius: 10px; font-size: 12px; cursor: pointer; background: #f2f3f5; color: #4e5969; transition: all 0.15s; }
.tag-chip:hover { background: #e8f3ff; color: #165dff; }
.tag-chip.active { background: #165dff; color: #fff; }

.table-card { padding: 0; overflow: auto; }
.wf-name-link { font-weight: 500; color: #165dff; cursor: pointer; }
.wf-name-link:hover { text-decoration: underline; }
.wf-version {
  margin-left: 6px; font-size: 11px; color: #86909C;
  font-family: 'JetBrains Mono', monospace;
}

/* 优先级 */
.priority-badge {
  display: inline-block; padding: 1px 6px; border-radius: 3px;
  font-size: 11px; font-weight: 600; font-family: 'JetBrains Mono', monospace;
}
.priority-badge.p1 { background: #FFECE8; color: #F53F3F; }
.priority-badge.p2 { background: #FFF7E8; color: #FF7D00; }
.priority-badge.p3 { background: #F2F3F5; color: #86909C; }

/* 状态 + 调度点 */
.combined-status { display: inline-flex; align-items: center; gap: 4px; }
.schedule-dot {
  width: 6px; height: 6px; border-radius: 50%; background: #C9CDD4;
}
.schedule-dot.active { background: #00B42A; animation: pulse 2s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

/* 运行状态 */
.run-cell { display: inline-flex; align-items: center; gap: 4px; white-space: nowrap; }
.run-icon { font-size: 13px; font-weight: 600; }
.run-icon.success { color: #00B42A; }
.run-icon.failure { color: #F53F3F; }
.run-icon.running { color: #165DFF; }

.mono { font-family: 'JetBrains Mono', monospace; font-size: 12px; }
.text-muted { color: #86909C; }
.empty-state { padding: 40px 0; text-align: center; }
.pagination-wrap { padding: 16px 24px; display: flex; justify-content: flex-end; border-top: 1px solid #F2F3F5; }
:deep(.arco-table-th) { background: #FAFBFC !important; }
</style>
