<template>
  <span
    class="lang-icon"
    :style="{
      background: cfg.gradient,
      fontSize: Math.round(sz * 0.45) + 'px',
      height: sz + 'px',
      padding: `0 ${Math.round(sz * 0.3)}px`,
    }"
    :title="cfg.label"
  >{{ cfg.abbr }}</span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { TYPE_GROUPS_WITH_DATAX } from '../composables/useFileTree'

const props = defineProps<{ type: string; size?: number }>()

const sz = computed(() => props.size ?? 20)

const cfg = computed(() => {
  const g = TYPE_GROUPS_WITH_DATAX.find(g => g.type === props.type)
  return g
    ? { gradient: g.gradient, label: g.label, abbr: g.abbr }
    : { gradient: '#86909C', label: props.type, abbr: (props.type || '?').slice(0, 2).toUpperCase() }
})
</script>

<style scoped>
.lang-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 3px;
  flex-shrink: 0;
  font-family: 'SF Mono', 'Consolas', 'Monaco', 'Menlo', monospace;
  font-weight: 700;
  color: #fff;
  letter-spacing: 1.5px;
  line-height: 1;
  user-select: none;
  white-space: nowrap;
}
</style>
