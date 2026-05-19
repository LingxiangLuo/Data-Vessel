<template>
  <div class="page">
    <div class="glass-card page-header">
      <div>
        <h3 class="page-title">数据质量规则</h3>
        <p class="page-desc">为数据表/字段配置质量检查规则，自动拦截脏数据</p>
      </div>
      <a-button type="primary" @click="openCreate">
        <template #icon><icon-plus /></template>
        新建规则
      </a-button>
    </div>

    <!-- 统计卡片 -->
    <div v-if="stats" class="stats-row">
      <div class="glass-card stat-card">
        <div class="stat-label">总检查次数</div>
        <div class="stat-value">{{ stats.summary?.total || 0 }}</div>
      </div>
      <div class="glass-card stat-card">
        <div class="stat-label">通过</div>
        <div class="stat-value" style="color: #00B42A">{{ stats.summary?.passed || 0 }}</div>
      </div>
      <div class="glass-card stat-card">
        <div class="stat-label">异常</div>
        <div class="stat-value" style="color: #F53F3F">{{ stats.summary?.failed || 0 }}</div>
      </div>
    </div>

    <!-- 规则列表 -->
    <div class="glass-card table-card">
      <a-table :data="rules" :loading="loading" :bordered="false" :pagination="false" stripe>
        <template #columns>
          <a-table-column title="规则名称" data-index="name" :width="160" />
          <a-table-column title="数据源" :width="140">
            <template #cell="{ record }">
              <span>{{ record.datasource_name || `数据源#${record.datasource_id}` }}</span>
            </template>
          </a-table-column>
          <a-table-column title="表/字段" :width="160">
            <template #cell="{ record }">
              <div class="table-col-cell">
                <a-tag size="small">{{ record.table_name }}</a-tag>
                <span v-if="record.column_name" class="text-muted">/{{ record.column_name }}</span>
              </div>
            </template>
          </a-table-column>
          <a-table-column title="规则类型" :width="130">
            <template #cell="{ record }">
              <a-tag size="small" color="arcoblue">{{ ruleTypeLabel(record.rule_type) }}</a-tag>
            </template>
          </a-table-column>
          <a-table-column title="阈值" :width="120">
            <template #cell="{ record }">
              <span>{{ opLabel(record.operator) }} {{ record.threshold }}{{ record.threshold_max ? ` ~ ${record.threshold_max}` : '' }}</span>
            </template>
          </a-table-column>
          <a-table-column title="级别" :width="80">
            <template #cell="{ record }">
              <a-tag v-if="record.is_strong" size="small" color="red">强规则</a-tag>
              <a-tag v-else size="small" color="green">弱规则</a-tag>
            </template>
          </a-table-column>
          <a-table-column title="状态" :width="80">
            <template #cell="{ record }">
              <a-switch :model-value="record.enabled" size="small" @change="handleToggle(record)" />
            </template>
          </a-table-column>
          <a-table-column title="操作" :width="200">
            <template #cell="{ record }">
              <a-space :size="4">
                <a-button type="text" size="mini" @click="openEdit(record)">编辑</a-button>
                <a-button type="text" size="mini" @click="handleCheck(record)">立即检查</a-button>
                <a-button type="text" size="mini" @click="openHistory(record)">历史</a-button>
                <a-button type="text" size="mini" status="danger" @click="handleDelete(record)">删除</a-button>
              </a-space>
            </template>
          </a-table-column>
        </template>
        <template #empty>
          <div class="empty-state">
            <p>暂无质量规则</p>
            <p class="text-muted">点击「新建规则」为数据表配置质量检查</p>
          </div>
        </template>
      </a-table>
    </div>

    <!-- 新建/编辑模态框 -->
    <a-modal
      v-model:visible="modalVisible"
      :title="editingId ? '编辑规则' : '新建规则'"
      :width="600"
      @ok="handleSave"
      :unmount-on-close="true"
    >
      <a-form :model="form" layout="vertical">
        <a-form-item label="规则名称" required>
          <a-input v-model="form.name" placeholder="例如：订单金额非空检查" />
        </a-form-item>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="数据源" required>
              <a-select
                v-model="form.datasource_id"
                placeholder="选择数据源"
                allow-search
                :loading="dsLoading"
                @change="onDsChange"
              >
                <a-option v-for="d in datasources" :key="d.id" :value="d.id">{{ d.name }}</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="表名" required>
              <a-select
                v-model="form.table_name"
                placeholder="选择表"
                allow-search
                :loading="tableLoading"
                @change="onTableChange"
              >
                <a-option v-for="t in tables" :key="t.name" :value="t.name">{{ t.name }}</a-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="字段名">
              <a-select
                v-model="form.column_name"
                placeholder="可选（表级规则留空）"
                allow-search
                :loading="colLoading"
                allow-clear
              >
                <a-option v-for="c in columns" :key="c.name" :value="c.name">{{ c.name }} ({{ c.type }})</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="规则类型" required>
              <a-select v-model="form.rule_type" placeholder="选择规则类型" @change="onRuleTypeChange">
                <a-option v-for="rt in ruleTypeOptions" :key="rt.value" :value="rt.value">{{ rt.label }}</a-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="比较方式" required>
              <a-select v-model="form.operator">
                <a-option v-for="op in operatorOptions" :key="op.value" :value="op.value">{{ op.label }}</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="阈值" required>
              <a-input v-model="form.threshold" placeholder="例如：5" />
            </a-form-item>
          </a-col>
          <a-col :span="8" v-if="form.operator === 'between'">
            <a-form-item label="上限" required>
              <a-input v-model="form.threshold_max" placeholder="例如：100" />
            </a-form-item>
          </a-col>
        </a-row>

        <!-- 额外配置 -->
        <a-form-item v-if="form.rule_type === 'custom_sql'" label="自定义 SQL" required>
          <a-textarea v-model="extraForm.custom_sql" :auto-size="{ minRows: 3, maxRows: 6 }" placeholder="SELECT COUNT(*) FROM ..." />
        </a-form-item>
        <a-form-item v-if="form.rule_type === 'regex_match_percent'" label="正则表达式" required>
          <a-input v-model="extraForm.pattern" placeholder="例如：^[0-9]+$" />
        </a-form-item>
        <a-row v-if="form.rule_type === 'value_range'" :gutter="16">
          <a-col :span="12">
            <a-form-item label="最小值">
              <a-input v-model="extraForm.min_value" placeholder="例如：0" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="最大值">
              <a-input v-model="extraForm.max_value" placeholder="例如：999999" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row v-if="form.rule_type === 'length_check'" :gutter="16">
          <a-col :span="12">
            <a-form-item label="长度比较" required>
              <a-select v-model="extraForm.length_op">
                <a-option value="eq">等于</a-option>
                <a-option value="gt">大于</a-option>
                <a-option value="lt">小于</a-option>
                <a-option value="gte">大于等于</a-option>
                <a-option value="lte">小于等于</a-option>
                <a-option value="neq">不等于</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="长度值" required>
              <a-input-number v-model="extraForm.length_value" :min="0" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row v-if="['diff_percent', 'diff_count'].includes(form.rule_type)" :gutter="16">
          <a-col :span="12">
            <a-form-item label="对比基准" required>
              <a-select v-model="extraForm.compare_with">
                <a-option value="prev_day">前一天</a-option>
                <a-option value="prev_week">上周同一天</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="时间字段" required>
              <a-input v-model="extraForm.time_column" placeholder="例如：dt, create_time" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item v-if="form.rule_type === 'value_enum'" label="允许值列表" required>
          <a-input v-model="extraForm.enum_values" placeholder="英文逗号分隔，例如：A,B,C" />
        </a-form-item>
        <a-form-item v-if="form.rule_type === 'format_check'" label="格式类型" required>
          <a-select v-model="extraForm.format_type">
            <a-option value="date">日期格式 (YYYY-MM-DD)</a-option>
            <a-option value="datetime">日期时间 (YYYY-MM-DD HH:mm:ss)</a-option>
            <a-option value="email">邮箱格式</a-option>
            <a-option value="phone">手机号格式</a-option>
            <a-option value="idcard">身份证号</a-option>
            <a-option value="custom">自定义正则</a-option>
          </a-select>
        </a-form-item>
        <a-form-item v-if="form.rule_type === 'format_check' && extraForm.format_type === 'custom'" label="自定义正则" required>
          <a-input v-model="extraForm.format_pattern" placeholder="例如：^[0-9]{4}$" />
        </a-form-item>
        <a-form-item v-if="form.rule_type === 'group_by_count'" label="分组字段" required>
          <a-input v-model="extraForm.group_by_column" placeholder="例如：city" />
        </a-form-item>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="规则级别">
              <a-select v-model="form.is_strong">
                <a-option :value="false">弱规则（仅告警）</a-option>
                <a-option :value="true">强规则（阻塞下游）</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="通知渠道">
              <a-select
                v-model="form.notify_channel_ids"
                multiple
                placeholder="选择通知渠道"
                allow-search
                :loading="channelsLoading"
              >
                <a-option v-for="ch in channels" :key="ch.id" :value="ch.id">{{ ch.name }}</a-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="描述">
          <a-textarea v-model="form.description" :auto-size="{ minRows: 2, maxRows: 4 }" placeholder="规则用途说明..." />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 检查历史模态框 -->
    <a-modal
      v-model:visible="historyVisible"
      title="检查历史"
      :width="700"
      :footer="false"
      :unmount-on-close="true"
    >
      <a-table :data="history" :bordered="false" :pagination="false" stripe row-key="id">
        <template #columns>
          <a-table-column title="检查时间" data-index="checked_at" :width="180" />
          <a-table-column title="实际值" data-index="actual_value" :width="120" />
          <a-table-column title="预期" data-index="expected_value" :width="120" />
          <a-table-column title="结果" :width="80">
            <template #cell="{ record }">
              <a-tag v-if="record.passed" size="small" color="green">通过</a-tag>
              <a-tag v-else size="small" color="red">失败</a-tag>
            </template>
          </a-table-column>
          <a-table-column title="失败采样" :width="120">
            <template #cell="{ record }">
              <a-button v-if="record.sample_data?.length" type="text" size="mini" @click="toggleSample(record.id)">
                {{ expandedSamples[record.id] ? '收起' : '查看' }} ({{ record.sample_data.length }})
              </a-button>
              <span v-else class="text-muted">—</span>
            </template>
          </a-table-column>
          <a-table-column title="错误信息" data-index="error_msg">
            <template #cell="{ record }">
              <span v-if="record.error_msg" class="text-error">{{ record.error_msg }}</span>
              <span v-else class="text-muted">—</span>
            </template>
          </a-table-column>
        </template>
        <template #empty>
          <div class="empty-state">
            <p>暂无检查记录</p>
          </div>
        </template>
      </a-table>
      <!-- 采样数据展开区 -->
      <div v-for="record in history.filter(h => expandedSamples[h.id])" :key="'sample-' + record.id" class="sample-panel">
        <div class="sample-panel__title">{{ record.checked_at }} — 失败采样（{{ record.sample_data.length }} 条）</div>
        <div class="sample-panel__scroll">
          <table class="sample-table">
            <thead>
              <tr>
                <th v-for="col in Object.keys(record.sample_data[0])" :key="col">{{ col }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in record.sample_data" :key="idx">
                <td v-for="col in Object.keys(record.sample_data[0])" :key="col">{{ row[col] }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Message, Modal } from '@arco-design/web-vue'
import {
  getDqcRules, createDqcRule, updateDqcRule, deleteDqcRule,
  toggleDqcRule, runDqcCheck, getDqcRuleHistory, getDqcStats,
  getDatasources, getMetadataTables, getMetadataColumns,
  adminListChannels,
} from '../api'

interface Rule {
  id: number
  name: string
  datasource_id: number
  datasource_name?: string
  table_name: string
  column_name?: string
  rule_type: string
  operator: string
  threshold: string
  threshold_max?: string
  is_strong: boolean
  enabled: boolean
  notify_channel_ids: number[]
  extra_config?: any
  description?: string
}

const loading = ref(false)
const dsLoading = ref(false)
const tableLoading = ref(false)
const colLoading = ref(false)
const channelsLoading = ref(false)
const rules = ref<Rule[]>([])
const datasources = ref<any[]>([])
const tables = ref<any[]>([])
const columns = ref<any[]>([])
const channels = ref<any[]>([])
const stats = ref<any>(null)
const modalVisible = ref(false)
const historyVisible = ref(false)
const editingId = ref<number | null>(null)
const history = ref<any[]>([])
const expandedSamples = ref<Record<number, boolean>>({})

const form = ref({
  name: '',
  datasource_id: undefined as number | undefined,
  table_name: '',
  column_name: undefined as string | undefined,
  rule_type: 'null_percent',
  operator: 'lt',
  threshold: '5',
  threshold_max: undefined as string | undefined,
  is_strong: false,
  enabled: true,
  notify_channel_ids: [] as number[],
  description: '',
})

const extraForm = ref<Record<string, any>>({
  custom_sql: '',
  pattern: '',
  min_value: '',
  max_value: '',
  length_op: 'eq',
  length_value: 0,
  compare_with: 'prev_day',
  time_column: '',
  enum_values: '',
  format_type: 'date',
  format_pattern: '',
  group_by_column: '',
})

const ruleTypeOptions = [
  { value: 'row_count', label: '表行数', needsCol: false },
  { value: 'null_count', label: '空值个数', needsCol: true },
  { value: 'null_percent', label: '空值率(%)', needsCol: true },
  { value: 'distinct_count', label: '唯一值个数', needsCol: true },
  { value: 'distinct_percent', label: '唯一值率(%)', needsCol: true },
  { value: 'duplicate_count', label: '重复值个数', needsCol: true },
  { value: 'duplicate_percent', label: '重复值率(%)', needsCol: true },
  { value: 'min', label: '最小值', needsCol: true },
  { value: 'max', label: '最大值', needsCol: true },
  { value: 'avg', label: '平均值', needsCol: true },
  { value: 'sum', label: '求和', needsCol: true },
  { value: 'custom_sql', label: '自定义SQL', needsCol: false },
  { value: 'regex_match_percent', label: '正则匹配率(%)', needsCol: true },
  { value: 'length_check', label: '长度检查', needsCol: true },
  { value: 'value_range', label: '值范围检查', needsCol: true },
  { value: 'table_size', label: '表大小(字节)', needsCol: false },
  { value: 'group_by_count', label: '分组行数', needsCol: true },
  { value: 'value_enum', label: '枚举值检查', needsCol: true },
  { value: 'format_check', label: '格式检查', needsCol: true },
  { value: 'diff_percent', label: '波动率(%)', needsCol: false },
  { value: 'diff_count', label: '波动量', needsCol: false },
]

const operatorOptions = [
  { value: 'gt', label: '>' },
  { value: 'lt', label: '<' },
  { value: 'gte', label: '>=' },
  { value: 'lte', label: '<=' },
  { value: 'eq', label: '=' },
  { value: 'neq', label: '!=' },
  { value: 'between', label: '介于' },
]

function ruleTypeLabel(t: string) {
  const m: any = {
    row_count: '表行数',
    null_count: '空值个数',
    null_percent: '空值率(%)',
    distinct_count: '唯一值个数',
    distinct_percent: '唯一值率(%)',
    duplicate_count: '重复值个数',
    duplicate_percent: '重复值率(%)',
    min: '最小值',
    max: '最大值',
    avg: '平均值',
    sum: '求和',
    custom_sql: '自定义SQL',
    regex_match_percent: '正则匹配率(%)',
    length_check: '长度检查',
    value_range: '值范围检查',
    table_size: '表大小(字节)',
    group_by_count: '分组行数',
    value_enum: '枚举值检查',
    format_check: '格式检查',
    diff_percent: '波动率(%)',
    diff_count: '波动量',
  }
  return m[t] || t
}

function opLabel(op: string) {
  const m: any = { gt: '>', lt: '<', gte: '>=', lte: '<=', eq: '=', neq: '!=', between: '介于' }
  return m[op] || op
}

async function loadData() {
  loading.value = true
  try {
    const res: any = await getDqcRules()
    rules.value = res?.items || []
  } catch { rules.value = [] }
  loading.value = false
}

async function loadStats() {
  try {
    const res: any = await getDqcStats(7)
    stats.value = res
  } catch { stats.value = null }
}

async function loadDatasources() {
  dsLoading.value = true
  try {
    const res: any = await getDatasources()
    datasources.value = res?.items || []
  } catch { datasources.value = [] }
  dsLoading.value = false
}

async function loadChannels() {
  channelsLoading.value = true
  try {
    const res: any = await adminListChannels()
    channels.value = Array.isArray(res) ? res : (res?.items || [])
  } catch { channels.value = [] }
  channelsLoading.value = false
}

async function onDsChange(val: any) {
  const dsId = Number(val)
  form.value.table_name = ''
  form.value.column_name = undefined
  tables.value = []
  columns.value = []
  if (!dsId) return
  tableLoading.value = true
  try {
    const res: any = await getMetadataTables(dsId, undefined, 200)
    tables.value = res?.tables || []
  } catch { tables.value = [] }
  tableLoading.value = false
}

async function onTableChange(val: any) {
  const tableName = String(val)
  form.value.column_name = undefined
  columns.value = []
  if (!form.value.datasource_id || !tableName) return
  colLoading.value = true
  try {
    const res: any = await getMetadataColumns(form.value.datasource_id, tableName)
    columns.value = res?.columns || []
  } catch { columns.value = [] }
  colLoading.value = false
}

function onRuleTypeChange(val: any) {
  const rt = String(val)
  const opt = ruleTypeOptions.find(o => o.value === rt)
  if (opt && !opt.needsCol) {
    form.value.column_name = undefined
  }
}

function openCreate() {
  editingId.value = null
  form.value = {
    name: '',
    datasource_id: undefined,
    table_name: '',
    column_name: undefined,
    rule_type: 'null_percent',
    operator: 'lt',
    threshold: '5',
    threshold_max: undefined,
    is_strong: false,
    enabled: true,
    notify_channel_ids: [],
    description: '',
  }
  extraForm.value = { custom_sql: '', pattern: '', min_value: '', max_value: '', length_op: 'eq', length_value: 0, compare_with: 'prev_day', time_column: '', enum_values: '', format_type: 'date', format_pattern: '', group_by_column: '' }
  tables.value = []
  columns.value = []
  modalVisible.value = true
}

function openEdit(r: Rule) {
  editingId.value = r.id
  form.value = {
    name: r.name,
    datasource_id: r.datasource_id,
    table_name: r.table_name,
    column_name: r.column_name,
    rule_type: r.rule_type,
    operator: r.operator,
    threshold: r.threshold,
    threshold_max: r.threshold_max,
    is_strong: r.is_strong,
    enabled: r.enabled,
    notify_channel_ids: r.notify_channel_ids || [],
    description: r.description || '',
  }
  extraForm.value = { custom_sql: '', pattern: '', min_value: '', max_value: '', length_op: 'eq', length_value: 0, compare_with: 'prev_day', time_column: '', enum_values: '', format_type: 'date', format_pattern: '', group_by_column: '' }
  if (r.extra_config) {
    extraForm.value.custom_sql = r.extra_config.custom_sql || ''
    extraForm.value.pattern = r.extra_config.pattern || ''
    extraForm.value.min_value = r.extra_config.min_value !== undefined ? String(r.extra_config.min_value) : ''
    extraForm.value.max_value = r.extra_config.max_value !== undefined ? String(r.extra_config.max_value) : ''
    extraForm.value.length_op = r.extra_config.length_op || 'eq'
    extraForm.value.length_value = r.extra_config.length_value || 0
    extraForm.value.compare_with = r.extra_config.compare_with || 'prev_day'
    extraForm.value.time_column = r.extra_config.time_column || ''
    extraForm.value.enum_values = r.extra_config.enum_values ? r.extra_config.enum_values.join(',') : ''
    extraForm.value.format_type = r.extra_config.format_type || 'date'
    extraForm.value.format_pattern = r.extra_config.format_pattern || ''
    extraForm.value.group_by_column = r.extra_config.group_by_column || ''
  }
  tables.value = []
  columns.value = []
  if (r.datasource_id) {
    onDsChange(r.datasource_id).then(() => {
      if (r.table_name) {
        onTableChange(r.table_name)
      }
    })
  }
  modalVisible.value = true
}

async function handleSave() {
  if (!form.value.name.trim()) { Message.warning('请填写规则名称'); return }
  if (!form.value.datasource_id) { Message.warning('请选择数据源'); return }
  if (!form.value.table_name) { Message.warning('请选择表名'); return }
  if (!form.value.rule_type) { Message.warning('请选择规则类型'); return }
  if (!form.value.threshold) { Message.warning('请填写阈值'); return }
  if (form.value.operator === 'between' && !form.value.threshold_max) {
    Message.warning('between 比较需要填写上限'); return
  }

  const extra: any = {}
  if (form.value.rule_type === 'custom_sql') {
    if (!extraForm.value.custom_sql.trim()) { Message.warning('请填写自定义 SQL'); return }
    extra.custom_sql = extraForm.value.custom_sql.trim()
  }
  if (form.value.rule_type === 'regex_match_percent') {
    if (!extraForm.value.pattern.trim()) { Message.warning('请填写正则表达式'); return }
    extra.pattern = extraForm.value.pattern.trim()
  }
  if (form.value.rule_type === 'value_range') {
    if (extraForm.value.min_value !== '') extra.min_value = Number(extraForm.value.min_value)
    if (extraForm.value.max_value !== '') extra.max_value = Number(extraForm.value.max_value)
  }
  if (form.value.rule_type === 'length_check') {
    extra.length_op = extraForm.value.length_op
    extra.length_value = extraForm.value.length_value
  }
  if (['diff_percent', 'diff_count'].includes(form.value.rule_type)) {
    extra.compare_with = extraForm.value.compare_with || 'prev_day'
    extra.time_column = extraForm.value.time_column || ''
  }
  if (form.value.rule_type === 'value_enum') {
    if (!extraForm.value.enum_values?.trim()) { Message.warning('请填写允许值列表'); return }
    extra.enum_values = extraForm.value.enum_values.split(',').map((s: string) => s.trim())
  }
  if (form.value.rule_type === 'format_check') {
    extra.format_type = extraForm.value.format_type || 'date'
    if (extraForm.value.format_type === 'custom') {
      if (!extraForm.value.format_pattern?.trim()) { Message.warning('请填写自定义正则'); return }
      extra.format_pattern = extraForm.value.format_pattern.trim()
    }
  }
  if (form.value.rule_type === 'group_by_count') {
    if (!extraForm.value.group_by_column?.trim()) { Message.warning('请填写分组字段'); return }
    extra.group_by_column = extraForm.value.group_by_column.trim()
  }

  const payload = {
    name: form.value.name.trim(),
    datasource_id: form.value.datasource_id,
    table_name: form.value.table_name,
    column_name: form.value.column_name || undefined,
    rule_type: form.value.rule_type,
    operator: form.value.operator,
    threshold: form.value.threshold,
    threshold_max: form.value.threshold_max,
    is_strong: form.value.is_strong,
    enabled: form.value.enabled,
    notify_channel_ids: form.value.notify_channel_ids,
    extra_config: Object.keys(extra).length ? extra : undefined,
    description: form.value.description || undefined,
  }

  try {
    if (editingId.value) {
      await updateDqcRule(editingId.value, payload)
      Message.success('已更新')
    } else {
      await createDqcRule(payload)
      Message.success('已创建')
    }
    modalVisible.value = false
    loadData()
    loadStats()
  } catch {}
}

async function handleToggle(r: Rule) {
  try {
    await toggleDqcRule(r.id)
    loadData()
  } catch {}
}

async function handleCheck(r: Rule) {
  try {
    const res: any = await runDqcCheck(r.id)
    if (res.passed) {
      Message.success(`检查通过，实际值：${res.actual_value || 'NULL'}`)
    } else {
      Message.error(`检查未通过，实际值：${res.actual_value || 'NULL'}`)
    }
    loadStats()
  } catch (e: any) {
    Message.error(e?.response?.data?.detail || '检查执行失败')
  }
}

async function openHistory(r: Rule) {
  historyVisible.value = true
  expandedSamples.value = {}
  try {
    const res: any = await getDqcRuleHistory(r.id, 50)
    history.value = res?.items || []
  } catch { history.value = [] }
}

function toggleSample(id: number) {
  expandedSamples.value[id] = !expandedSamples.value[id]
}

function handleDelete(r: Rule) {
  Modal.confirm({
    title: '删除规则',
    content: `确认删除「${r.name}」?`,
    onOk: async () => {
      try { await deleteDqcRule(r.id); Message.success('已删除'); loadData() } catch {}
    },
  })
}

const route = useRoute()

onMounted(() => {
  loadData(); loadStats(); loadDatasources(); loadChannels()
  // 处理从组件开发页面跳转过来的预填参数
  const qds = route.query.datasource_id
  const qtb = route.query.table_name
  if (qds || qtb) {
    if (qds) form.value.datasource_id = Number(qds)
    if (qtb) form.value.table_name = String(qtb)
    // 延迟打开新建弹窗，等待数据源列表加载
    setTimeout(() => {
      openCreate()
      if (form.value.datasource_id) {
        onDsChange(form.value.datasource_id).then(() => {
          if (form.value.table_name) {
            onTableChange(form.value.table_name)
          }
        })
      }
    }, 300)
  }
})
</script>

<style scoped>
.page { animation: fadeIn 0.3s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

.page-header { padding: 20px 24px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { margin: 0; font-size: 18px; font-weight: 600; color: #1D2129; }
.page-desc { margin: 4px 0 0; font-size: 13px; color: #86909C; }

.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 16px; }
.stat-card { padding: 16px 20px; }
.stat-label { font-size: 13px; color: #86909C; margin-bottom: 4px; }
.stat-value { font-size: 24px; font-weight: 600; color: #1D2129; }

.table-card { padding: 0; overflow: auto; }
.text-muted { color: #86909C; }
.text-error { color: #F53F3F; }
.empty-state { padding: 40px 0; text-align: center; }
.table-col-cell { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }

:deep(.arco-table-th) { background: #FAFBFC !important; }

.sample-panel { margin-top: 12px; border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; background: #fafbfc; }
.sample-panel__title { font-size: 12px; font-weight: 500; color: #4e5969; margin-bottom: 8px; }
.sample-panel__scroll { overflow-x: auto; }
.sample-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.sample-table th, .sample-table td { padding: 6px 10px; text-align: left; border: 1px solid #e5e7eb; white-space: nowrap; }
.sample-table th { background: #f2f3f5; font-weight: 500; color: #4e5969; }
.sample-table td { color: #1d2129; }
</style>
