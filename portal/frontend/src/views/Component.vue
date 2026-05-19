<template>
  <div class="page">
    <div class="glass-card page-header">
      <div>
        <h3 class="page-title">组件管理</h3>
        <p class="page-desc">SQL / Python / Shell / DataX 统一组件,经 DSL Translator 翻译为底层任务</p>
      </div>
      <a-space>
        <a-input-search
          v-model="searchVal"
          placeholder="搜索组件名"
          style="width: 200px;"
          @search="loadData"
          allow-clear
          @clear="loadData"
        />
        <a-select v-model="typeFilter" placeholder="全部类型" style="width: 130px;" allow-clear @change="loadData">
          <a-option value="sql">SQL</a-option>
          <a-option value="python">Python</a-option>
          <a-option value="shell">Shell</a-option>
          <a-option value="datax">DataX</a-option>
        </a-select>
        <a-button type="primary" @click="openCreate">
          <template #icon><icon-plus /></template>
          新建组件
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

    <!-- 表格 -->
    <div class="glass-card table-card">
      <a-table :data="items" :loading="loading" :bordered="false" :pagination="false" stripe>
        <template #columns>
          <a-table-column title="组件名" data-index="name" :width="240">
            <template #cell="{ record }">
              <span class="comp-name">{{ record.name }}</span>
              <span class="comp-version">v{{ record.version }}</span>
            </template>
          </a-table-column>
          <a-table-column title="类型" :width="100">
            <template #cell="{ record }">
              <a-tag :color="typeColor(record.type)" size="small">{{ typeLabel(record.type) }}</a-tag>
            </template>
          </a-table-column>
          <a-table-column title="状态" :width="100">
            <template #cell="{ record }">
              <a-tag :color="statusColor(record.status)" size="small">{{ statusLabel(record.status) }}</a-tag>
            </template>
          </a-table-column>
          <a-table-column title="描述" data-index="description" :width="180" :ellipsis="true" :tooltip="true" />
          <a-table-column title="更新时间" :width="150">
            <template #cell="{ record }">
              <span class="mono text-muted">{{ formatTime(record.updated_at) }}</span>
            </template>
          </a-table-column>
          <a-table-column title="操作" :width="260" fixed="right">
            <template #cell="{ record }">
              <a-space :size="4">
                <a-button type="text" size="mini" @click="openEdit(record)" :disabled="!canEdit(record)">编辑</a-button>
                <a-button type="text" size="mini" status="success" @click="testComp(record)" :disabled="!canTest(record)">测试</a-button>
                <a-button v-if="record.status !== 'online'" type="text" size="mini" @click="publishComp(record)" :disabled="!canPublish(record)">发布</a-button>
                <a-button v-else type="text" size="mini" status="warning" @click="offlineComp(record)">下线</a-button>
                <a-dropdown>
                  <a-button type="text" size="mini">更多</a-button>
                  <template #content>
                    <a-doption @click="runComp(record)">运行</a-doption>
                    <a-doption @click="viewComp(record)">查看</a-doption>
                    <a-doption :disabled="!canDelete(record)" @click="deleteComp(record)">删除</a-doption>
                  </template>
                </a-dropdown>
              </a-space>
            </template>
          </a-table-column>
        </template>
        <template #empty>
          <div class="empty-state">
            <p>暂无组件</p>
            <p class="text-muted">点击「新建组件」创建第一个 SQL / Python / Shell / DataX 组件</p>
          </div>
        </template>
      </a-table>
      <div class="pagination-wrap" v-if="total > pageSize">
        <a-pagination v-model:current="page" :total="total" :page-size="pageSize" show-total @change="loadData" />
      </div>
    </div>

    <!-- 编辑器模态框 -->
    <a-modal
      v-model:visible="editorVisible"
      :title="editorTitle"
      :width="900"
      :ok-text="readonlyMode ? '关闭' : '保存'"
      :hide-cancel="readonlyMode"
      @ok="handleSave"
      @cancel="editorVisible = false"
      :unmount-on-close="true"
    >
      <a-form :model="form" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="组件名" required>
              <a-input v-model="form.name" placeholder="例如:extract_user_daily" :disabled="readonlyMode" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="类型" required>
              <a-select v-model="form.type" :disabled="isEditMode || readonlyMode" @change="onTypeChange">
                <a-option value="sql">SQL</a-option>
                <a-option value="python">Python</a-option>
                <a-option value="shell">Shell</a-option>
                <a-option value="datax">DataX (JSON)</a-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="描述">
          <a-input v-model="form.description" placeholder="可选" :disabled="readonlyMode" />
        </a-form-item>

        <!-- 类型特定配置 -->
        <a-form-item v-if="form.type === 'sql'" label="数据源">
          <a-select v-model="form.config.datasource_id" placeholder="选择数据源" :disabled="readonlyMode">
            <a-option v-for="ds in datasources" :key="ds.id" :value="ds.id">
              {{ ds.name }} ({{ ds.type }})
            </a-option>
          </a-select>
        </a-form-item>

        <a-form-item v-if="form.type !== 'datax'" label="超时秒数">
          <a-input-number v-model="form.config.timeout" :min="1" :max="3600" :default-value="300" :disabled="readonlyMode" />
        </a-form-item>

        <!-- 代码编辑器 -->
        <a-form-item :label="codeLabel">
          <CodeEditor
            v-model="form.code"
            :language="codeLanguage"
            :readonly="readonlyMode"
            height="360px"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import { IconPlus } from '@arco-design/web-vue/es/icon'
import CodeEditor from '../components/CodeEditor.vue'
import {
  getComponents, createComponent, updateComponent, deleteComponent,
  testComponent, publishComponent, offlineComponent, runComponent,
  getDatasources,
} from '../api'

interface Comp {
  id: number
  name: string
  type: string
  description?: string
  config_json: Record<string, any>
  version: number
  status: string
  ds_task_code?: number | null
  created_at?: string
  updated_at?: string
}

const loading = ref(false)
const items = ref<Comp[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const searchVal = ref('')
const typeFilter = ref<string | undefined>(undefined)
const statusFilter = ref('')
const datasources = ref<any[]>([])

const editorVisible = ref(false)
const editorTitle = ref('新建组件')
const isEditMode = ref(false)
const readonlyMode = ref(false)
const editingId = ref<number | null>(null)

interface FormState {
  name: string
  type: string
  description: string
  config: Record<string, any>
  code: string
}

const form = reactive<FormState>({
  name: '',
  type: 'sql',
  description: '',
  config: { timeout: 300 },
  code: '',
})

const codeLanguage = computed(() => {
  switch (form.type) {
    case 'sql': return 'sql'
    case 'python': return 'python'
    case 'shell': return 'shell'
    case 'datax': return 'json'
    default: return 'plaintext'
  }
})

const codeLabel = computed(() => {
  switch (form.type) {
    case 'sql': return 'SQL 语句'
    case 'python': return 'Python 脚本'
    case 'shell': return 'Shell 脚本'
    case 'datax': return 'DataX Job JSON'
    default: return '代码'
  }
})

// ===== 工具函数 =====
function typeColor(t: string) {
  return { sql: 'blue', python: 'green', shell: 'orange', datax: 'purple' }[t] || 'gray'
}
function typeLabel(t: string) {
  return { sql: 'SQL', python: 'Python', shell: 'Shell', datax: 'DataX' }[t] || t
}
function statusColor(s: string) {
  return { draft: 'gray', tested: 'cyan', online: 'green', offline: 'orange' }[s] || 'gray'
}
function statusLabel(s: string) {
  return { draft: '草稿', tested: '已测试', online: '已上线', offline: '已下线' }[s] || s
}
function formatTime(t?: string) {
  if (!t) return '—'
  return t.replace('T', ' ').split('.')[0]
}

function canEdit(c: Comp) { return c.status === 'draft' || c.status === 'tested' }
function canTest(c: Comp) { return c.status === 'draft' || c.status === 'tested' }
function canPublish(c: Comp) { return c.status === 'tested' }
function canDelete(c: Comp) { return c.status === 'draft' || c.status === 'offline' }

function setStatus(s: string) { statusFilter.value = s; loadData() }

function onTypeChange() {
  // 切类型时清空 code 和类型特定配置
  form.code = ''
  form.config = { timeout: 300 }
}

// ===== 数据加载 =====
async function loadData() {
  loading.value = true
  try {
    const params: any = {
      page: page.value,
      page_size: pageSize.value,
    }
    if (searchVal.value) params.keyword = searchVal.value
    if (typeFilter.value) params.type = typeFilter.value
    if (statusFilter.value) params.status = statusFilter.value
    const res: any = await getComponents(params)
    items.value = res?.items || []
    total.value = res?.total || 0
  } catch {
    items.value = []
    total.value = 0
  }
  loading.value = false
}

async function loadDatasources() {
  try {
    const res: any = await getDatasources({ page: 1, page_size: 100 })
    datasources.value = res?.items || []
  } catch {
    datasources.value = []
  }
}

// ===== 表单 <-> 数据转换 =====
function resetForm() {
  form.name = ''
  form.type = 'sql'
  form.description = ''
  form.config = { timeout: 300 }
  form.code = ''
}

function loadFormFromComp(c: Comp) {
  form.name = c.name
  form.type = c.type
  form.description = c.description || ''
  const cfg = { ...(c.config_json || {}) }
  // 把代码字段从 config 抽出来
  if (c.type === 'sql') {
    form.code = cfg.sql || ''
    delete cfg.sql
  } else if (c.type === 'python') {
    form.code = cfg.script || ''
    delete cfg.script
  } else if (c.type === 'shell') {
    form.code = cfg.script || ''
    delete cfg.script
  } else if (c.type === 'datax') {
    form.code = cfg.rawJson || ''
    delete cfg.rawJson
  }
  form.config = cfg
}

function buildPayload() {
  const cfg: Record<string, any> = { ...form.config }
  if (form.type === 'sql') cfg.sql = form.code
  else if (form.type === 'python') cfg.script = form.code
  else if (form.type === 'shell') cfg.script = form.code
  else if (form.type === 'datax') cfg.rawJson = form.code
  return {
    name: form.name,
    type: form.type,
    description: form.description || null,
    config_json: cfg,
  }
}

// ===== 操作 =====
function openCreate() {
  resetForm()
  isEditMode.value = false
  readonlyMode.value = false
  editingId.value = null
  editorTitle.value = '新建组件'
  editorVisible.value = true
}

function openEdit(c: Comp) {
  loadFormFromComp(c)
  isEditMode.value = true
  readonlyMode.value = false
  editingId.value = c.id
  editorTitle.value = `编辑 - ${c.name}`
  editorVisible.value = true
}

function viewComp(c: Comp) {
  loadFormFromComp(c)
  isEditMode.value = true
  readonlyMode.value = true
  editingId.value = c.id
  editorTitle.value = `查看 - ${c.name}`
  editorVisible.value = true
}

async function handleSave() {
  if (readonlyMode.value) {
    editorVisible.value = false
    return
  }
  if (!form.name.trim()) {
    Message.warning('请填写组件名')
    return
  }
  if (!form.code.trim()) {
    Message.warning('请填写代码 / 配置内容')
    return
  }
  try {
    const payload = buildPayload()
    if (editingId.value) {
      await updateComponent(editingId.value, { name: payload.name, description: payload.description, config_json: payload.config_json })
      Message.success('已保存(状态回到 draft,需重新测试)')
    } else {
      await createComponent(payload)
      Message.success('已创建')
    }
    editorVisible.value = false
    loadData()
  } catch {}
}

function testComp(c: Comp) {
  Modal.confirm({
    title: '测试组件',
    content: `测试通过后状态将从 ${statusLabel(c.status)} 转为已测试,确认?`,
    onOk: async () => {
      try {
        await testComponent(c.id)
        Message.success('测试通过')
        loadData()
      } catch {}
    },
  })
}

function publishComp(c: Comp) {
  Modal.confirm({
    title: '发布组件',
    content: `「${c.name}」将发布上线,确认?(Phase 3 仅切状态,Phase 5+ 将同步 DS)`,
    onOk: async () => {
      try {
        await publishComponent(c.id)
        Message.success('已发布')
        loadData()
      } catch {}
    },
  })
}

function offlineComp(c: Comp) {
  Modal.confirm({
    title: '下线组件',
    content: `确认下线「${c.name}」?`,
    onOk: async () => {
      try {
        await offlineComponent(c.id)
        Message.success('已下线')
        loadData()
      } catch {}
    },
  })
}

function runComp(c: Comp) {
  Modal.confirm({
    title: '运行组件',
    content: `立即运行「${c.name}」?`,
    onOk: async () => {
      try {
        await runComponent(c.id)
        Message.success('已触发运行')
      } catch {}
    },
  })
}

function deleteComp(c: Comp) {
  Modal.confirm({
    title: '删除组件',
    content: `确认删除「${c.name}」?该操作不可恢复`,
    onOk: async () => {
      try {
        await deleteComponent(c.id)
        Message.success('已删除')
        loadData()
      } catch {}
    },
  })
}

onMounted(() => {
  loadDatasources()
  loadData()
})
</script>

<style scoped>
.page { animation: fadeIn 0.3s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

.page-header { padding: 20px 24px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { margin: 0; font-size: 18px; font-weight: 600; color: #1D2129; }
.page-desc { margin: 4px 0 0; font-size: 13px; color: #86909C; }

.filter-tabs { display: flex; gap: 4px; margin-bottom: 16px; }
.tab-item {
  padding: 6px 16px; border-radius: 6px; font-size: 13px; cursor: pointer;
  color: #4E5969; background: #F7F8FA; transition: all 0.15s;
}
.tab-item:hover { background: #EFF4FF; color: #2B5AED; }
.tab-item.active { background: #2B5AED; color: #FFFFFF; }
.tab-item.online.active { background: #00B42A; }

.table-card { padding: 0; overflow: hidden; }

.comp-name { font-weight: 500; color: #1D2129; }
.comp-version {
  margin-left: 8px;
  font-size: 11px;
  color: #86909C;
  font-family: 'JetBrains Mono', monospace;
}

.mono { font-family: 'JetBrains Mono', monospace; font-size: 12px; }
.text-muted { color: #86909C; }
.cell-ellipsis { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.empty-state { padding: 40px 0; text-align: center; }

.pagination-wrap { padding: 16px 24px; display: flex; justify-content: flex-end; border-top: 1px solid #F2F3F5; }

:deep(.arco-table-th) { background: #FAFBFC !important; }
</style>
