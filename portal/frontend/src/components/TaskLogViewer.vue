<template>
  <div class="task-log-viewer">
    <!-- 工具栏 -->
    <div class="log-toolbar">
      <div class="log-stats">
        <span class="stat-item">总行数: {{ stats.total_lines || 0 }}</span>
        <span class="stat-item error">Error: {{ stats.error_count || 0 }}</span>
        <span class="stat-item warn">Warn: {{ stats.warn_count || 0 }}</span>
        <span class="stat-item info">Info: {{ stats.info_count || 0 }}</span>
        <span v-if="isRealtime" class="realtime-indicator">
          <span class="dot"></span> 实时中
        </span>
        <span v-else-if="stats.is_archived" class="archived-indicator">已归档</span>
      </div>
      <div class="log-controls">
        <a-input-search
          v-model="searchKeyword"
          placeholder="搜索日志..."
          size="small"
          style="width: 200px"
          allow-clear
          @search="onSearch"
        />
        <a-radio-group v-model="levelFilter" type="button" size="small">
          <a-radio value="">全部</a-radio>
          <a-radio value="ERROR">ERROR</a-radio>
          <a-radio value="WARN">WARN</a-radio>
          <a-radio value="INFO">INFO</a-radio>
          <a-radio value="DEBUG">DEBUG</a-radio>
        </a-radio-group>
        <a-checkbox v-model="autoScroll" @change="onAutoScrollChange">自动滚动</a-checkbox>
        <a-button size="small" @click="refreshLog">
          <template #icon><icon-refresh /></template>
          刷新
        </a-button>
      </div>
    </div>

    <!-- 日志内容 -->
    <div ref="logContainer" class="log-content" @scroll="onScroll">
      <div v-if="filteredLines.length === 0" class="log-empty">
        {{ loading ? '加载中...' : '暂无日志' }}
      </div>
      <div
        v-for="(line, index) in filteredLines"
        :key="index"
        class="log-line"
        :class="getLineClass(line)"
        v-html="highlightLine(line)"
      />
    </div>

    <!-- 底部状态栏 -->
    <div class="log-footer">
      <span>显示 {{ filteredLines.length }} / {{ lines.length }} 行</span>
      <span v-if="searchKeyword && searchResults.length > 0">
        找到 {{ searchResults.length }} 处匹配
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import { IconRefresh } from '@arco-design/web-vue/es/icon'

interface Props {
  taskId: number
  source?: 'local' | 'ds' | 'auto'
}

const props = defineProps<Props>()

const loading = ref(false)
const lines = ref<string[]>([])
const stats = ref<Record<string, any>>({})
const searchKeyword = ref('')
const levelFilter = ref('')
const autoScroll = ref(true)
const logContainer = ref<HTMLElement>()
const isRealtime = ref(false)
const eventSource = ref<EventSource | null>(null)
const searchResults = ref<number[]>([])
const scrollLocked = ref(false)

const filteredLines = computed(() => {
  let result = lines.value
  if (levelFilter.value) {
    const level = levelFilter.value.toUpperCase()
    result = result.filter(ln => ln.toUpperCase().includes(`[${level}]`) || ln.toUpperCase().includes(level))
  }
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    result = result.filter(ln => ln.toLowerCase().includes(kw))
  }
  return result
})

function getLineClass(line: string): string {
  const upper = line.toUpperCase()
  if (upper.includes('[ERROR]') || upper.includes(' ERROR ')) return 'level-error'
  if (upper.includes('[WARN]') || upper.includes(' WARNING ') || upper.includes(' WARN ')) return 'level-warn'
  if (upper.includes('[DEBUG]') || upper.includes(' DEBUG ')) return 'level-debug'
  return 'level-info'
}

function escapeRegExp(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function highlightLine(line: string): string {
  if (!searchKeyword.value) return escapeHtml(line)
  const kw = escapeRegExp(escapeHtml(searchKeyword.value))
  const regex = new RegExp(`(${kw})`, 'gi')
  return escapeHtml(line).replace(regex, '<mark>$1</mark>')
}

function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

async function refreshLog() {
  loading.value = true
  try {
    const res = await fetch(`/api/ds/tasks/${props.taskId}/log?limit=10000`, {
      credentials: 'include',
    })
    if (!res.ok) throw new Error('获取日志失败')
    const data = await res.json()
    lines.value = data.lines || data.log?.split('\n') || []
    stats.value = data.stats || {}
    isRealtime.value = !stats.value.is_archived
    if (autoScroll.value) {
      nextTick(() => scrollToBottom())
    }
  } catch (e: any) {
    Message.error(e.message || '获取日志失败')
  } finally {
    loading.value = false
  }
}

async function fetchStats() {
  try {
    const res = await fetch(`/api/ds/tasks/${props.taskId}/log/stats`, {
      credentials: 'include',
    })
    if (res.ok) {
      stats.value = await res.json()
      isRealtime.value = !stats.value.is_archived
    }
  } catch {
    // 静默失败
  }
}

function onSearch() {
  if (!searchKeyword.value) {
    searchResults.value = []
    return
  }
  const kw = searchKeyword.value.toLowerCase()
  searchResults.value = lines.value
    .map((ln, i) => (ln.toLowerCase().includes(kw) ? i : -1))
    .filter(i => i >= 0)
}

function onAutoScrollChange() {
  if (autoScroll.value) {
    scrollToBottom()
  }
}

function scrollToBottom() {
  const el = logContainer.value
  if (el) {
    el.scrollTop = el.scrollHeight
  }
}

function onScroll() {
  const el = logContainer.value
  if (!el) return
  const nearBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 50
  if (!nearBottom && autoScroll.value) {
    scrollLocked.value = true
  } else if (nearBottom) {
    scrollLocked.value = false
  }
}

function startRealtimeStream() {
  if (eventSource.value) return
  const es = new EventSource(`/api/ds/tasks/${props.taskId}/log/stream`, {
    withCredentials: true,
  })
  es.onmessage = (event) => {
    // SSE 默认消息
  }
  es.addEventListener('log', (event) => {
    lines.value.push(event.data)
    if (autoScroll.value && !scrollLocked.value) {
      nextTick(() => scrollToBottom())
    }
  })
  es.addEventListener('status', (event) => {
    stats.value.task_state = event.data
  })
  es.addEventListener('stats', (event) => {
    try {
      stats.value.summary = JSON.parse(event.data)
    } catch {
      // ignore
    }
  })
  es.addEventListener('done', () => {
    isRealtime.value = false
    es.close()
    eventSource.value = null
  })
  es.onerror = () => {
    es.close()
    eventSource.value = null
    // 3 秒后重连
    setTimeout(() => {
      if (isRealtime.value) startRealtimeStream()
    }, 3000)
  }
  eventSource.value = es
  isRealtime.value = true
}

watch(() => props.taskId, () => {
  lines.value = []
  refreshLog()
  fetchStats()
  if (eventSource.value) {
    eventSource.value.close()
    eventSource.value = null
  }
  startRealtimeStream()
}, { immediate: true })

onUnmounted(() => {
  if (eventSource.value) {
    eventSource.value.close()
    eventSource.value = null
  }
})
</script>

<style scoped>
.task-log-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1e1e1e;
  color: #d4d4d4;
  border-radius: 4px;
  overflow: hidden;
}

.log-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #2d2d2d;
  border-bottom: 1px solid #3e3e3e;
  gap: 12px;
  flex-wrap: wrap;
}

.log-stats {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 12px;
}

.stat-item {
  padding: 2px 8px;
  border-radius: 3px;
  background: #3e3e3e;
}

.stat-item.error {
  background: #5c2b2b;
  color: #ff6b6b;
}

.stat-item.warn {
  background: #5c4b1e;
  color: #ffd93d;
}

.stat-item.info {
  background: #1e3a5c;
  color: #6bcb77;
}

.realtime-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #6bcb77;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #6bcb77;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.archived-indicator {
  color: #888;
}

.log-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.log-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px 12px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}

.log-empty {
  text-align: center;
  padding: 40px;
  color: #666;
}

.log-line {
  padding: 1px 0;
}

.log-line :deep(mark) {
  background: #ffd93d;
  color: #1e1e1e;
  padding: 0 2px;
  border-radius: 2px;
}

.level-error {
  color: #ff6b6b;
}

.level-warn {
  color: #ffd93d;
}

.level-debug {
  color: #888;
}

.level-info {
  color: #d4d4d4;
}

.log-footer {
  display: flex;
  justify-content: space-between;
  padding: 6px 12px;
  background: #2d2d2d;
  border-top: 1px solid #3e3e3e;
  font-size: 11px;
  color: #888;
}
</style>
