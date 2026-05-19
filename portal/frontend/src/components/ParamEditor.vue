<template>
  <div class="param-editor">
    <div class="param-toolbar">
      <span class="param-title">参数配置</span>
      <a-space size="mini">
        <span class="param-hint">系统变量:</span>
        <a-tooltip
          v-for="v in systemVars"
          :key="v.key"
          :content="`${v.desc} 例: ${v.example}`"
        >
          <a-tag
            size="small"
            class="sys-var-tag"
            @click="insertSysVar(v.key)"
          >${{ v.key }}</a-tag>
        </a-tooltip>
      </a-space>
    </div>
    <a-table
      :columns="columns"
      :data="modelValue"
      :pagination="false"
      size="mini"
      class="param-table"
    >
      <template #key="{ record, rowIndex }">
        <a-input
          v-model="record.key"
          size="mini"
          placeholder="参数名"
          @change="onChange"
        />
      </template>
      <template #value="{ record, rowIndex }">
        <a-input
          v-model="record.value"
          size="mini"
          placeholder="如 ${bizdate}"
          @change="onChange"
        />
      </template>
      <template #desc="{ record, rowIndex }">
        <a-input
          v-model="record.desc"
          size="mini"
          placeholder="说明"
          @change="onChange"
        />
      </template>
      <template #actions="{ record, rowIndex }">
        <a-button type="text" size="mini" status="danger" @click="removeRow(rowIndex)">
          <template #icon><icon-delete /></template>
        </a-button>
      </template>
    </a-table>
    <a-button type="text" size="mini" class="add-btn" @click="addRow">
      <template #icon><icon-plus /></template>
      添加参数
    </a-button>
  </div>
</template>

<script setup lang="ts">
import { IconPlus, IconDelete } from '@arco-design/web-vue/es/icon'
import type { ComponentParam } from '../types/component'

const props = defineProps<{
  modelValue: ComponentParam[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', val: ComponentParam[]): void
}>()

const systemVars = [
  { key: 'bizdate', desc: '业务日期(昨天) yyyyMMdd', example: '20260517' },
  { key: 'gmtdate', desc: '当前日期 yyyyMMdd', example: '20260518' },
  { key: 'cyctime', desc: '定时时间 yyyyMMddHHmmss', example: '20260518120000' },
  { key: 'bizmonth', desc: '业务月份 yyyyMM', example: '202605' },
  { key: 'yyyy', desc: '4位年份', example: '2026' },
  { key: 'yyyy-mm-dd', desc: '日期(业务日期基准)', example: '2026-05-17' },
  { key: 'yyyymmdd', desc: '日期紧凑格式', example: '20260517' },
  { key: 'yyyymmdd-1', desc: '前天', example: '20260516' },
  { key: 'yyyymmdd-7', desc: '7天前', example: '20260510' },
  { key: 'hh24', desc: '当前小时', example: '12' },
  { key: 'mi', desc: '当前分钟', example: '30' },
]

const columns = [
  { title: '参数名', slotName: 'key', width: 140 },
  { title: '参数值', slotName: 'value', width: 180 },
  { title: '说明', slotName: 'desc', width: 120 },
  { title: '', slotName: 'actions', width: 50 },
]

function onChange() {
  emit('update:modelValue', [...props.modelValue])
}

function addRow() {
  const list = [...props.modelValue, { key: '', value: '', desc: '' }]
  emit('update:modelValue', list)
}

function removeRow(idx: number) {
  const list = props.modelValue.filter((_, i) => i !== idx)
  emit('update:modelValue', list)
}

function insertSysVar(v: string) {
  // 在最后一个参数的 value 中插入，或新建一行
  const list = [...props.modelValue]
  if (list.length > 0) {
    const last = list[list.length - 1]
    last.value = last.value ? `${last.value} \${${v}}` : `\${${v}}`
  } else {
    list.push({ key: '', value: `\${${v}}`, desc: '' })
  }
  emit('update:modelValue', list)
}
</script>

<style scoped>
.param-editor {
  padding: 8px 12px;
  border-bottom: 1px solid var(--color-neutral-3);
  background: var(--color-bg-2);
}
.param-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 6px;
}
.param-title {
  font-weight: 500;
  font-size: 13px;
}
.param-hint {
  font-size: 12px;
  color: var(--color-text-3);
}
.sys-var-tag {
  cursor: pointer;
  user-select: none;
}
.sys-var-tag:hover {
  opacity: 0.8;
}
.add-btn {
  margin-top: 4px;
}
</style>
