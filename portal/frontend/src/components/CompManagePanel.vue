<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import LangIcon from './LangIcon.vue'
import ContextMenu from './ContextMenu.vue'
import type { MenuItem } from './ContextMenu.vue'
import {
  getComponents, deleteComponent, testComponent, publishComponent,
  offlineComponent, runComponent,
  getComponentFolders, quickPublishComponent, moveComponent, reorderComponents,
  updateComponent,
} from '../api'
import type { ComponentItem, ComponentStatus, FolderItem } from '../types/component'
import { statusLabel, statusColor, STATUS_DEFS } from '../types/component'
import { TYPE_GROUPS_WITH_DATAX } from '../composables/useFileTree'

const emit = defineEmits<{
  (e: 'open', comp: ComponentItem): void
  (e: 'refresh'): void
}>()

// ---- 数据 ----
const loading = ref(false)
const items = ref<ComponentItem[]>([])
const folders = ref<FolderItem[]>([])
const searchVal = ref('')
const currentType = ref<string>('') // '' = 全部
const statusFilter = ref<string>('')
const selectedId = ref<number | null>(null)

// 详情 Drawer
const detailVisible = ref(false)
const detailComp = ref<ComponentItem | null>(null)

// 右键菜单
const contextMenu = reactive({ visible: false, x: 0, y: 0, items: [] as MenuItem[], target: null as ComponentItem | null })

// 剪贴板
const clipboard = ref<{ action: 'copy' | 'cut'; comp: ComponentItem } | null>(null)

// 文件夹折叠状态
const folderCollapsed = reactive<Record<string, boolean>>({})

// ---- 类型导航 ----
const typeNavItems = computed(() => {
  const allCount = items.value.length
  const navs = [
    { type: '', label: '全部', count: allCount },
    ...TYPE_GROUPS_WITH_DATAX.map(g => ({
      type: g.type,
      label: g.label,
      count: items.value.filter(c => c.type === g.type).length,
      color: g.color,
    })),
  ]
  return navs
})

// ---- 过滤后的组件 ----
const filteredItems = computed(() => {
  let list = items.value
  if (currentType.value) {
    list = list.filter(c => c.type === currentType.value)
  }
  if (statusFilter.value) {
    list = list.filter(c => c.status === statusFilter.value)
  }
  const kw = searchVal.value.trim().toLowerCase()
  if (kw) {
    list = list.filter(c => c.name.toLowerCase().includes(kw))
  }
  return list
})

// ---- 按类型和文件夹分组 ----
interface FolderGroup {
  folderId: number | null
  folderName: string
  depth: number
  components: ComponentItem[]
}

interface TypeGroup {
  type: string
  label: string
  color: string
  folders: FolderGroup[]
}

function getTypeFolders(type: string): FolderItem[] {
  return folders.value.filter(f => f.type === type)
}

function buildFolderGroups(type: string, comps: ComponentItem[]): FolderGroup[] {
  const typeFolders = getTypeFolders(type)
  const validFolderIds = new Set(typeFolders.map(f => f.id))

  // 递归构建文件夹树
  function traverse(parentId: number | null, depth: number): FolderGroup[] {
    const childFolders = typeFolders
      .filter(f => (f.parent_id ?? null) === parentId)
      .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0) || a.id - b.id)

    const result: FolderGroup[] = []
    for (const f of childFolders) {
      const childGroups = traverse(f.id, depth + 1)
      const folderComps = comps
        .filter(c => c.folder_id === f.id)
        .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0) || b.id - a.id)
      if (folderComps.length > 0 || childGroups.length > 0) {
        result.push({ folderId: f.id, folderName: f.name, depth, components: folderComps })
        result.push(...childGroups)
      }
    }
    return result
  }

  const result = traverse(null, 0)

  // 未分组组件
  const ungrouped = comps
    .filter(c => {
      const fid = c.folder_id ?? null
      return fid === null || !validFolderIds.has(fid)
    })
    .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0) || b.id - a.id)

  if (ungrouped.length > 0) {
    result.push({ folderId: null, folderName: '未分组', depth: 0, components: ungrouped })
  }

  return result
}

const groupedTypes = computed((): TypeGroup[] => {
  const types = currentType.value ? [currentType.value] : TYPE_GROUPS_WITH_DATAX.map(g => g.type)
  return types.map(type => {
    const cfg = TYPE_GROUPS_WITH_DATAX.find(g => g.type === type)!
    const comps = filteredItems.value.filter(c => c.type === type)
    return {
      type,
      label: cfg.label,
      color: cfg.color,
      folders: buildFolderGroups(type, comps),
    }
  }).filter(g => g.folders.length > 0)
})

// ---- 加载数据 ----
async function loadData() {
  loading.value = true
  try {
    const [cRes, fRes]: any = await Promise.all([
      getComponents({ page_size: 500 }),
      getComponentFolders(),
    ])
    items.value = cRes?.items || []
    folders.value = Array.isArray(fRes) ? fRes : (fRes.items || [])
    selectedId.value = null
  } catch {
    items.value = []
    folders.value = []
  }
  loading.value = false
}

// ---- 辅助函数 ----
function formatDate(t?: string) {
  if (!t) return '—'
  return t.replace('T', ' ').split('.')[0].slice(0, 10)
}

function formatTime(t?: string) {
  if (!t) return '—'
  return t.replace('T', ' ').split('.')[0]
}

function typeLabel(type: string) {
  return TYPE_GROUPS_WITH_DATAX.find(g => g.type === type)?.label || type
}

function canTest(c: ComponentItem) { return c.status === 'draft' || c.status === 'tested' }
function canPublish(c: ComponentItem) { return c.status === 'tested' }
function canQuickPublish(c: ComponentItem) { return c.status === 'draft' }
function canDelete(c: ComponentItem) { return c.status === 'draft' || c.status === 'offline' }

function folderKey(type: string, folderId: number | null) {
  return `${type}-${folderId ?? 'null'}`
}

function isCollapsed(type: string, folderId: number | null) {
  const key = folderKey(type, folderId)
  // 默认展开根级文件夹，折叠深层文件夹
  return folderCollapsed[key] ?? false
}

function toggleFolder(type: string, folderId: number | null) {
  const key = folderKey(type, folderId)
  folderCollapsed[key] = !isCollapsed(type, folderId)
}

// ---- 交互 ----
function onSelect(comp: ComponentItem) {
  selectedId.value = comp.id
}

function onDblClick(comp: ComponentItem) {
  emit('open', comp)
}

function openDetail(comp: ComponentItem) {
  detailComp.value = comp
  detailVisible.value = true
}

// ---- 右键菜单 ----
function buildCompMenuItems(comp: ComponentItem): MenuItem[] {
  const items: MenuItem[] = []
  items.push({ key: 'open', label: '在 IDE 中打开' })
  if (comp.type !== 'datax') {
    items.push({ key: 'run', label: '运行' })
  }
  items.push({ divider: true })

  if (canTest(comp)) {
    items.push({ key: 'test', label: '测试' })
  }
  if (canPublish(comp)) {
    items.push({ key: 'publish', label: '发布' })
  }
  if (canQuickPublish(comp)) {
    items.push({ key: 'quick-publish', label: '快速发布' })
  }
  if (comp.status === 'online') {
    items.push({ key: 'offline', label: '下线' })
  }

  items.push({ divider: true })
  items.push({ key: 'copy', label: '复制' })
  items.push({ key: 'cut', label: '剪切' })
  if (clipboard.value) {
    items.push({ key: 'paste', label: '粘贴到当前文件夹' })
  }
  items.push({
    key: 'move',
    label: '移动到文件夹',
    children: buildMoveToFolderMenu(comp),
  })
  items.push({ divider: true })
  items.push({ key: 'rename', label: '重命名' })
  items.push({ key: 'detail', label: '查看详情' })
  items.push({ divider: true })
  items.push({ key: 'delete', label: '删除', danger: true })
  return items
}

function buildMoveToFolderMenu(comp: ComponentItem): MenuItem[] {
  const typeFolders = folders.value.filter(f => f.type === comp.type)
  const roots = typeFolders.filter(f => f.parent_id == null)
  function buildSub(list: FolderItem[]): MenuItem[] {
    return list.map(f => {
      const children = typeFolders.filter(child => child.parent_id === f.id)
      const item: MenuItem = { key: `move-to-${f.id}`, label: f.name }
      if (children.length > 0) {
        item.children = buildSub(children)
      }
      return item
    })
  }
  const menu = buildSub(roots)
  menu.unshift({ key: 'move-to-0', label: '（无文件夹）' })
  return menu
}

function showContextMenu(e: MouseEvent, comp: ComponentItem) {
  e.preventDefault()
  selectedId.value = comp.id
  contextMenu.x = e.clientX
  contextMenu.y = e.clientY
  contextMenu.items = buildCompMenuItems(comp)
  contextMenu.target = comp
  contextMenu.visible = true
}

async function onMenuSelect(key: string) {
  const comp = contextMenu.target
  if (!comp) return

  if (key === 'open') {
    emit('open', comp)
  } else if (key === 'run') {
    runComp(comp)
  } else if (key === 'test') {
    testComp(comp)
  } else if (key === 'publish') {
    publishComp(comp)
  } else if (key === 'quick-publish') {
    quickPublishComp(comp)
  } else if (key === 'offline') {
    offlineComp(comp)
  } else if (key === 'copy') {
    clipboard.value = { action: 'copy', comp }
    Message.success('已复制')
  } else if (key === 'cut') {
    clipboard.value = { action: 'cut', comp }
    Message.success('已剪切')
  } else if (key === 'paste') {
    await doPaste(comp)
  } else if (key === 'rename') {
    doRename(comp)
  } else if (key === 'detail') {
    openDetail(comp)
  } else if (key === 'delete') {
    deleteComp(comp)
  } else if (key.startsWith('move-to-')) {
    const folderId = parseInt(key.replace('move-to-', ''), 10)
    await doMoveComponent(comp.id, folderId)
  }
}

// ---- 操作 ----
function runComp(c: ComponentItem) {
  Modal.confirm({
    title: '运行组件',
    content: `立即运行「${c.name}」？`,
    onOk: async () => {
      try { await runComponent(c.id); Message.success('已触发运行') } catch (e: any) { Message.error(e.message || '运行失败') }
    },
  })
}

function testComp(c: ComponentItem) {
  Modal.confirm({
    title: '测试组件',
    content: `「${c.name}」测试通过后状态将转为已测试，确认？`,
    onOk: async () => {
      try { await testComponent(c.id); Message.success('测试通过'); loadData(); emit('refresh') } catch (e: any) { Message.error(e.message || '测试失败') }
    },
  })
}

function publishComp(c: ComponentItem) {
  Modal.confirm({
    title: '发布组件',
    content: `「${c.name}」将发布上线，确认？`,
    onOk: async () => {
      try { await publishComponent(c.id); Message.success('已发布'); loadData(); emit('refresh') } catch (e: any) { Message.error(e.message || '发布失败') }
    },
  })
}

function quickPublishComp(c: ComponentItem) {
  Modal.confirm({
    title: '快速发布',
    content: `「${c.name}」将跳过测试直接发布上线，确认？`,
    onOk: async () => {
      try { await quickPublishComponent(c.id); Message.success('已快速发布'); loadData(); emit('refresh') } catch (e: any) { Message.error(e.message || '快速发布失败') }
    },
  })
}

function offlineComp(c: ComponentItem) {
  Modal.confirm({
    title: '下线组件',
    content: `确认下线「${c.name}」？`,
    onOk: async () => {
      try { await offlineComponent(c.id); Message.success('已下线'); loadData(); emit('refresh') } catch (e: any) { Message.error(e.message || '下线失败') }
    },
  })
}

function deleteComp(c: ComponentItem) {
  Modal.confirm({
    title: '删除组件',
    content: `确认删除「${c.name}」？该操作不可恢复`,
    okButtonProps: { status: 'danger' },
    onOk: async () => {
      try { await deleteComponent(c.id); Message.success('已删除'); loadData(); emit('refresh') } catch (e: any) { Message.error(e.message || '删除失败') }
    },
  })
}

async function doMoveComponent(compId: number, folderId: number) {
  try {
    await moveComponent(compId, folderId)
    Message.success('移动成功')
    clipboard.value = null
    await loadData()
    emit('refresh')
  } catch (e: any) { Message.error(e.message || '移动失败') }
}

async function doPaste(targetComp: ComponentItem) {
  const cb = clipboard.value
  if (!cb) return
  const targetFolderId = targetComp.folder_id ?? null
  if (cb.action === 'copy') {
    try {
      const res: any = await import('../api').then(m => m.createComponent({
        name: cb.comp.name + '_copy',
        type: cb.comp.type,
        description: cb.comp.description,
        config_json: cb.comp.config_json || {},
        folder_id: targetFolderId,
      }))
      Message.success('已复制')
      clipboard.value = null
      await loadData()
      emit('refresh')
      emit('open', res)
    } catch (e: any) { Message.error(e.message || '复制失败') }
  } else if (cb.action === 'cut') {
    await doMoveComponent(cb.comp.id, targetFolderId ?? 0)
  }
}

function doRename(c: ComponentItem) {
  const newName = window.prompt('重命名组件', c.name)
  if (!newName || newName.trim() === '' || newName.trim() === c.name) return
  updateComponent(c.id, { name: newName.trim() }).then(() => {
    Message.success('已重命名')
    loadData()
    emit('refresh')
  }).catch((e: any) => Message.error(e.message || '重命名失败'))
}

// ---- 拖拽 ----
const dragState = reactive({
  draggingId: null as number | null,
  dragComp: null as ComponentItem | null,
  dropTargetFolderId: null as number | null,
})

function onDragStart(e: DragEvent, comp: ComponentItem) {
  dragState.draggingId = comp.id
  dragState.dragComp = comp
  e.dataTransfer!.effectAllowed = 'move'
  e.dataTransfer!.setData('application/json', JSON.stringify({ id: comp.id, type: comp.type, folder_id: comp.folder_id }))
}

function onDragOverFolder(e: DragEvent, folderId: number | null, compType: string) {
  e.preventDefault()
  if (!dragState.dragComp) return
  if (dragState.dragComp.type !== compType) {
    e.dataTransfer!.dropEffect = 'none'
    dragState.dropTargetFolderId = null
    return
  }
  e.dataTransfer!.dropEffect = 'move'
  dragState.dropTargetFolderId = folderId
}

function onDropFolder(e: DragEvent, folderId: number | null, compType: string) {
  e.preventDefault()
  const dataStr = e.dataTransfer!.getData('application/json')
  if (!dataStr) return
  const data = JSON.parse(dataStr)
  if (data.type !== compType) return
  const targetFolder = folderId ?? 0
  doMoveComponent(data.id, targetFolder)
  dragState.draggingId = null
  dragState.dragComp = null
  dragState.dropTargetFolderId = null
}

function onDragEnd() {
  dragState.draggingId = null
  dragState.dragComp = null
  dragState.dropTargetFolderId = null
}

// ---- 状态可视化 ----
function statusTransitionPath(status: string): { label: string; color: string; current: boolean }[] {
  const path = [
    { key: 'draft',   label: '草稿',   color: '#86909C' },
    { key: 'tested',  label: '已测试', color: '#0FC6C2' },
    { key: 'online',  label: '已上线', color: '#00B42A' },
    { key: 'offline', label: '已下线', color: '#FF7D00' },
  ]
  return path.map(p => ({ label: p.label, color: p.color, current: p.key === status }))
}

onMounted(() => loadData())

defineExpose({ loadData })
</script>

<template>
  <div class="finder-panel">
    <!-- 左侧类型导航 -->
    <div class="finder-sidebar">
      <div class="nav-title">组件类型</div>
      <div class="nav-list">
        <div
          v-for="nav in typeNavItems"
          :key="nav.type"
          :class="['nav-item', { active: currentType === nav.type }]"
          @click="currentType = nav.type"
        >
          <LangIcon v-if="nav.type" :type="nav.type" :size="16" />
          <span v-else class="nav-icon-all">◈</span>
          <span class="nav-label">{{ nav.label }}</span>
          <span class="nav-count">{{ nav.count }}</span>
        </div>
      </div>
    </div>

    <!-- 右侧内容区 -->
    <div class="finder-content">
      <!-- 顶部工具栏 -->
      <div class="finder-toolbar">
        <div class="toolbar-left">
          <span class="breadcrumb">
            <span class="breadcrumb-root" @click="currentType = ''">全部</span>
            <span v-if="currentType" class="breadcrumb-sep">›</span>
            <span v-if="currentType" class="breadcrumb-current">{{ typeLabel(currentType) }}</span>
          </span>
        </div>
        <div class="toolbar-center">
          <a-input-search
            v-model="searchVal"
            placeholder="搜索组件名"
            size="small"
            style="width: 200px;"
            @search="() => {}"
            allow-clear
          />
          <a-select v-model="statusFilter" placeholder="全部状态" size="small" style="width: 120px;" allow-clear>
            <a-option value="">全部状态</a-option>
            <a-option v-for="st in Object.keys(STATUS_DEFS)" :key="st" :value="st">
              <span class="status-dot-inline" :style="{ background: statusColor(st) }"></span>
              {{ statusLabel(st) }}
            </a-option>
          </a-select>
        </div>
        <div class="toolbar-right">
          <span class="total-count">共 {{ filteredItems.length }} 个组件</span>
        </div>
      </div>

      <!-- 组件列表 -->
      <div class="finder-list">
        <a-spin v-if="loading" style="display: flex; justify-content: center; padding: 60px;" />
        <template v-else-if="groupedTypes.length">
          <div v-for="typeGroup in groupedTypes" :key="typeGroup.type" class="type-section">
            <!-- 类型标题栏 -->
            <div class="type-header" :style="{ borderLeftColor: typeGroup.color }">
              <span class="type-icon" :style="{ color: typeGroup.color }">📂</span>
              <span class="type-label">{{ typeGroup.label }}</span>
              <span class="type-count">{{ typeGroup.folders.reduce((sum, f) => sum + f.components.length, 0) }}</span>
            </div>

            <!-- 文件夹组 -->
            <div class="type-body">
              <div
                v-for="folder in typeGroup.folders"
                :key="folderKey(typeGroup.type, folder.folderId)"
                class="folder-group"
                :style="{ marginLeft: `${folder.depth * 16}px` }"
              >
                <!-- 文件夹头 -->
                <div
                  class="folder-header"
                  :class="{ 'drop-target': dragState.dropTargetFolderId === folder.folderId && dragState.dragComp?.type === typeGroup.type }"
                  @click="toggleFolder(typeGroup.type, folder.folderId)"
                  @dragover.prevent="onDragOverFolder($event, folder.folderId, typeGroup.type)"
                  @drop.prevent="onDropFolder($event, folder.folderId, typeGroup.type)"
                >
                  <span class="folder-caret">{{ isCollapsed(typeGroup.type, folder.folderId) ? '▸' : '▾' }}</span>
                  <span class="folder-icon">📁</span>
                  <span class="folder-name">{{ folder.folderName }}</span>
                  <span class="folder-count">{{ folder.components.length }}</span>
                </div>

                <!-- 组件列表 -->
                <div v-show="!isCollapsed(typeGroup.type, folder.folderId)" class="folder-items">
                  <div
                    v-for="comp in folder.components"
                    :key="comp.id"
                    :class="['comp-row', { selected: selectedId === comp.id, dragging: dragState.draggingId === comp.id }]"
                    draggable="true"
                    @click="onSelect(comp)"
                    @dblclick="onDblClick(comp)"
                    @contextmenu.prevent="showContextMenu($event, comp)"
                    @dragstart="onDragStart($event, comp)"
                    @dragend="onDragEnd"
                  >
                    <LangIcon :type="comp.type" :size="20" />
                    <span class="comp-name">{{ comp.name }}</span>
                    <span class="comp-version">v{{ comp.version }}</span>
                    <span class="comp-status">
                      <span class="status-dot-inline" :style="{ background: statusColor(comp.status) }"></span>
                      <span :style="{ color: statusColor(comp.status) }">{{ statusLabel(comp.status) }}</span>
                    </span>
                    <span class="comp-desc" :title="comp.description">{{ comp.description || '—' }}</span>
                    <span class="comp-time">{{ formatDate(comp.updated_at) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>

        <div v-else class="empty-state">
          <p>暂无组件</p>
          <p class="text-muted">调整筛选条件或从左侧选择其他类型</p>
        </div>
      </div>
    </div>

    <!-- 详情 Drawer -->
    <a-drawer
      v-model:visible="detailVisible"
      :width="420"
      :footer="false"
      unmount-on-close
      :title="detailComp ? detailComp.name : ''"
    >
      <div v-if="detailComp" class="detail-body">
        <!-- 基本信息 -->
        <div class="detail-section">
          <div class="detail-section-title">基本信息</div>
          <div class="detail-info-grid">
            <div class="detail-info-item">
              <span class="detail-info-label">类型</span>
              <span class="detail-info-value">
                <span class="type-badge" :style="{ background: TYPE_GROUPS_WITH_DATAX.find(g => g.type === detailComp!.type)?.color }">
                  {{ typeLabel(detailComp!.type) }}
                </span>
              </span>
            </div>
            <div class="detail-info-item">
              <span class="detail-info-label">状态</span>
              <span class="detail-info-value">
                <span class="status-badge">
                  <span class="status-dot-lg" :style="{ background: statusColor(detailComp.status) }"></span>
                  {{ statusLabel(detailComp.status) }}
                </span>
              </span>
            </div>
            <div class="detail-info-item">
              <span class="detail-info-label">创建者</span>
              <span class="detail-info-value">{{ detailComp.created_by_name || detailComp.created_by || '—' }}</span>
            </div>
            <div class="detail-info-item">
              <span class="detail-info-label">创建时间</span>
              <span class="detail-info-value">{{ formatTime(detailComp.created_at) }}</span>
            </div>
            <div class="detail-info-item">
              <span class="detail-info-label">更新时间</span>
              <span class="detail-info-value">{{ formatTime(detailComp.updated_at) }}</span>
            </div>
          </div>
        </div>

        <!-- 状态流转 -->
        <div class="detail-section">
          <div class="detail-section-title">状态流转</div>
          <div class="status-flow">
            <div
              v-for="(node, idx) in statusTransitionPath(detailComp.status)"
              :key="node.label"
              class="flow-node"
            >
              <span class="flow-dot" :style="{ background: node.color, borderColor: node.color }"></span>
              <span class="flow-label" :style="{ color: node.color, fontWeight: node.current ? 600 : 400 }">
                {{ node.label }}
              </span>
              <span v-if="idx < statusTransitionPath(detailComp.status).length - 1" class="flow-arrow">→</span>
            </div>
          </div>
        </div>

        <!-- 描述 -->
        <div v-if="detailComp.description" class="detail-section">
          <div class="detail-section-title">描述</div>
          <div class="detail-desc">{{ detailComp.description }}</div>
        </div>

        <!-- 操作 -->
        <div class="detail-actions">
          <a-button type="primary" long @click="emit('open', detailComp); detailVisible = false">
            在 IDE 中打开
          </a-button>
        </div>
      </div>
    </a-drawer>

    <!-- 右键菜单 -->
    <ContextMenu
      v-model:visible="contextMenu.visible"
      :x="contextMenu.x"
      :y="contextMenu.y"
      :items="contextMenu.items"
      @select="onMenuSelect"
    />
  </div>
</template>

<style scoped>
.finder-panel {
  display: flex;
  height: 100%;
  overflow: hidden;
  background: #fff;
}

/* ---- 左侧导航 ---- */
.finder-sidebar {
  width: 200px;
  flex-shrink: 0;
  background: #FAFBFC;
  border-right: 1px solid #E5E6EB;
  padding: 16px 0;
  overflow-y: auto;
}
.nav-title {
  font-size: 11px;
  font-weight: 600;
  color: #86909C;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 0 16px 8px;
}
.nav-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0 8px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: #1D2129;
  transition: all 0.12s;
  user-select: none;
}
.nav-item:hover {
  background: #F2F3F5;
}
.nav-item.active {
  background: #EAF1FF;
  color: #2B5AED;
  font-weight: 500;
}
.nav-icon-all {
  font-size: 12px;
  color: #86909C;
  width: 20px;
  text-align: center;
}
.nav-label {
  flex: 1;
}
.nav-count {
  font-size: 11px;
  background: #E5E6EB;
  color: #86909C;
  padding: 0 6px;
  height: 16px;
  line-height: 16px;
  border-radius: 8px;
  flex-shrink: 0;
}
.nav-item.active .nav-count {
  background: #2B5AED;
  color: #fff;
}

/* ---- 右侧内容区 ---- */
.finder-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

/* 顶部工具栏 */
.finder-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 16px;
  border-bottom: 1px solid #E5E6EB;
  background: #fff;
  flex-shrink: 0;
}
.toolbar-left {
  display: flex;
  align-items: center;
}
.toolbar-center {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  justify-content: center;
}
.toolbar-right {
  display: flex;
  align-items: center;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}
.breadcrumb-root {
  color: #2B5AED;
  cursor: pointer;
}
.breadcrumb-root:hover {
  text-decoration: underline;
}
.breadcrumb-sep {
  color: #C9CDD4;
}
.breadcrumb-current {
  color: #1D2129;
  font-weight: 500;
}

.total-count {
  font-size: 12px;
  color: #86909C;
}

/* 状态筛选下拉中的圆点 */
.status-dot-inline {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
}

/* ---- 列表区域 ---- */
.finder-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 16px 16px;
}

.type-section {
  margin-bottom: 16px;
}
.type-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 600;
  color: #1D2129;
  border-left: 3px solid;
  background: #FAFBFC;
  border-radius: 0 6px 6px 0;
  margin-bottom: 4px;
}
.type-icon {
  font-size: 14px;
}
.type-count {
  font-size: 11px;
  background: #E5E6EB;
  color: #86909C;
  padding: 0 6px;
  height: 16px;
  line-height: 16px;
  border-radius: 8px;
  margin-left: auto;
}

.type-body {
  padding-left: 8px;
}

/* 文件夹组 */
.folder-group {
  margin-bottom: 2px;
}
.folder-header {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  font-size: 12px;
  font-weight: 500;
  color: #4E5969;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.12s;
  user-select: none;
}
.folder-header:hover {
  background: #F2F3F5;
}
.folder-header.drop-target {
  background: #EAF1FF !important;
  box-shadow: inset 0 0 0 1px #2B5AED;
}
.folder-caret {
  font-size: 10px;
  color: #86909C;
  flex-shrink: 0;
}
.folder-icon {
  font-size: 13px;
  color: #F7BA1E;
  flex-shrink: 0;
}
.folder-name {
  flex: 1;
}
.folder-count {
  font-size: 11px;
  color: #86909C;
  background: #F2F3F5;
  padding: 0 5px;
  border-radius: 4px;
}

/* 组件行 */
.folder-items {
  padding-left: 16px;
}
.comp-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 12px;
  font-size: 13px;
  cursor: pointer;
  border-radius: 5px;
  transition: background 0.1s;
  user-select: none;
}
.comp-row:hover {
  background: #F2F3F5;
}
.comp-row.selected {
  background: #EAF1FF;
}
.comp-row.dragging {
  opacity: 0.5;
}
.comp-name {
  font-weight: 500;
  color: #1D2129;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  max-width: 200px;
}
.comp-version {
  font-size: 11px;
  color: #86909C;
  font-family: 'JetBrains Mono', monospace;
  flex-shrink: 0;
}
.comp-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  flex-shrink: 0;
  width: 80px;
}
.comp-desc {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #86909C;
  font-size: 12px;
}
.comp-time {
  font-size: 12px;
  color: #86909C;
  font-family: 'JetBrains Mono', monospace;
  flex-shrink: 0;
  width: 90px;
  text-align: right;
}

/* 空状态 */
.empty-state {
  padding: 60px 0;
  text-align: center;
  color: #86909C;
}
.empty-state p:first-child {
  font-size: 14px;
  margin-bottom: 4px;
}
.text-muted {
  color: #86909C;
  font-size: 12px;
}

/* ---- 详情 Drawer ---- */
.detail-header {
  display: flex;
  align-items: center;
  gap: 10px;
}
.detail-title {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.detail-name {
  font-size: 15px;
  font-weight: 600;
  color: #1D2129;
}
.detail-version {
  font-size: 12px;
  color: #86909C;
  font-family: 'JetBrains Mono', monospace;
}

.detail-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.detail-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.detail-section-title {
  font-size: 13px;
  font-weight: 600;
  color: #1D2129;
  padding-bottom: 6px;
  border-bottom: 1px solid #F2F3F5;
}

.detail-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px 16px;
}
.detail-info-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.detail-info-label {
  font-size: 11px;
  color: #86909C;
}
.detail-info-value {
  font-size: 13px;
  color: #1D2129;
}

.type-badge {
  display: inline-block;
  color: #fff;
  font-size: 11px;
  font-weight: 500;
  padding: 1px 8px;
  border-radius: 4px;
}
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}
.status-dot-lg {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-flow {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}
.flow-node {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}
.flow-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: 2px solid;
}
.flow-arrow {
  color: #C9CDD4;
  font-size: 12px;
}
.previous-status {
  margin-top: 8px;
  font-size: 12px;
}

.detail-desc {
  font-size: 13px;
  color: #4E5969;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}

.detail-actions {
  margin-top: 8px;
}
</style>
