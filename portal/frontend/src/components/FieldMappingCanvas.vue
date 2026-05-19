<template>
  <div class="mapping-canvas-wrap">
    <!-- 工具栏 -->
    <div class="canvas-toolbar">
      <a-space size="small">
        <a-button size="small" type="primary" @click="autoMapByName" :disabled="readonly">
          <template #icon><icon-link /></template>
          同名映射
        </a-button>
        <a-button size="small" @click="autoMapByPosition" :disabled="readonly">同行映射</a-button>
        <a-button size="small" status="warning" @click="clearMappings" :disabled="readonly">清空</a-button>
        <a-divider direction="vertical" />
        <a-button size="small" @click="openConstantModal" :disabled="readonly">
          <template #icon><icon-plus /></template>
          常量
        </a-button>
        <a-button size="small" @click="openVariableModal" :disabled="readonly">
          <template #icon><icon-plus /></template>
          变量
        </a-button>
        <a-button v-if="enableAutoCreate" size="small" @click="$emit('auto-create-table')" :disabled="readonly">
          <template #icon><icon-storage /></template>
          一键建表
        </a-button>
        <a-divider direction="vertical" />
        <span class="hint">
          源 <b>{{ effectiveSourceItems.length }}</b> · 目标 <b>{{ targetColumns.length }}</b> ·
          已映射 <b style="color:#2B5AED">{{ mappings.length }}</b>
        </span>
      </a-space>
    </div>

    <!-- 表头 -->
    <div class="canvas-headers">
      <div class="col-header">来源字段</div>
      <div class="col-header">目标字段</div>
    </div>

    <!-- 画布主体 -->
    <div class="canvas-body" ref="bodyRef">
      <!-- 左列 -->
      <div class="field-col src-col">
        <div
          v-for="(f, i) in effectiveSourceItems"
          :key="`src-${f.kind}-${f.src}-${i}`"
          :ref="el => setRowRef('src', i, el as HTMLElement | null)"
          :class="['field-row', { selected: selectedSrcKey === srcKey(f), custom: f.kind !== 'column' }]"
          @click="onSrcClick(f)"
          @mousedown="!readonly && onSrcMousedown(f, $event)"
        >
          <span v-if="f.kind === 'constant'" class="badge badge-const" title="常量">★</span>
          <span v-else-if="f.kind === 'variable'" class="badge badge-var" title="变量">⚡</span>
          <span class="field-name">{{ f.src }}</span>
          <span class="field-type">{{ f.kind === 'column' ? (f.type || '') : f.kind === 'constant' ? '常量' : '变量' }}</span>
          <span v-if="f.kind !== 'column'" class="del-btn" @click.stop="!readonly && removeCustomItem(f)">×</span>
          <div class="anchor anchor-right" />
        </div>
        <div v-if="effectiveSourceItems.length === 0" class="empty-tip">请先选择来源表</div>
      </div>

      <!-- SVG 连线层 -->
      <svg ref="svgRef" class="lines-svg" :width="lineWidth" :height="canvasHeight">
        <path
          v-for="(p, i) in linePaths"
          :key="`line-${i}`"
          :d="p.d"
          fill="none"
          stroke="#2B5AED"
          stroke-width="2"
          @click="!readonly && removeMapping(p.srcKey, p.dst)"
          class="line-path"
        />
        <!-- 拖拽预览线 -->
        <path
          v-if="pendingLine"
          :d="pendingLine"
          fill="none"
          stroke="#86909C"
          stroke-width="2"
          stroke-dasharray="4 4"
        />
      </svg>

      <!-- 右列 -->
      <div class="field-col dst-col">
        <div
          v-for="(t, i) in targetColumns"
          :key="`dst-${t.name}-${i}`"
          :ref="el => setRowRef('dst', i, el as HTMLElement | null)"
          :class="['field-row', { selected: selectedDstKey === t.name, mapped: dstMapped(t.name) }]"
          :data-dst-index="i"
          @click="!readonly && onDstClick(t)"
        >
          <div class="anchor anchor-left" />
          <span class="field-name">{{ t.name }}</span>
          <span class="field-type">{{ t.type || '' }}</span>
        </div>
        <div v-if="targetColumns.length === 0" class="empty-tip">请先选择目标表</div>
      </div>
    </div>

    <!-- 常量 / 变量 弹窗 -->
    <a-modal v-model:visible="constModalVisible" title="添加常量" @ok="addConstant" :ok-text="'添加'" width="420px">
      <a-form :model="{ v: constValue }" layout="vertical">
        <a-form-item label="常量值">
          <a-input v-model="constValue" placeholder="如：CN" />
        </a-form-item>
        <div class="hint-text">将作为 DataX reader.column 中的 {"type":"string","value":"..."} 透传</div>
      </a-form>
    </a-modal>

    <a-modal v-model:visible="varModalVisible" title="添加调度变量" @ok="addVariable" :ok-text="'添加'" width="420px">
      <a-form :model="{ v: varValue }" layout="vertical">
        <a-form-item label="变量表达式">
          <a-select v-model="varValue" allow-create placeholder="选择或输入变量">
            <a-option value="${bizdate}">${'$'}{bizdate} — 业务日期 (yyyyMMdd)</a-option>
            <a-option value="${last_sync_time}">${'$'}{last_sync_time} — 上次同步时间</a-option>
            <a-option value="${cyctime}">${'$'}{cyctime} — 调度周期时间</a-option>
          </a-select>
        </a-form-item>
        <div class="hint-text">由调度器在执行时替换为实际值</div>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { IconLink, IconPlus, IconStorage } from '@arco-design/web-vue/es/icon'

interface ColumnDef {
  name: string
  type?: string
  comment?: string
}

interface MappingItem {
  kind: 'column' | 'constant' | 'variable'
  src: string
  dst: string
  type?: string
}

const props = defineProps<{
  sourceColumns: ColumnDef[]
  targetColumns: ColumnDef[]
  modelValue: MappingItem[]
  enableAutoCreate?: boolean
  readonly?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [items: MappingItem[]]
  'auto-create-table': []
}>()

// ---- 来源项 = 真实列 + 用户自定义的常量/变量 ----
interface SourceItem { kind: 'column' | 'constant' | 'variable'; src: string; type?: string }

const customItems = ref<SourceItem[]>([])

function syncCustomFromMapping() {
  const customs = (props.modelValue || []).filter(m => m.kind === 'constant' || m.kind === 'variable')
  const seen = new Set<string>()
  const arr: SourceItem[] = []
  for (const c of customs) {
    const k = `${c.kind}::${c.src}`
    if (seen.has(k)) continue
    seen.add(k)
    arr.push({ kind: c.kind, src: c.src })
  }
  customItems.value = arr
}

const effectiveSourceItems = computed<SourceItem[]>(() => [
  ...props.sourceColumns.map(c => ({ kind: 'column' as const, src: c.name, type: c.type })),
  ...customItems.value,
])

function srcKey(f: SourceItem): string {
  return f.kind === 'column' ? `col::${f.src}` : `${f.kind}::${f.src}`
}

const mappings = ref<{ srcKey: string; dst: string }[]>([])

function mappingsToValue(): MappingItem[] {
  const dstTypeMap = new Map(props.targetColumns.map(c => [c.name, c.type]))
  const srcItemMap = new Map(effectiveSourceItems.value.map(f => [srcKey(f), f]))
  const arr: MappingItem[] = []
  for (const m of mappings.value) {
    const src = srcItemMap.get(m.srcKey)
    if (!src) continue
    arr.push({ kind: src.kind, src: src.src, dst: m.dst, type: dstTypeMap.get(m.dst) })
  }
  return arr
}

function emitChange() {
  emit('update:modelValue', mappingsToValue())
}

function valueToMappings() {
  const arr: { srcKey: string; dst: string }[] = []
  for (const m of (props.modelValue || [])) {
    const sk = (m.kind === 'constant' || m.kind === 'variable') ? `${m.kind}::${m.src}` : `col::${m.src}`
    arr.push({ srcKey: sk, dst: m.dst })
  }
  mappings.value = arr
}

// ---- 选中态：点击一边再点对侧建立映射 ----
const selectedSrcKey = ref<string | null>(null)
const selectedDstKey = ref<string | null>(null)

// 拖拽标志，防止 mousedown→drag→mouseup 之后触发 click 建立重复映射
let _wasDragged = false

function onSrcClick(f: SourceItem) {
  if (_wasDragged) return
  const sk = srcKey(f)
  if (selectedDstKey.value) {
    pairUp(sk, selectedDstKey.value)
    selectedSrcKey.value = null
    selectedDstKey.value = null
  } else {
    selectedSrcKey.value = selectedSrcKey.value === sk ? null : sk
  }
}

function onDstClick(t: ColumnDef) {
  if (selectedSrcKey.value) {
    pairUp(selectedSrcKey.value, t.name)
    selectedSrcKey.value = null
    selectedDstKey.value = null
  } else {
    selectedDstKey.value = selectedDstKey.value === t.name ? null : t.name
  }
}

function pairUp(srcK: string, dst: string) {
  mappings.value = mappings.value.filter(m => m.dst !== dst)
  mappings.value = mappings.value.filter(m => m.srcKey !== srcK)
  mappings.value.push({ srcKey: srcK, dst })
  emitChange()
}

function removeMapping(srcK: string, dst: string) {
  mappings.value = mappings.value.filter(m => !(m.srcKey === srcK && m.dst === dst))
  emitChange()
}

function dstMapped(name: string) {
  return mappings.value.some(m => m.dst === name)
}

// ---- 工具栏动作 ----
function autoMapByName() {
  const srcMap = new Map(props.sourceColumns.map(c => [c.name, true]))
  const arr: { srcKey: string; dst: string }[] = []
  for (const t of props.targetColumns) {
    if (srcMap.has(t.name)) arr.push({ srcKey: `col::${t.name}`, dst: t.name })
  }
  mappings.value = arr
  emitChange()
}

function autoMapByPosition() {
  const len = Math.min(props.sourceColumns.length, props.targetColumns.length)
  const arr: { srcKey: string; dst: string }[] = []
  for (let i = 0; i < len; i++) {
    arr.push({ srcKey: `col::${props.sourceColumns[i].name}`, dst: props.targetColumns[i].name })
  }
  mappings.value = arr
  emitChange()
}

function clearMappings() {
  mappings.value = []
  emitChange()
}

// ---- 常量 / 变量 弹窗 ----
const constModalVisible = ref(false)
const constValue = ref('')
const varModalVisible = ref(false)
const varValue = ref('${bizdate}')

function openConstantModal() { constValue.value = ''; constModalVisible.value = true }
function openVariableModal() { varValue.value = '${bizdate}'; varModalVisible.value = true }

function addConstant() {
  const v = (constValue.value || '').trim()
  if (!v) return
  const k = `constant::${v}`
  if (!customItems.value.some(i => srcKey(i) === k)) {
    customItems.value.push({ kind: 'constant', src: v })
  }
  constModalVisible.value = false
}

function addVariable() {
  const v = (varValue.value || '').trim()
  if (!v) return
  const k = `variable::${v}`
  if (!customItems.value.some(i => srcKey(i) === k)) {
    customItems.value.push({ kind: 'variable', src: v })
  }
  varModalVisible.value = false
}

function removeCustomItem(f: SourceItem) {
  const k = srcKey(f)
  customItems.value = customItems.value.filter(i => srcKey(i) !== k)
  mappings.value = mappings.value.filter(m => m.srcKey !== k)
  emitChange()
}

// ---- SVG 连线计算 ----
const bodyRef = ref<HTMLElement | null>(null)
const svgRef = ref<SVGElement | null>(null)
const srcRowRefs = ref<Record<number, HTMLElement | null>>({})
const dstRowRefs = ref<Record<number, HTMLElement | null>>({})
const tick = ref(0)

function setRowRef(side: 'src' | 'dst', i: number, el: HTMLElement | null) {
  const m = side === 'src' ? srcRowRefs.value : dstRowRefs.value
  m[i] = el
}

const lineWidth = ref(240)
const canvasHeight = computed(() => {
  const cnt = Math.max(effectiveSourceItems.value.length, props.targetColumns.length, 1)
  return cnt * 42 + 8
})

const linePaths = computed(() => {
  void tick.value
  void mappings.value
  if (!bodyRef.value) return []
  const bodyRect = bodyRef.value.getBoundingClientRect()
  const items = effectiveSourceItems.value
  const targets = props.targetColumns
  const srcIdx = new Map(items.map((f, i) => [srcKey(f), i]))
  const dstIdx = new Map(targets.map((t, i) => [t.name, i]))
  const paths: { d: string; srcKey: string; dst: string }[] = []
  for (const m of mappings.value) {
    const si = srcIdx.get(m.srcKey); const di = dstIdx.get(m.dst)
    if (si === undefined || di === undefined) continue
    const sEl = srcRowRefs.value[si]; const dEl = dstRowRefs.value[di]
    if (!sEl || !dEl) continue
    const sr = sEl.getBoundingClientRect(); const dr = dEl.getBoundingClientRect()
    const sx = sr.right - bodyRect.left - 280
    const sy = sr.top + sr.height / 2 - bodyRect.top
    const dx = dr.left - bodyRect.left - 280
    const dy = dr.top + dr.height / 2 - bodyRect.top
    const cx = (sx + dx) / 2
    const d = `M ${sx} ${sy} C ${cx} ${sy}, ${cx} ${dy}, ${dx} ${dy}`
    paths.push({ d, srcKey: m.srcKey, dst: m.dst })
  }
  return paths
})

// ---- 拖拽连线 ----
const pendingLine = ref<string | null>(null)
const draggingFrom = ref<SourceItem | null>(null)

function onSrcMousedown(f: SourceItem, e: MouseEvent) {
  if (e.button !== 0) return  // 只响应左键
  const startX = e.clientX
  const startY = e.clientY
  const dragThreshold = 6

  let dragging = false

  const onMove = (ev: MouseEvent) => {
    if (!dragging) {
      const dist = Math.sqrt((ev.clientX - startX) ** 2 + (ev.clientY - startY) ** 2)
      if (dist > dragThreshold) {
        dragging = true
        _wasDragged = true
        draggingFrom.value = f
      }
    }
    if (dragging) updatePendingLine(ev.clientX, ev.clientY)
  }

  const onUp = (ev: MouseEvent) => {
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('mouseup', onUp)

    if (dragging) {
      // 找到鼠标释放位置下的目标字段行
      const el = document.elementFromPoint(ev.clientX, ev.clientY) as HTMLElement | null
      const dstRow = el?.closest('[data-dst-index]') as HTMLElement | null
      if (dstRow) {
        const idx = parseInt(dstRow.dataset.dstIndex ?? '-1')
        if (idx >= 0 && idx < props.targetColumns.length) {
          pairUp(srcKey(f), props.targetColumns[idx].name)
        }
      }
    }

    draggingFrom.value = null
    pendingLine.value = null
    // 给 click 事件一个宏任务的时间先触发，然后再重置 _wasDragged
    setTimeout(() => { _wasDragged = false }, 50)
  }

  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onUp)
}

function updatePendingLine(clientX: number, clientY: number) {
  const f = draggingFrom.value
  if (!f || !bodyRef.value) return
  const items = effectiveSourceItems.value
  const si = items.findIndex(item => srcKey(item) === srcKey(f))
  if (si === -1) return
  const sEl = srcRowRefs.value[si]
  if (!sEl) return

  const bodyRect = bodyRef.value.getBoundingClientRect()
  const sr = sEl.getBoundingClientRect()
  const sx = sr.right - bodyRect.left - 280
  const sy = sr.top + sr.height / 2 - bodyRect.top
  const dx = clientX - bodyRect.left - 280
  const dy = clientY - bodyRect.top
  const cx = (sx + dx) / 2
  pendingLine.value = `M ${sx} ${sy} C ${cx} ${sy}, ${cx} ${dy}, ${dx} ${dy}`
}

function recalc() { tick.value++ }

onMounted(() => {
  valueToMappings()
  syncCustomFromMapping()
  nextTick(recalc)
})

watch(customItems, () => nextTick(recalc), { deep: true })

watch(() => props.modelValue, () => {
  valueToMappings()
  syncCustomFromMapping()
  nextTick(recalc)
}, { deep: true })

watch(() => [props.sourceColumns, props.targetColumns], () => {
  // 只有两侧都有字段时才做剪枝，避免加载顺序不同导致映射被清空
  if (props.sourceColumns.length > 0 && props.targetColumns.length > 0) {
    const srcSet = new Set(effectiveSourceItems.value.map(f => srcKey(f)))
    const dstSet = new Set(props.targetColumns.map(t => t.name))
    const before = mappings.value.length
    mappings.value = mappings.value.filter(m => srcSet.has(m.srcKey) && dstSet.has(m.dst))
    if (mappings.value.length !== before) emitChange()
  }
  nextTick(recalc)
}, { deep: true })

function onWinResize() { recalc() }
onMounted(() => window.addEventListener('resize', onWinResize))
onBeforeUnmount(() => window.removeEventListener('resize', onWinResize))
</script>

<style scoped>
.mapping-canvas-wrap {
  border: 1px solid #E5E6EB;
  border-radius: 8px;
  background: #fff;
}

.canvas-toolbar {
  padding: 10px 14px;
  border-bottom: 1px solid #F2F3F5;
  background: #FAFBFC;
}
.canvas-toolbar .hint { color: #86909C; font-size: 13px; }

.canvas-headers {
  display: grid;
  grid-template-columns: 280px 1fr 280px;
  background: #F7F8FA;
  border-bottom: 1px solid #F2F3F5;
}
.canvas-headers .col-header {
  padding: 10px 14px;
  font-weight: 600;
  font-size: 13px;
  color: #1D2129;
}
.canvas-headers .col-header:last-child { grid-column: 3 / 4; }

.canvas-body {
  position: relative;
  display: grid;
  grid-template-columns: 280px 1fr 280px;
  background: #FCFCFD;
  min-height: 200px;
  overflow: auto;
}

.field-col { display: flex; flex-direction: column; }

.field-row {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  margin: 2px 6px;
  background: #fff;
  border: 1px solid #E5E6EB;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
  min-height: 38px;
  user-select: none;
}
.field-row:hover { border-color: #2B5AED; box-shadow: 0 2px 6px rgba(43,90,237,0.12); }
.field-row.selected { background: #EAF1FF; border-color: #2B5AED; box-shadow: 0 0 0 2px rgba(43,90,237,0.18); }
.field-row.mapped { background: linear-gradient(90deg, #fff 0%, #F4FFF9 100%); border-color: #00C9A7; }
.field-row.custom { background: linear-gradient(90deg, #FFF7EA 0%, #fff 100%); border-color: #F7BA1E; }

.field-name {
  flex: 1;
  font-weight: 500;
  font-size: 13px;
  color: #1D2129;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.field-type {
  font-size: 11px;
  color: #86909C;
  font-family: 'SF Mono', Menlo, Consolas, monospace;
}

.badge {
  display: inline-block;
  width: 18px;
  height: 18px;
  line-height: 18px;
  text-align: center;
  border-radius: 50%;
  font-size: 11px;
  color: #fff;
  flex-shrink: 0;
}
.badge-const { background: #F7BA1E; }
.badge-var { background: #722ED1; }

.del-btn {
  width: 18px;
  height: 18px;
  line-height: 16px;
  text-align: center;
  border-radius: 50%;
  background: #F2F3F5;
  color: #86909C;
  font-size: 14px;
  cursor: pointer;
  flex-shrink: 0;
}
.del-btn:hover { background: #F53F3F; color: #fff; }

.anchor {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #2B5AED;
  border: 2px solid #fff;
  box-shadow: 0 0 0 1px #C9CDD4;
}
.anchor-right { right: -5px; }
.anchor-left  { left: -5px; }

.empty-tip {
  padding: 30px 12px;
  text-align: center;
  color: #C9CDD4;
  font-size: 12px;
}

.lines-svg {
  pointer-events: none;
  position: relative;
  width: 100%;
  height: 100%;
}
.line-path {
  pointer-events: stroke;
  cursor: pointer;
  transition: stroke 0.15s;
}
.line-path:hover { stroke: #F53F3F !important; stroke-width: 3; }

.hint-text { color: #86909C; font-size: 12px; margin-top: 4px; }
</style>
