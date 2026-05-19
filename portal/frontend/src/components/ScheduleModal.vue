<template>
  <a-modal
    :visible="visible"
    title="调度设置"
    :width="520"
    @cancel="$emit('update:visible', false)"
    @ok="handleSave"
    ok-text="保存调度配置"
    :unmount-on-close="true"
  >
    <div class="schedule-modal">
      <!-- 调度模式 -->
      <div class="section">
        <div class="section-label">调度模式</div>
        <a-radio-group v-model="mode" direction="vertical">
          <a-radio value="none">不调度（仅手动触发）</a-radio>
          <a-radio value="periodic">周期调度</a-radio>
        </a-radio-group>
      </div>

      <!-- 周期配置 -->
      <div v-if="mode === 'periodic'" class="section period-section">
        <div class="field-row">
          <span class="field-label">频率</span>
          <a-select v-model="frequency" style="width: 120px">
            <a-option value="daily">每天</a-option>
            <a-option value="weekly">每周</a-option>
            <a-option value="monthly">每月</a-option>
            <a-option value="custom">自定义</a-option>
          </a-select>
        </div>

        <div v-if="frequency !== 'custom'" class="field-row">
          <span class="field-label">执行时间</span>
          <div class="time-picker">
            <a-select v-model="hour" style="width: 72px">
              <a-option v-for="h in 24" :key="h-1" :value="h-1">{{ String(h-1).padStart(2,'0') }}</a-option>
            </a-select>
            <span class="time-sep">:</span>
            <a-select v-model="minute" style="width: 72px">
              <a-option v-for="m in minuteOptions" :key="m" :value="m">{{ String(m).padStart(2,'0') }}</a-option>
            </a-select>
          </div>
        </div>

        <!-- 每周：周几选择 -->
        <div v-if="frequency === 'weekly'" class="field-row">
          <span class="field-label">周几</span>
          <div class="weekday-group">
            <div
              v-for="(label, idx) in weekLabels"
              :key="idx"
              class="weekday-chip"
              :class="{ active: weekdays.includes(idx + 1) }"
              @click="toggleWeekday(idx + 1)"
            >{{ label }}</div>
          </div>
        </div>

        <!-- 每月：日期选择 -->
        <div v-if="frequency === 'monthly'" class="field-row">
          <span class="field-label">日期</span>
          <div class="monthday-group">
            <div
              v-for="d in 31"
              :key="d"
              class="monthday-chip"
              :class="{ active: monthDays.includes(d) }"
              @click="toggleMonthDay(d)"
            >{{ d }}</div>
          </div>
        </div>

        <!-- 自定义 CRON -->
        <div v-if="frequency === 'custom'" class="field-row">
          <span class="field-label">CRON</span>
          <a-input v-model="customCron" placeholder="0 0 22 * * ?" style="flex:1" />
        </div>
      </div>

      <!-- 预览 -->
      <div v-if="mode === 'periodic' && generatedCron" class="preview-section">
        <div class="preview-cron">
          <span class="preview-label">CRON</span>
          <code>{{ generatedCron }}</code>
        </div>
        <div class="preview-times" v-if="previewTimes.length">
          <span class="preview-label">未来执行</span>
          <div class="preview-list">
            <span v-for="(t, i) in previewTimes" :key="i" class="preview-time">{{ t }}</span>
          </div>
        </div>
        <div v-if="cronError" class="preview-error">{{ cronError }}</div>
      </div>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import dayjs from 'dayjs'
import { cronPreview } from '../api'

const props = defineProps<{
  visible: boolean
  cronExpression: string
  scheduleStatus: string
}>()

const emit = defineEmits<{
  'update:visible': [val: boolean]
  'save': [cron: string]
}>()

const mode = ref<'none' | 'periodic'>('none')
const frequency = ref<'daily' | 'weekly' | 'monthly' | 'custom'>('daily')
const hour = ref(22)
const minute = ref(0)
const weekdays = ref<number[]>([1, 2, 3, 4, 5])
const monthDays = ref<number[]>([1])
const customCron = ref('')
const previewTimes = ref<string[]>([])
const cronError = ref('')

const weekLabels = ['一', '二', '三', '四', '五', '六', '日']
const minuteOptions = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]

// 生成 CRON（DS 6段格式，带秒）
const generatedCron = computed(() => {
  if (mode.value === 'none') return ''
  switch (frequency.value) {
    case 'daily':
      return `0 ${minute.value} ${hour.value} * * ?`
    case 'weekly':
      if (!weekdays.value.length) return ''
      return `0 ${minute.value} ${hour.value} ? * ${weekdays.value.join(',')}`
    case 'monthly':
      if (!monthDays.value.length) return ''
      return `0 ${minute.value} ${hour.value} ${monthDays.value.join(',')} * ?`
    case 'custom':
      return customCron.value.trim()
    default:
      return ''
  }
})

function toggleWeekday(d: number) {
  const idx = weekdays.value.indexOf(d)
  if (idx >= 0) weekdays.value.splice(idx, 1)
  else weekdays.value.push(d)
  weekdays.value.sort()
}

function toggleMonthDay(d: number) {
  const idx = monthDays.value.indexOf(d)
  if (idx >= 0) monthDays.value.splice(idx, 1)
  else monthDays.value.push(d)
  monthDays.value.sort((a, b) => a - b)
}

// 前端计算预览（简单场景）
function computeLocalPreview(): string[] {
  if (frequency.value === 'custom') return []
  const times: string[] = []
  let base = dayjs().second(0).millisecond(0)
  for (let i = 0; i < 3; i++) {
    let next = getNextFire(base)
    if (!next) break
    times.push(next.format('YYYY-MM-DD HH:mm'))
    base = next.add(1, 'minute')
  }
  return times
}

function getNextFire(from: dayjs.Dayjs): dayjs.Dayjs | null {
  let cursor = from.minute(minute.value).hour(hour.value).second(0)
  if (cursor.isBefore(from) || cursor.isSame(from)) {
    cursor = cursor.add(1, 'day')
  }
  if (frequency.value === 'daily') return cursor
  if (frequency.value === 'weekly') {
    for (let i = 0; i < 8; i++) {
      const dow = cursor.day() === 0 ? 7 : cursor.day()
      if (weekdays.value.includes(dow)) return cursor
      cursor = cursor.add(1, 'day')
    }
  }
  if (frequency.value === 'monthly') {
    for (let i = 0; i < 62; i++) {
      if (monthDays.value.includes(cursor.date())) return cursor
      cursor = cursor.add(1, 'day')
    }
  }
  return null
}

// 后端预览（自定义 CRON）
async function fetchPreview() {
  if (!generatedCron.value) { previewTimes.value = []; cronError.value = ''; return }
  if (frequency.value !== 'custom') {
    previewTimes.value = computeLocalPreview()
    cronError.value = ''
    return
  }
  try {
    const res: any = await cronPreview(generatedCron.value)
    if (res.error) { cronError.value = res.error; previewTimes.value = [] }
    else { previewTimes.value = res.times || []; cronError.value = '' }
  } catch { cronError.value = '预览请求失败'; previewTimes.value = [] }
}

watch(generatedCron, () => { fetchPreview() }, { immediate: false })

// 打开时反解析 CRON
watch(() => props.visible, (v) => {
  if (v) parseCron(props.cronExpression)
})

function parseCron(cron: string) {
  if (!cron || !cron.trim()) { mode.value = 'none'; return }
  mode.value = 'periodic'
  const parts = cron.trim().split(/\s+/)
  const p = parts.length === 6 ? parts.slice(1) : parts
  if (p.length < 5) { frequency.value = 'custom'; customCron.value = cron; return }
  const [min, hr, dom, , dow] = p
  hour.value = parseInt(hr) || 0
  minute.value = parseInt(min) || 0

  if ((dom === '*' || dom === '?') && (dow === '*' || dow === '?')) {
    frequency.value = 'daily'
  } else if ((dom === '?' || dom === '*') && dow !== '*' && dow !== '?') {
    frequency.value = 'weekly'
    weekdays.value = dow.split(',').map(Number).filter(n => !isNaN(n))
  } else if (dow === '?' || dow === '*') {
    if (dom !== '*' && dom !== '?') {
      frequency.value = 'monthly'
      monthDays.value = dom.split(',').map(Number).filter(n => !isNaN(n))
    } else {
      frequency.value = 'custom'
      customCron.value = cron
    }
  } else {
    frequency.value = 'custom'
    customCron.value = cron
  }
  // 触发预览
  setTimeout(() => fetchPreview(), 100)
}

function handleSave() {
  const cron = mode.value === 'none' ? '' : generatedCron.value
  emit('save', cron)
  emit('update:visible', false)
}

onMounted(() => {
  if (props.visible) parseCron(props.cronExpression)
})
</script>

<style scoped>
.schedule-modal { display: flex; flex-direction: column; gap: 20px; }
.section-label { font-size: 13px; font-weight: 600; color: #1D2129; margin-bottom: 8px; }
.period-section {
  background: #F7F8FA; border-radius: 8px; padding: 16px;
  display: flex; flex-direction: column; gap: 14px;
}
.field-row { display: flex; align-items: center; gap: 12px; }
.field-label { font-size: 13px; color: #4E5969; width: 60px; flex-shrink: 0; }
.time-picker { display: flex; align-items: center; gap: 4px; }
.time-sep { font-size: 16px; color: #86909C; font-weight: 600; }

.weekday-group { display: flex; gap: 6px; flex-wrap: wrap; }
.weekday-chip {
  width: 32px; height: 32px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; cursor: pointer; border: 1px solid #E5E8ED;
  background: #fff; color: #4E5969; transition: all 0.15s;
}
.weekday-chip:hover { border-color: #165DFF; color: #165DFF; }
.weekday-chip.active { background: #165DFF; color: #fff; border-color: #165DFF; }

.monthday-group { display: flex; gap: 4px; flex-wrap: wrap; max-width: 340px; }
.monthday-chip {
  width: 28px; height: 28px; border-radius: 4px;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; cursor: pointer; border: 1px solid #E5E8ED;
  background: #fff; color: #4E5969; transition: all 0.15s;
}
.monthday-chip:hover { border-color: #165DFF; color: #165DFF; }
.monthday-chip.active { background: #165DFF; color: #fff; border-color: #165DFF; }

.preview-section {
  background: #FAFBFC; border: 1px solid #E5E8ED; border-radius: 8px; padding: 12px 16px;
  display: flex; flex-direction: column; gap: 8px;
}
.preview-cron { display: flex; align-items: center; gap: 8px; }
.preview-cron code {
  font-family: 'JetBrains Mono', monospace; font-size: 13px;
  color: #165DFF; font-weight: 500;
}
.preview-label { font-size: 11px; color: #86909C; width: 60px; flex-shrink: 0; }
.preview-times { display: flex; align-items: flex-start; gap: 8px; }
.preview-list { display: flex; flex-wrap: wrap; gap: 6px; }
.preview-time {
  font-family: 'JetBrains Mono', monospace; font-size: 12px;
  color: #1D2129; background: #fff; border: 1px solid #E5E8ED;
  padding: 2px 8px; border-radius: 4px;
}
.preview-error { font-size: 12px; color: #F53F3F; }
</style>
