<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { IconClockCircle } from '@arco-design/web-vue/es/icon'
import DagCanvas from '../components/dag/DagCanvas.vue'
import DagNodePanel from '../components/dag/DagNodePanel.vue'
import DagToolbar from '../components/dag/DagToolbar.vue'
import ScheduleModal from '../components/ScheduleModal.vue'
import { getWorkflow, createWorkflow, updateWorkflow, testWorkflow, publishWorkflow, runWorkflow } from '../api'

interface DagNode { id: string; component_id: number; type?: string; name: string; position: { x: number; y: number }; skip: boolean }
interface DagEdge { id: string; source: string; target: string }

const route = useRoute()
const router = useRouter()
const dagCanvas = ref<InstanceType<typeof DagCanvas>>()

const workflowId = ref<number | null>(null)
const workflowName = ref('')
const workflowDesc = ref('')
const workflowStatus = ref('draft')
const cronExpression = ref('')
const scheduleStatus = ref('OFFLINE')
const workflowTags = ref<string[]>([])
const tagInput = ref('')
const workflowPriority = ref(3)
const dagNodes = ref<DagNode[]>([])
const dagEdges = ref<DagEdge[]>([])
const loading = ref(false)
const scheduleModalVisible = ref(false)

// 人类可读的调度描述
const cronHumanReadable = computed(() => {
  const cron = cronExpression.value
  if (!cron) return ''
  const parts = cron.trim().split(/\s+/)
  const p = parts.length === 6 ? parts.slice(1) : parts
  if (p.length < 5) return '自定义'
  const [min, hr, dom, , dow] = p
  const everyDay  = (dom === '*' || dom === '?') && (dow === '*' || dow === '?')
  const everyHour = hr === '*' || hr === '?'
  const everyMin  = min === '*' || min === '?'
  if (everyDay && everyHour && everyMin) return '每分钟'
  if (everyDay && everyHour) return `每小时第 ${min} 分`
  const time = `${String(parseInt(hr)).padStart(2, '0')}:${String(parseInt(min)).padStart(2, '0')}`
  if (everyDay) {
    return `每天 ${time}`
  }
  if ((dom === '?' || dom === '*') && dow !== '*' && dow !== '?') {
    const dayNames = ['', '一', '二', '三', '四', '五', '六', '日']
    const days = dow.split(',').map((d: string) => dayNames[+d] || d).join('')
    return `每周${days} ${time}`
  }
  if ((dow === '?' || dow === '*') && dom !== '*' && dom !== '?') {
    return `每月${dom}日 ${time}`
  }
  return '自定义 CRON'
})

onMounted(async () => {
  const id = route.params.id as string
  if (id && id !== 'new') {
    workflowId.value = parseInt(id)
    await loadWorkflow()
  }
})

async function loadWorkflow() {
  if (!workflowId.value) return
  let res: any
  try {
    res = await getWorkflow(workflowId.value)
  } catch (e: any) {
    Message.error(e?.response?.data?.detail || '加载工作流失败')
    return
  }
  workflowName.value = res.name
  workflowDesc.value = res.description || ''
  workflowStatus.value = res.status
  cronExpression.value = res.cron_expression || ''
  scheduleStatus.value = res.schedule_status || 'OFFLINE'
  workflowTags.value = res.tags || []
  workflowPriority.value = res.priority || 3
  if (res.dag && res.dag.nodes) {
    dagNodes.value = res.dag.nodes
    dagEdges.value = res.dag.edges || []
  } else if (res.steps && res.steps.length) {
    dagNodes.value = res.steps.map((s: any, i: number) => ({
      id: `node-${i+1}`, component_id: s.component_id, type: s.component_type || 'sql', name: s.name || s.component_name,
      position: { x: 200 + i * 220, y: 200 }, skip: false,
    }))
    dagEdges.value = res.steps.slice(1).map((s: any, i: number) => ({
      id: `edge-${i+1}`, source: `node-${i+1}`, target: `node-${i+2}`,
    }))
  }
}

function onDagUpdate(dag: { nodes: DagNode[]; edges: DagEdge[] }) {
  dagNodes.value = dag.nodes
  dagEdges.value = dag.edges
}

async function onScheduleSave(cron: string) {
  cronExpression.value = cron
  if (!workflowId.value) return
  try {
    await updateWorkflow(workflowId.value, { cron_expression: cron })
  } catch {}
}

async function handleSave() {
  if (!workflowName.value.trim()) { Message.warning('请输入工作流名称'); return }
  loading.value = true
  try {
    const payload = {
      name: workflowName.value,
      description: workflowDesc.value || null,
      cron_expression: cronExpression.value || null,
      tags: workflowTags.value,
      priority: workflowPriority.value,
      dag: { nodes: dagNodes.value, edges: dagEdges.value },
    }
    if (workflowId.value) {
      await updateWorkflow(workflowId.value, payload)
      Message.success('保存成功')
    } else {
      const res: any = await createWorkflow(payload)
      workflowId.value = res.id
      workflowStatus.value = res.status
      router.replace(`/workflows/${res.id}/edit`)
      Message.success('创建成功')
    }
    await loadWorkflow()
  } catch (e: any) {
    Message.error(e?.response?.data?.detail || '保存失败')
  } finally { loading.value = false }
}

async function handleTest() {
  if (!workflowId.value) { Message.warning('请先保存'); return }
  try {
    await testWorkflow(workflowId.value)
    await loadWorkflow()
    Message.success('测试通过')
  } catch (e: any) { Message.error(e?.response?.data?.detail || '测试失败') }
}

async function handlePublish() {
  if (!workflowId.value) return
  try {
    await publishWorkflow(workflowId.value)
    await loadWorkflow()
    Message.success('发布成功')
  } catch (e: any) { Message.error(e?.response?.data?.detail || '发布失败') }
}

async function handleRun() {
  if (!workflowId.value) return
  try {
    await runWorkflow(workflowId.value)
    Message.success('已触发运行')
  } catch (e: any) { Message.error(e?.response?.data?.detail || '运行失败') }
}

function handleBack() { router.push('/workflows') }
function handleAutoLayout() { dagCanvas.value?.autoLayout() }
</script>

<template>
  <div class="workflow-editor">
    <DagToolbar
      :workflow-name="workflowName"
      :status="workflowStatus"
      @save="handleSave" @test="handleTest" @publish="handlePublish"
      @run="handleRun" @back="handleBack" @auto-layout="handleAutoLayout"
    />
    <div class="workflow-editor__meta">
      <input v-model="workflowName" placeholder="工作流名称" class="workflow-editor__name-input" />
      <input v-model="workflowDesc" placeholder="描述（可选）" class="workflow-editor__desc-input" />
      <select v-model="workflowPriority" class="workflow-editor__priority-select">
        <option :value="1">P1 高</option>
        <option :value="2">P2 中</option>
        <option :value="3">P3 低</option>
      </select>
      <div class="schedule-trigger" @click="scheduleModalVisible = true">
        <icon-clock-circle style="font-size: 14px;" />
        <span v-if="cronHumanReadable" class="schedule-text">{{ cronHumanReadable }}</span>
        <span v-else class="schedule-placeholder">设置调度</span>
        <span v-if="cronExpression" class="schedule-dot" :class="{ active: scheduleStatus === 'ONLINE' }"></span>
      </div>
      <div class="workflow-editor__tags">
        <span v-for="t in workflowTags" :key="t" class="tag-chip-edit">
          {{ t }}
          <span class="tag-remove" @click="workflowTags = workflowTags.filter(x => x !== t)">×</span>
        </span>
        <input
          v-model="tagInput"
          placeholder="+ 添加标签"
          class="tag-add-input"
          @keydown.enter.prevent="() => { const v = tagInput.trim(); if(v && !workflowTags.includes(v)) workflowTags.push(v); tagInput = '' }"
          @keydown.backspace="() => { if(!tagInput && workflowTags.length) workflowTags.pop() }"
        />
      </div>
    </div>
    <div class="workflow-editor__body">
      <DagNodePanel />
      <DagCanvas ref="dagCanvas" :nodes="dagNodes" :edges="dagEdges" @update="onDagUpdate" />
    </div>

    <ScheduleModal
      :visible="scheduleModalVisible"
      :cron-expression="cronExpression"
      :schedule-status="scheduleStatus"
      @update:visible="scheduleModalVisible = $event"
      @save="onScheduleSave"
    />
  </div>
</template>

<style scoped>
.workflow-editor { display: flex; flex-direction: column; height: 100vh; background: #f7f8fa; }
.workflow-editor__meta { display: flex; gap: 12px; padding: 8px 16px; background: #fff; border-bottom: 1px solid #e5e7eb; align-items: center; }
.workflow-editor__name-input { flex: 1; max-width: 300px; padding: 6px 10px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 14px; }
.workflow-editor__desc-input { flex: 1; max-width: 240px; padding: 6px 10px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 13px; color: #666; }
.workflow-editor__priority-select { width: 80px; padding: 6px 8px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 13px; color: #333; background: #fff; cursor: pointer; }

.schedule-trigger {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 12px; border: 1px solid #E5E8ED; border-radius: 6px;
  cursor: pointer; background: #FAFBFC; transition: all 0.15s;
  white-space: nowrap;
}
.schedule-trigger:hover { border-color: #165DFF; background: #F2F7FF; }
.schedule-text { font-size: 13px; color: #1D2129; font-weight: 500; }
.schedule-placeholder { font-size: 13px; color: #C9CDD4; }
.schedule-dot {
  width: 6px; height: 6px; border-radius: 50%; background: #C9CDD4; margin-left: 2px;
}
.schedule-dot.active { background: #00B42A; animation: pulse 2s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

.workflow-editor__tags { display: flex; align-items: center; flex-wrap: wrap; gap: 4px; border: 1px solid #d9d9d9; border-radius: 4px; padding: 3px 8px; min-width: 160px; background: #fff; }
.tag-chip-edit { display: inline-flex; align-items: center; gap: 3px; background: #e8f3ff; color: #165dff; padding: 1px 6px; border-radius: 10px; font-size: 12px; }
.tag-remove { cursor: pointer; font-size: 14px; line-height: 1; opacity: 0.6; }
.tag-remove:hover { opacity: 1; }
.tag-add-input { border: none; outline: none; font-size: 12px; color: #666; min-width: 80px; background: transparent; }
.workflow-editor__body { flex: 1; display: flex; overflow: hidden; }
</style>
