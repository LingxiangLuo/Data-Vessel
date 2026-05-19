<template>
  <div class="page">
    <div class="glass-card page-header">
      <div>
        <h3 class="page-title">监控规则</h3>
        <p class="page-desc">配置告警规则，工作流异常时自动通知到已配置的通知渠道</p>
      </div>
      <a-button type="primary" @click="openCreate">
        <template #icon><icon-plus /></template>
        新建规则
      </a-button>
    </div>

    <div class="glass-card table-card">
      <a-table :data="rules" :loading="loading" :bordered="false" :pagination="false" stripe>
        <template #columns>
          <a-table-column title="规则名称" data-index="name" :width="180" />
          <a-table-column title="监控对象" :width="160">
            <template #cell="{ record }">
              <span v-if="record.target_type === 'all'" class="text-muted">所有工作流</span>
              <span v-else>{{ record.target_name || `工作流#${record.target_id}` }}</span>
            </template>
          </a-table-column>
          <a-table-column title="触发条件" :width="160">
            <template #cell="{ record }">
              <a-tag :color="triggerColor(record.trigger_type)" size="small">{{ triggerLabel(record) }}</a-tag>
            </template>
          </a-table-column>
          <a-table-column title="通知渠道" :width="200">
            <template #cell="{ record }">
              <template v-if="record.notify_channel_names && record.notify_channel_names.length">
                <a-space :size="4" wrap>
                  <a-tag v-for="name in record.notify_channel_names" :key="name" size="small" color="arcoblue">
                    {{ name }}
                  </a-tag>
                </a-space>
              </template>
              <span v-else class="text-muted">—</span>
            </template>
          </a-table-column>
          <a-table-column title="状态" :width="80">
            <template #cell="{ record }">
              <a-switch :model-value="record.enabled" size="small" @change="handleToggle(record)" />
            </template>
          </a-table-column>
          <a-table-column title="操作" :width="160">
            <template #cell="{ record }">
              <a-space :size="4">
                <a-button type="text" size="mini" @click="openEdit(record)">编辑</a-button>
                <a-button type="text" size="mini" @click="handleTest(record)">测试</a-button>
                <a-button type="text" size="mini" status="danger" @click="handleDelete(record)">删除</a-button>
              </a-space>
            </template>
          </a-table-column>
        </template>
        <template #empty>
          <div class="empty-state">
            <p>暂无监控规则</p>
            <p class="text-muted">点击「新建规则」配置工作流异常告警</p>
          </div>
        </template>
      </a-table>
    </div>

    <!-- 新建/编辑模态框 -->
    <a-modal
      v-model:visible="modalVisible"
      :title="editingId ? '编辑规则' : '新建规则'"
      :width="560"
      @ok="handleSave"
      :unmount-on-close="true"
    >
      <a-form :model="form" layout="vertical">
        <a-form-item label="规则名称" required>
          <a-input v-model="form.name" placeholder="例如：ODS同步失败告警" />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="监控对象">
              <a-select v-model="form.target_type">
                <a-option value="all">所有工作流</a-option>
                <a-option value="workflow">指定工作流</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12" v-if="form.target_type === 'workflow'">
            <a-form-item label="选择工作流">
              <a-select v-model="form.target_id" placeholder="选择" allow-search>
                <a-option v-for="w in workflows" :key="w.id" :value="w.id">{{ w.name }}</a-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="触发条件">
              <a-select v-model="form.trigger_type">
                <a-option value="failure">运行失败</a-option>
                <a-option value="timeout">运行超时</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12" v-if="form.trigger_type === 'timeout'">
            <a-form-item label="超时阈值（秒）">
              <a-input-number v-model="form.trigger_value" :min="60" :step="60" placeholder="600" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="通知渠道" required>
          <a-select
            v-model="form.notify_channel_ids"
            multiple
            placeholder="选择一个或多个通知渠道"
            allow-search
            :loading="channelsLoading"
            :max-tag-count="3"
          >
            <a-option v-for="ch in channels" :key="ch.id" :value="ch.id" :disabled="!ch.enabled">
              <a-space :size="6">
                <a-tag :color="typeColor(ch.type)" size="small">{{ typeLabel(ch.type) }}</a-tag>
                <span>{{ ch.name }}</span>
                <span v-if="!ch.enabled" class="text-muted">（已停用）</span>
              </a-space>
            </a-option>
          </a-select>
          <div class="field-hint">
            在
            <a-link @click="goToNotifyConfig">通知配置</a-link>
            中管理渠道
          </div>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import { IconPlus } from '@arco-design/web-vue/es/icon'
import { useRouter } from 'vue-router'
import {
  getAlertRules, createAlertRule, updateAlertRule, deleteAlertRule,
  toggleAlertRule, testAlertNotify, getWorkflows, adminListChannels,
} from '../api'

interface Rule {
  id: number
  name: string
  target_type: string
  target_id?: number
  target_name?: string
  trigger_type: string
  trigger_value?: number
  notify_channel_ids: number[]
  notify_channel_names: string[]
  enabled: boolean
}

interface Channel {
  id: number
  name: string
  type: string
  enabled: boolean
}

const router = useRouter()
const loading = ref(false)
const channelsLoading = ref(false)
const rules = ref<Rule[]>([])
const workflows = ref<any[]>([])
const channels = ref<Channel[]>([])
const modalVisible = ref(false)
const editingId = ref<number | null>(null)

const form = ref({
  name: '',
  target_type: 'all',
  target_id: undefined as number | undefined,
  trigger_type: 'failure',
  trigger_value: 600,
  notify_channel_ids: [] as number[],
})

const typeColor = (t: string) =>
  ({ feishu_webhook: 'blue', dingtalk_webhook: 'cyan', wecom_webhook: 'green', email: 'orange' } as any)[t] || 'gray'
const typeLabel = (t: string) =>
  ({ feishu_webhook: '飞书', dingtalk_webhook: '钉钉', wecom_webhook: '企微', email: '邮件' } as any)[t] || t

function triggerColor(t: string) {
  return ({ failure: 'red', timeout: 'orange', consecutive_failure: 'purple' } as any)[t] || 'gray'
}
function triggerLabel(r: Rule) {
  if (r.trigger_type === 'failure') return '运行失败'
  if (r.trigger_type === 'timeout') return `超时 > ${r.trigger_value || 0}s`
  if (r.trigger_type === 'consecutive_failure') return `连续失败 ${r.trigger_value} 次`
  return r.trigger_type
}

function goToNotifyConfig() {
  router.push('/admin/notify')
}

async function loadData() {
  loading.value = true
  try {
    const res: any = await getAlertRules()
    rules.value = res?.items || []
  } catch { rules.value = [] }
  loading.value = false
}

async function loadWorkflows() {
  try {
    const res: any = await getWorkflows({ page: 1, page_size: 200 })
    workflows.value = res?.items || []
  } catch {}
}

async function loadChannels() {
  channelsLoading.value = true
  try {
    const res: any = await adminListChannels()
    channels.value = Array.isArray(res) ? res : (res?.items || [])
  } catch { channels.value = [] }
  channelsLoading.value = false
}

function openCreate() {
  editingId.value = null
  form.value = { name: '', target_type: 'all', target_id: undefined, trigger_type: 'failure', trigger_value: 600, notify_channel_ids: [] }
  modalVisible.value = true
}

function openEdit(r: Rule) {
  editingId.value = r.id
  form.value = {
    name: r.name,
    target_type: r.target_type,
    target_id: r.target_id,
    trigger_type: r.trigger_type,
    trigger_value: r.trigger_value || 600,
    notify_channel_ids: r.notify_channel_ids || [],
  }
  modalVisible.value = true
}

async function handleSave() {
  if (!form.value.name.trim()) { Message.warning('请填写规则名称'); return }
  if (!form.value.notify_channel_ids.length) { Message.warning('请选择至少一个通知渠道'); return }

  const payload = {
    name: form.value.name.trim(),
    target_type: form.value.target_type,
    target_id: form.value.target_type === 'workflow' ? form.value.target_id : undefined,
    trigger_type: form.value.trigger_type,
    trigger_value: form.value.trigger_type === 'timeout' ? form.value.trigger_value : undefined,
    notify_channel_ids: form.value.notify_channel_ids,
  }
  try {
    if (editingId.value) {
      await updateAlertRule(editingId.value, payload)
      Message.success('已更新')
    } else {
      await createAlertRule(payload)
      Message.success('已创建')
    }
    modalVisible.value = false
    loadData()
  } catch {}
}

async function handleToggle(r: Rule) {
  try {
    await toggleAlertRule(r.id)
    loadData()
  } catch {}
}

async function handleTest(r: Rule) {
  if (!r.notify_channel_ids?.length) {
    Message.warning('该规则未配置通知渠道')
    return
  }
  try {
    await testAlertNotify({ channel_ids: r.notify_channel_ids })
    Message.success('测试通知已发送，请检查接收端')
  } catch (e: any) {
    Message.error(e?.response?.data?.detail || '发送失败')
  }
}

function handleDelete(r: Rule) {
  Modal.confirm({
    title: '删除规则',
    content: `确认删除「${r.name}」?`,
    onOk: async () => {
      try { await deleteAlertRule(r.id); Message.success('已删除'); loadData() } catch {}
    },
  })
}

onMounted(() => { loadData(); loadWorkflows(); loadChannels() })
</script>

<style scoped>
.page { animation: fadeIn 0.3s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

.page-header { padding: 20px 24px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { margin: 0; font-size: 18px; font-weight: 600; color: #1D2129; }
.page-desc { margin: 4px 0 0; font-size: 13px; color: #86909C; }

.table-card { padding: 0; overflow: auto; }
.text-muted { color: #86909C; }
.empty-state { padding: 40px 0; text-align: center; }
.field-hint { margin-top: 4px; font-size: 12px; color: #86909C; }

:deep(.arco-table-th) { background: #FAFBFC !important; }
</style>
