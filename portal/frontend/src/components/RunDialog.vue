<template>
  <a-modal
    :visible="visible"
    title="执行参数"
    @ok="onOk"
    @cancel="onCancel"
    @update:visible="(v: boolean) => emit('update:visible', v)"
    width="420px"
  >
    <div v-if="params.length === 0" class="no-params">
      该组件未配置参数，将直接执行。
    </div>
    <div v-else class="param-form">
      <div v-for="p in params" :key="p.key" class="param-row">
        <div class="param-label">
          {{ p.key }}
          <span v-if="p.desc" class="param-desc">({{ p.desc }})</span>
        </div>
        <a-input
          v-model="runtimeValues[p.key]"
          size="small"
          :placeholder="`默认值: ${p.value || '(空)'}`"
        />
      </div>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import type { ComponentParam } from '../types/component'

const props = defineProps<{
  visible: boolean
  params: ComponentParam[]
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'run', runtimeParams: Record<string, string>): void
}>()

const runtimeValues = reactive<Record<string, string>>({})

watch(() => props.visible, (v) => {
  if (v) {
    // 初始化运行时值为默认值
    for (const p of props.params) {
      if (!(p.key in runtimeValues)) {
        runtimeValues[p.key] = p.value || ''
      }
    }
  }
})

function onOk() {
  const overrides: Record<string, string> = {}
  for (const p of props.params) {
    const val = runtimeValues[p.key]
    if (val !== undefined && val !== p.value) {
      overrides[p.key] = val
    }
  }
  emit('run', overrides)
  emit('update:visible', false)
}

function onCancel() {
  emit('update:visible', false)
}
</script>

<style scoped>
.no-params {
  padding: 16px 0;
  text-align: center;
  color: var(--color-text-3);
}
.param-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px 0;
}
.param-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.param-label {
  font-size: 13px;
  font-weight: 500;
}
.param-desc {
  font-weight: normal;
  color: var(--color-text-3);
  margin-left: 4px;
}
</style>
