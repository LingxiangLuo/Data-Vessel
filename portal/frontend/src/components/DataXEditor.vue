<template>
  <div class="datax-editor" v-if="ready">
    <!-- 顶栏 -->
    <div class="editor-header">
      <div class="title-area">
        <a-input
          v-model="config.name"
          placeholder="DataX 同步任务名称"
          class="title-input"
          size="large"
          :disabled="isOnline"
        />
        <a-tag :color="statusColor(comp?.status || 'draft')" size="small">
          {{ statusLabel(comp?.status || 'draft') }}
        </a-tag>
        <span class="path-hint" v-if="config.source_table || config.target_table">
          {{ config.source_table || '?' }} → {{ config.target_table || '?' }}
        </span>
      </div>
      <div class="action-area">
        <a-radio-group v-model="mode" type="button" size="small">
          <a-radio value="graphical"><icon-computer /> 图形化</a-radio>
          <a-radio value="script"><icon-code /> 脚本</a-radio>
        </a-radio-group>
        <a-button @click="loadPreview" :loading="previewing" size="small">
          <template #icon><icon-eye /></template>
          预览 DataX
        </a-button>
        <a-button
          v-if="!isOnline"
          type="primary"
          @click="handleSave"
          :loading="saving"
          size="small"
        >
          <template #icon><icon-save /></template>
          保存
        </a-button>
        <a-button
          v-if="compId && !isOnline"
          status="success"
          @click="handleOnline"
          :loading="toggling"
          size="small"
        >
          <template #icon><icon-unlock /></template>
          上线
        </a-button>
        <a-button
          v-if="compId && isOnline"
          @click="handleOffline"
          :loading="toggling"
          size="small"
        >
          <template #icon><icon-lock /></template>
          下线
        </a-button>
      </div>
    </div>

    <!-- 图形化面板 -->
    <div v-show="mode === 'graphical'" class="editor-body">
      <div class="scroll-area">
        <!-- 基础信息 -->
        <section class="card-section">
          <div class="section-title">基础信息</div>
          <div class="form-row">
            <div class="form-item">
              <label>通道数</label>
              <a-input-number v-model="config.channel" :min="1" :max="32" :disabled="isOnline" />
            </div>
          </div>
        </section>

        <!-- 来源配置 -->
        <section class="card-section">
          <div class="section-title"><icon-import /> 数据来源</div>
          <div class="form-row">
            <div class="form-item">
              <label>来源数据源 <span class="required">*</span></label>
              <a-select
                v-model="config.source_id"
                placeholder="选择来源数据源"
                show-search
                :filter-option="dsFilter"
                @change="onSourceDsChange"
                :disabled="isOnline"
              >
                <a-option v-for="d in datasources" :key="d.id" :value="d.id">
                  {{ d.name }} ({{ d.type }})
                </a-option>
              </a-select>
            </div>
            <div class="form-item">
              <label>来源表 <span class="required">*</span></label>
              <a-auto-complete
                v-model="config.source_table"
                placeholder="输入关键字搜索表名"
                :data="sourceTableOptions"
                :trigger-props="{ autoFitPopupMinWidth: true }"
                @search="onSearchSourceTable"
                @change="onSourceTableChange"
                allow-clear
                :disabled="isOnline"
              />
            </div>
          </div>
          <div class="form-row">
            <div class="form-item span-2">
              <label>数据过滤 WHERE（可选，支持 ${bizdate} 等变量）</label>
              <a-input
                v-model="config.where_clause"
                placeholder="如：dt = '${bizdate}' AND status = 1"
                :disabled="isOnline"
              />
            </div>
            <div class="form-item">
              <label>切分键 splitPk（默认取第一列）</label>
              <a-select v-model="config.split_pk" placeholder="可选" allow-clear :disabled="isOnline">
                <a-option v-for="c in sourceColumns" :key="c.name" :value="c.name">
                  {{ c.name }} ({{ c.type }})
                </a-option>
              </a-select>
            </div>
          </div>
        </section>

        <!-- 去向配置 -->
        <section class="card-section">
          <div class="section-title"><icon-export /> 数据去向</div>
          <div class="form-row">
            <div class="form-item">
              <label>去向数据源 <span class="required">*</span></label>
              <a-select
                v-model="config.target_id"
                placeholder="选择去向数据源"
                show-search
                :filter-option="dsFilter"
                @change="onTargetDsChange"
                :disabled="isOnline"
              >
                <a-option v-for="d in datasources" :key="d.id" :value="d.id">
                  {{ d.name }} ({{ d.type }})
                </a-option>
              </a-select>
            </div>
            <div class="form-item">
              <label>目标表 <span class="required">*</span></label>
              <a-auto-complete
                v-model="config.target_table"
                placeholder="选择或输入表名（不存在可一键建表）"
                :data="targetTableOptions"
                @search="onSearchTargetTable"
                @change="onTargetTableChange"
                allow-clear
                :disabled="isOnline"
              />
            </div>
            <div class="form-item">
              <label>写入模式</label>
              <a-select v-model="config.write_mode" :disabled="isOnline">
                <a-option value="insert">insert</a-option>
                <a-option value="replace">replace</a-option>
                <a-option value="update">update</a-option>
              </a-select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-item span-2">
              <label>导入前准备语句 preSql（目标库执行，每行一条）</label>
              <a-textarea
                v-model="preSqlText"
                placeholder="如：TRUNCATE TABLE ${targetTable}"
                :auto-size="{ minRows: 2, maxRows: 6 }"
                :disabled="isOnline"
              />
            </div>
            <div class="form-item span-2">
              <label>导入后准备语句 postSql（目标库执行，每行一条）</label>
              <a-textarea
                v-model="postSqlText"
                placeholder="如：ANALYZE TABLE ${targetTable}"
                :auto-size="{ minRows: 2, maxRows: 6 }"
                :disabled="isOnline"
              />
            </div>
          </div>
        </section>

        <!-- 同步配置 -->
        <section class="card-section">
          <div class="section-title"><icon-sync /> 同步配置</div>
          <div class="form-row">
            <div class="form-item">
              <label>同步方式</label>
              <a-radio-group v-model="config.sync_type" type="button" :disabled="isOnline">
                <a-radio value="full">全量</a-radio>
                <a-radio value="increment">增量</a-radio>
              </a-radio-group>
            </div>
            <div v-if="config.sync_type === 'increment'" class="form-item">
              <label>增量字段</label>
              <a-select v-model="config.increment_column" placeholder="选择增量字段" allow-clear :disabled="isOnline">
                <a-option v-for="c in sourceColumns" :key="c.name" :value="c.name">
                  {{ c.name }} ({{ c.type }})
                </a-option>
              </a-select>
            </div>
          </div>
        </section>

        <!-- 字段映射 -->
        <section class="card-section mapping-section">
          <div class="section-title">
            <icon-swap /> 字段映射
            <span v-if="!sourceColumns.length || !targetColumns.length" class="title-hint">
              （请先在上面选择来源表 / 目标表）
            </span>
          </div>
          <FieldMappingCanvas
            v-model="config.field_mapping"
            :source-columns="sourceColumns"
            :target-columns="targetColumns"
            :enable-auto-create="targetIsSql && !!config.target_id && !!config.target_table"
            :readonly="isOnline"
            @auto-create-table="handleAutoCreateTable"
          />
        </section>
      </div>

      <!-- 底部 JSON 实时预览（可折叠） -->
      <div class="json-preview-bar">
        <div class="json-preview-toggle" @click="showJsonPreview = !showJsonPreview">
          <icon-code /> DataX JSON 实时预览
          <icon-down v-if="showJsonPreview" class="caret" />
          <icon-right v-else class="caret" />
        </div>
        <div v-show="showJsonPreview" class="json-preview-panel">
          <pre>{{ liveJsonPreview }}</pre>
        </div>
      </div>
    </div>

    <!-- 脚本面板 -->
    <div v-show="mode === 'script'" class="editor-body script-mode">
      <div class="script-toolbar">
        <a-space>
          <a-button size="mini" @click="formatJson">
            <template #icon><icon-code-block /></template>
            格式化
          </a-button>
          <a-button size="mini" @click="minifyJson">
            <template #icon><icon-file /></template>
            压缩
          </a-button>
        </a-space>
        <span v-if="jsonError" class="json-error">{{ jsonError }}</span>
        <span v-else class="json-ok">JSON 格式正确</span>
      </div>
      <CodeEditor
        v-model="scriptContent"
        language="json"
        style="flex: 1; min-height: 0;"
      />
    </div>

    <!-- 预览弹窗 -->
    <a-modal
      v-model:visible="previewModalVisible"
      title="DataX 配置预览（密码已打码）"
      width="800px"
      :footer="false"
    >
      <pre class="preview-pre">{{ previewJson }}</pre>
    </a-modal>

    <!-- 一键建表 -->
    <a-modal
      v-model:visible="ddlModalVisible"
      title="一键建表 — DDL 预览"
      @ok="confirmExecuteDDL"
      :ok-loading="ddlExecuting"
      ok-text="执行建表"
      width="640px"
    >
      <a-textarea v-model="ddlText" :auto-size="{ minRows: 8, maxRows: 16 }" style="font-family: 'SF Mono', Menlo, Consolas, monospace;" />
      <div class="hint-text">该 DDL 将在<b>目标数据源</b>执行；如表已存在会被跳过</div>
    </a-modal>
  </div>

  <div v-else class="empty-state">
    <icon-folder class="empty-icon" />
    <p>请在左侧选择或新建一个 DataX 组件</p>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import {
  IconImport, IconExport, IconSync, IconSwap, IconEye, IconCode,
  IconSave, IconFolder, IconLock, IconUnlock, IconComputer,
  IconCodeBlock, IconFile, IconDown, IconRight,
} from '@arco-design/web-vue/es/icon'
import {
  getComponent, createComponent, updateComponent,
  previewDataXConfig,
  getDatasources, getMetadataTables, getMetadataColumns,
  generateDDL, executeDDL,
  publishComponentAsWorkflow, offlineComponent,
} from '../api'
import {
  DataXConfig, emptyDataXConfig, configToJson, jsonToConfig, buildComponentPayload,
} from '../types/datax'
import { statusLabel, statusColor } from '../types/component'
import FieldMappingCanvas from './FieldMappingCanvas.vue'
import CodeEditor from './CodeEditor.vue'

const props = defineProps<{
  compId: number | null
}>()

const emit = defineEmits<{
  saved: [comp: any]
  statusChanged: [comp: any]
}>()

const ready = ref(true)
const mode = ref<'graphical' | 'script'>('graphical')
const comp = ref<any>(null)
const datasources = ref<any[]>([])

const config = reactive<DataXConfig>(emptyDataXConfig())
const preSqlText = ref('')
const postSqlText = ref('')

const sourceColumns = ref<any[]>([])
const targetColumns = ref<any[]>([])
const sourceTableOptions = ref<string[]>([])
const targetTableOptions = ref<string[]>([])

const isOnline = computed(() => comp.value?.status === 'online')
const targetIsSql = computed(() => {
  const t = datasources.value.find((d: any) => d.id === config.target_id)?.type || ''
  return ['mysql', 'postgresql', 'sqlserver', 'oracle', 'clickhouse'].includes(t.toLowerCase())
})
const toggling = ref(false)
const saving = ref(false)
const previewing = ref(false)
const previewModalVisible = ref(false)
const previewJson = ref('')
const showJsonPreview = ref(false)

const scriptContent = ref('')
const jsonError = ref('')

const ddlModalVisible = ref(false)
const ddlText = ref('')
const ddlStatements = ref<string[]>([])
const ddlTargetColumns = ref<any[]>([])
const ddlGenerating = ref(false)
const ddlExecuting = ref(false)

const dsFilter = (input: string, opt: any) => {
  const txt = (opt.children?.[0]?.children || '') as string
  return txt.toLowerCase().includes(input.toLowerCase())
}

// ---- 加载 ----
async function loadDatasources() {
  try {
    const res: any = await getDatasources({ page: 1, page_size: 100 })
    datasources.value = (res.items || []).filter((d: any) => d.host && d.username)
  } catch {}
}

async function loadComp() {
  if (!props.compId) {
    Object.assign(config, emptyDataXConfig())
    preSqlText.value = ''
    postSqlText.value = ''
    sourceColumns.value = []
    targetColumns.value = []
    comp.value = null
    scriptContent.value = configToJson(config)
    jsonError.value = ''
    return
  }
  try {
    const res: any = await getComponent(props.compId)
    comp.value = res
    const cfg = res.config_json || {}
    const loaded: DataXConfig = {
      name: res.name || '',
      source_id: cfg.source_id ?? undefined,
      target_id: cfg.target_id ?? undefined,
      source_table: cfg.source_table || '',
      target_table: cfg.target_table || '',
      sync_type: cfg.sync_type === 'increment' ? 'increment' : 'full',
      increment_column: cfg.increment_column ?? undefined,
      field_mapping: Array.isArray(cfg.field_mapping) ? cfg.field_mapping : [],
      where_clause: cfg.where_clause ?? undefined,
      split_pk: cfg.split_pk ?? undefined,
      write_mode: ['insert', 'replace', 'update'].includes(cfg.write_mode) ? cfg.write_mode : 'insert',
      channel: Number.isFinite(cfg.channel) ? cfg.channel : 3,
      pre_sql: Array.isArray(cfg.pre_sql) ? cfg.pre_sql : undefined,
      post_sql: Array.isArray(cfg.post_sql) ? cfg.post_sql : undefined,
      rawJson: cfg.rawJson,
    }
    Object.assign(config, loaded)
    preSqlText.value = (loaded.pre_sql || []).join('\n')
    postSqlText.value = (loaded.post_sql || []).join('\n')
    scriptContent.value = configToJson(config)
    jsonError.value = ''
    if (config.source_id && config.source_table) await loadSourceColumns()
    if (config.target_id && config.target_table) await loadTargetColumns()
  } catch {}
}

async function onSourceDsChange() {
  config.source_table = ''
  sourceColumns.value = []
  await onSearchSourceTable('')
}

async function onTargetDsChange() {
  config.target_table = ''
  targetColumns.value = []
  await onSearchTargetTable('')
}

let srcSearchTimer: number | null = null
async function onSearchSourceTable(kw: string) {
  if (!config.source_id) return
  if (srcSearchTimer) clearTimeout(srcSearchTimer)
  srcSearchTimer = window.setTimeout(async () => {
    try {
      const res: any = await getMetadataTables(config.source_id!, kw || undefined, 50)
      sourceTableOptions.value = (res.tables || []).map((t: any) => t.name)
    } catch {}
  }, 200)
}

let dstSearchTimer: number | null = null
async function onSearchTargetTable(kw: string) {
  if (!config.target_id) return
  if (dstSearchTimer) clearTimeout(dstSearchTimer)
  dstSearchTimer = window.setTimeout(async () => {
    try {
      const res: any = await getMetadataTables(config.target_id!, kw || undefined, 50)
      targetTableOptions.value = (res.tables || []).map((t: any) => t.name)
    } catch {}
  }, 200)
}

async function onSourceTableChange(v: string) {
  if (!config.source_id || !v) { sourceColumns.value = []; return }
  await loadSourceColumns()
}

async function onTargetTableChange(v: string) {
  if (!config.target_id || !v) { targetColumns.value = []; return }
  await loadTargetColumns()
}

async function loadSourceColumns() {
  if (!config.source_id || !config.source_table) return
  try {
    const res: any = await getMetadataColumns(config.source_id, config.source_table)
    sourceColumns.value = res.columns || []
  } catch { sourceColumns.value = [] }
}

async function loadTargetColumns() {
  if (!config.target_id || !config.target_table) return
  try {
    const res: any = await getMetadataColumns(config.target_id, config.target_table)
    targetColumns.value = res.columns || []
  } catch (e: any) {
    // API 拦截器已显示错误提示，这里不再重复；也不清空 targetColumns，保留推断值
    throw e
  }
}

// ---- 脚本模式 ----
function formatJson() {
  try {
    scriptContent.value = JSON.stringify(JSON.parse(scriptContent.value), null, 2)
    jsonError.value = ''
  } catch (e: any) {
    jsonError.value = e.message || 'JSON 格式错误'
  }
}

function minifyJson() {
  try {
    scriptContent.value = JSON.stringify(JSON.parse(scriptContent.value))
    jsonError.value = ''
  } catch (e: any) {
    jsonError.value = e.message || 'JSON 格式错误'
  }
}

watch(mode, (newMode, oldMode) => {
  if (oldMode === 'script' && newMode === 'graphical') {
    const result = jsonToConfig(scriptContent.value)
    if ('error' in result) {
      Message.error(`无法切换回图形化模式：${result.error}`)
      mode.value = 'script'
      return
    }
    Object.assign(config, result)
    preSqlText.value = (result.pre_sql || []).join('\n')
    postSqlText.value = (result.post_sql || []).join('\n')
  }
  if (oldMode === 'graphical' && newMode === 'script') {
    scriptContent.value = configToJson(config)
    jsonError.value = ''
  }
})

watch(() => scriptContent.value, () => {
  try {
    JSON.parse(scriptContent.value)
    jsonError.value = ''
  } catch (e: any) {
    jsonError.value = e.message || 'JSON 格式错误'
  }
})

const liveJsonPreview = computed(() => {
  try {
    return configToJson(config)
  } catch {
    return '{}'
  }
})

// ---- 保存 / 上线 / 下线 ----
function buildConfigJson(): Record<string, any> {
  const preSql = preSqlText.value.split('\n').map(s => s.trim()).filter(Boolean)
  const postSql = postSqlText.value.split('\n').map(s => s.trim()).filter(Boolean)
  return {
    name: config.name,
    source_id: config.source_id,
    target_id: config.target_id,
    source_table: config.source_table,
    target_table: config.target_table,
    sync_type: config.sync_type,
    increment_column: config.increment_column,
    field_mapping: config.field_mapping,
    where_clause: config.where_clause,
    split_pk: config.split_pk,
    write_mode: config.write_mode,
    channel: config.channel,
    pre_sql: preSql.length ? preSql : null,
    post_sql: postSql.length ? postSql : null,
  }
}

async function handleSave() {
  if (!config.name) { Message.warning('请输入任务名称'); return }
  if (!config.source_id || !config.target_id) { Message.warning('请选择来源和去向数据源'); return }
  if (!config.source_table || !config.target_table) { Message.warning('请选择来源表和目标表'); return }
  if (!config.field_mapping || config.field_mapping.length === 0) {
    Message.warning('请至少配置一条字段映射'); return
  }
  saving.value = true
  try {
    const config_json = buildConfigJson()
    let res: any
    if (props.compId) {
      res = await updateComponent(props.compId, { name: config.name, config_json })
      Message.success('已更新')
    } else {
      res = await createComponent({
        name: config.name,
        type: 'datax',
        description: `DataX 同步：${config.source_table} → ${config.target_table}`,
        config_json,
      })
      Message.success('已创建')
    }
    comp.value = res
    emit('saved', res)
  } catch {} finally {
    saving.value = false
  }
}

async function handleOnline() {
  if (!props.compId) { Message.warning('请先保存任务'); return }
  toggling.value = true
  try {
    const res: any = await publishComponentAsWorkflow(props.compId)
    comp.value = { ...comp.value, status: 'online', ds_task_code: res.ds_process_code }
    Message.success('已上线并发布到 DS')
    emit('statusChanged', comp.value)
  } catch {} finally { toggling.value = false }
}

async function handleOffline() {
  if (!props.compId) return
  toggling.value = true
  try {
    const res: any = await offlineComponent(props.compId)
    comp.value = res
    Message.success('已下线，可以编辑')
    emit('statusChanged', res)
  } catch {} finally { toggling.value = false }
}

// ---- 预览 ----
async function loadPreview() {
  if (!config.source_id || !config.target_id || !config.source_table || !config.target_table) {
    Message.warning('请先填写来源/目标信息')
    return
  }
  if (!config.field_mapping?.length) { Message.warning('请先配置字段映射'); return }
  previewing.value = true
  try {
    const res: any = await previewDataXConfig({
      source_id: config.source_id,
      target_id: config.target_id,
      source_table: config.source_table,
      target_table: config.target_table,
      sync_type: config.sync_type,
      increment_column: config.increment_column,
      field_mapping: config.field_mapping,
      where_clause: config.where_clause,
      split_pk: config.split_pk,
      write_mode: config.write_mode,
      channel: config.channel,
      pre_sql: preSqlText.value.split('\n').map(s => s.trim()).filter(Boolean),
      post_sql: postSqlText.value.split('\n').map(s => s.trim()).filter(Boolean),
    })
    previewJson.value = JSON.stringify(res.datax, null, 2)
    previewModalVisible.value = true
  } catch {} finally {
    previewing.value = false
  }
}

// ---- 一键建表 ----
async function handleAutoCreateTable() {
  if (!config.target_id || !config.target_table) {
    Message.warning('请先选择目标数据源和目标表名')
    return
  }
  if (!sourceColumns.value.length) {
    Message.warning('未获取到源表字段，无法推断建表 SQL')
    return
  }
  ddlGenerating.value = true
  try {
    const res: any = await generateDDL({
      datasource_id: config.target_id,
      target_table: config.target_table,
      columns: sourceColumns.value.map((c: any) => ({
        name: c.name, type: c.type, nullable: c.nullable,
        primary_key: c.primary_key, comment: c.comment,
      })),
    })
    ddlText.value = res.ddl || ''
    ddlStatements.value = Array.isArray(res.statements) ? res.statements : [res.ddl]
    ddlTargetColumns.value = Array.isArray(res.columns) ? res.columns : []
    ddlModalVisible.value = true
  } catch {} finally {
    ddlGenerating.value = false
  }
}

async function confirmExecuteDDL() {
  if (!ddlText.value.trim()) return
  ddlExecuting.value = true
  try {
    const res: any = await executeDDL({
      datasource_id: config.target_id!,
      ddl: ddlText.value,
      statements: ddlStatements.value,
    })
    if (res.ok) {
      Message.success(res.message || '建表成功')
      ddlModalVisible.value = false
      config.field_mapping = []
      // 先用 generateDDL 返回的列信息更新目标列，保证画布立即渲染
      if (ddlTargetColumns.value.length) {
        targetColumns.value = ddlTargetColumns.value
      }
      // 再异步刷新真实列信息（某些数据库信息 schema 可能有延迟）
      try {
        await loadTargetColumns()
      } catch {
        Message.warning('目标列刷新延迟，已使用推断类型，稍后自动同步')
      }
    } else {
      Message.error(res.message || '建表失败')
    }
  } catch {} finally {
    ddlExecuting.value = false
  }
}

watch(() => props.compId, () => loadComp())

onMounted(async () => {
  await loadDatasources()
  await loadComp()
})
</script>

<style scoped>
.datax-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #F7F8FA;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: #fff;
  border-bottom: 1px solid #E5E6EB;
  flex-shrink: 0;
}

.title-area {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}
.title-input {
  width: 280px;
  flex-shrink: 0;
}
.title-input :deep(.arco-input) {
  font-weight: 600;
  font-size: 15px;
}
.path-hint {
  font-size: 12px;
  color: #86909C;
  font-family: 'SF Mono', Menlo, Consolas, monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.action-area {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-shrink: 0;
}

.editor-body {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.scroll-area {
  flex: 1;
  overflow: auto;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.card-section {
  background: #fff;
  border-radius: 8px;
  padding: 14px 18px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  flex-shrink: 0;
}
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #1D2129;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.title-hint { font-size: 12px; font-weight: normal; color: #C9CDD4; margin-left: 4px; }

.form-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px 14px;
  margin-bottom: 6px;
}
.form-row:last-child { margin-bottom: 0; }
.form-item { display: flex; flex-direction: column; gap: 3px; }
.form-item label {
  font-size: 12px;
  color: #4E5969;
  line-height: 1.4;
}
.form-item .required { color: #F53F3F; }
.form-item.span-2 { grid-column: span 2; }

.mapping-section { padding-bottom: 16px; }

/* 脚本模式 */
.script-mode {
  display: flex;
  flex-direction: column;
}
.script-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: #fff;
  border-bottom: 1px solid #E5E6EB;
  flex-shrink: 0;
}
.json-error {
  color: #F53F3F;
  font-size: 12px;
  margin-left: auto;
}
.json-ok {
  color: #00B42A;
  font-size: 12px;
  margin-left: auto;
}

/* JSON 实时预览 */
.json-preview-bar {
  background: #fff;
  border-top: 1px solid #E5E6EB;
  flex-shrink: 0;
}
.json-preview-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: 12px;
  color: #4E5969;
  cursor: pointer;
  user-select: none;
  transition: background 0.15s;
}
.json-preview-toggle:hover { background: #F2F3F5; }
.json-preview-toggle .caret { margin-left: auto; font-size: 10px; color: #86909C; }
.json-preview-panel {
  padding: 0 16px 12px;
  max-height: 240px;
  overflow: auto;
}
.json-preview-panel pre {
  margin: 0;
  padding: 10px;
  background: #1D2129;
  color: #E5E6EB;
  border-radius: 6px;
  font-family: 'SF Mono', Menlo, Consolas, monospace;
  font-size: 11px;
  line-height: 1.5;
  white-space: pre;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #C9CDD4;
}
.empty-icon { font-size: 48px; margin-bottom: 12px; }

.preview-pre {
  margin: 0;
  padding: 12px;
  background: #1D2129;
  color: #E5E6EB;
  border-radius: 6px;
  font-family: 'SF Mono', Menlo, Consolas, monospace;
  font-size: 12px;
  line-height: 1.5;
  max-height: 60vh;
  overflow: auto;
  white-space: pre;
}
.hint-text { color: #86909C; font-size: 12px; margin-top: 6px; }
</style>
