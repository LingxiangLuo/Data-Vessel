<template>
  <div class="ide-wrap">
    <!-- 视图切换头部 -->
    <div class="view-header">
      <div class="view-tabs">
        <div
          class="view-tab"
          :class="{ active: viewMode === 'ide' }"
          @click="viewMode = 'ide'"
        >
          <icon-code /> IDE 视图
        </div>
        <div
          class="view-tab"
          :class="{ active: viewMode === 'manage' }"
          @click="switchToManage"
        >
          <icon-list /> 管理视图
        </div>
      </div>
    </div>

    <!-- 左侧文件夹树（仅 IDE 视图显示） -->
    <div class="ide-body">
    <div v-show="viewMode === 'ide'" class="ide-sidebar">
      <div class="sidebar-header">
        <span class="sidebar-title">组件开发</span>
      </div>
      <div class="sidebar-search">
        <a-input v-model="searchKw" size="small" placeholder="搜索" allow-clear>
          <template #prefix><icon-search /></template>
        </a-input>
      </div>
      <div class="comp-tree">
        <template v-for="grp in typeGroups" :key="grp.type">
          <!-- 类型组标题 -->
          <div
            class="grp-header"
            :class="{ 'drop-target': dragState.dropTargetId === grp.type && dragState.dropKind === 'group' }"
            @click="toggleGrp(grp.type)"
            @dragover.prevent="onDragOverGroup($event, grp.type)"
            @drop.prevent="onDropGroup($event, grp.type)"
          >
            <span class="caret">{{ grpCollapsed[grp.type] ? "▸" : "▾" }}</span>
            <span class="grp-label">{{ grp.label }}</span>
            <span class="grp-count">{{ compCountByType(grp.type) }}</span>
            <a-tooltip v-if="userStore.hasPermission('component:write')" content="新建文件夹">
              <span class="grp-action" @click.stop="startNewFolder(grp.type, null)">⊞</span>
            </a-tooltip>
            <a-tooltip v-if="userStore.hasPermission('component:write')" content="新建组件">
              <span class="grp-action" @click.stop="newBlankTab(grp.type as Language)">＋</span>
            </a-tooltip>
          </div>

          <!-- 展开后的树节点（搜索时强制展开）-->
          <template v-if="searchKw || !grpCollapsed[grp.type]">
            <template v-for="node in flatTree(grp.type)" :key="node.nodeKey">
              <!-- 文件夹行 -->
              <div
                v-if="node.kind === 'folder'"
                :class="[
                  'tree-node folder-node',
                  { 'dragging': dragState.draggingId === node.id, 'drop-target': dragState.dropTargetId === node.id && dragState.dropKind === 'folder' }
                ]"
                :style="{ paddingLeft: `${14 + node.depth * 16}px` }"
                :draggable="renamingFolderId !== node.id"
                @contextmenu.prevent="showFolderContextMenu($event, node)"
                @dragstart="onDragStart($event, node)"
                @dragend="onDragEnd()"
                @dragover.prevent="onDragOver($event, node)"
                @drop.prevent="onDrop($event, node)"
              >
                <span class="node-toggle" @click="toggleFolder(node.id)">
                  <span v-if="!folderCollapsed[node.id]" class="caret">▾</span>
                  <span v-else class="caret">▸</span>
                </span>
                <span class="folder-icon">📁</span>
                <span v-if="renamingFolderId !== node.id" class="node-name" @dblclick="startRename(node)">
                  {{ node.name }}
                </span>
                <a-input
                  v-else
                  v-model="renameValue"
                  size="mini"
                  class="rename-input"
                  @blur="submitRename(node.id)"
                  @keyup.enter="submitRename(node.id)"
                  @keyup.escape="renamingFolderId = null"
                  @dragstart.stop.prevent
                  ref="renameInputRef"
                />
                <span class="node-actions">
                  <a-tooltip v-if="userStore.hasPermission('component:write') && node.depth < 3" content="新建子文件夹">
                    <span class="node-action" @click.stop="startNewFolder(node.folderType, node.id)">⊞</span>
                  </a-tooltip>
                  <a-tooltip v-if="userStore.hasPermission('component:write')" content="新建组件">
                    <span class="node-action" @click.stop="newBlankTab(node.folderType as Language, node.id)">＋</span>
                  </a-tooltip>
                  <a-tooltip v-if="userStore.hasPermission('component:write')" content="删除文件夹">
                    <span class="node-action danger" @click.stop="deleteFolder(node.id)">×</span>
                  </a-tooltip>
                </span>
              </div>

              <!-- 组件行 -->
              <div
                v-else
                :class="[
                  'tree-node comp-node',
                  {
                    'comp-open': isTabActive(node.id),
                    'dragging': dragState.draggingId === node.id,
                    'drop-target': dragState.dropTargetId === node.id && dragState.dropKind === 'component',
                    'drop-before': dragState.dropTargetId === node.id && dragState.dropPosition === 'before',
                    'drop-after': dragState.dropTargetId === node.id && dragState.dropPosition === 'after'
                  }
                ]"
                :style="{ paddingLeft: `${14 + node.depth * 16}px` }"
                :draggable="renamingCompId !== node.id"
                @click="openComp(node.data)"
                @contextmenu.prevent="showCompContextMenu($event, node)"
                @dragstart="onDragStart($event, node)"
                @dragend="onDragEnd()"
                @dragover.prevent="onDragOver($event, node)"
                @drop.prevent="onDrop($event, node)"
              >
                <LangIcon :type="node.data.type" :size="18" />
                <span v-if="renamingCompId !== node.id" class="node-name">{{ node.name }}</span>
                <a-input
                  v-else
                  v-model="renameCompValue"
                  size="mini"
                  class="rename-input"
                  @blur="submitRenameComp(node.id)"
                  @keyup.enter="submitRenameComp(node.id)"
                  @keyup.escape="renamingCompId = null"
                  @dragstart.stop.prevent
                  ref="renameCompInputRef"
                />
                <a-tooltip :content="statusLabel(node.data.status)" position="right">
                  <span
                    class="status-dot-only"
                    :style="{ background: statusColor(node.data.status) }"
                  ></span>
                </a-tooltip>
              </div>
            </template>
          </template>
        </template>
      </div>
    </div>

    <!-- 右侧编辑区 / 管理面板 -->
    <div class="ide-main">
      <!-- 管理视图 -->
      <CompManagePanel
        v-if="viewMode === 'manage'"
        ref="managePanelRef"
        @open="onManageOpen"
        @refresh="loadComponents"
      />

      <!-- IDE 视图 -->
      <template v-else-if="tabs.length === 0">
        <div class="ide-empty">
          <div class="empty-hint">从左侧选择组件，或新建</div>
          <a-button type="outline" size="small" @click="newBlankTab('sql')">
            <template #icon><icon-plus /></template>
            新建 SQL
          </a-button>
        </div>
      </template>

      <template v-else>
        <!-- 标签栏 -->
        <div class="tab-bar">
          <div class="tabs-scroll">
            <div
              v-for="tab in tabs"
              :key="tab.key"
              :class="['tab-item', { active: activeKey === tab.key }]"
              @click="switchTab(tab.key)"
            >
              <LangIcon :type="tab.language" :size="16" />
              <span class="tab-name">{{ tab.dirty ? '● ' : '' }}{{ tab.name }}</span>
              <span class="tab-close" @click.stop="closeTab(tab.key)">×</span>
            </div>
          </div>
          <a-dropdown trigger="click">
            <a-button type="text" size="mini" class="add-tab-btn"><icon-plus /></a-button>
            <template #content>
              <a-doption @click="newBlankTab('sql')">新建 SQL</a-doption>
              <a-doption @click="newBlankTab('python')">新建 Python</a-doption>
              <a-doption @click="newBlankTab('shell')">新建 Shell</a-doption>
              <a-doption @click="newBlankTab('datax')">新建 DataX 同步</a-doption>
            </template>
          </a-dropdown>
        </div>

        <!-- DataX 编辑器 -->
        <template v-if="activeTab && activeTab.language === 'datax'">
          <DataXEditor
            :comp-id="activeTab.componentId ?? null"
            @saved="onDataXSaved"
            @status-changed="loadComponents"
            style="flex: 1; overflow: hidden;"
          />
        </template>

        <!-- 代码编辑器（非 datax tab） -->
        <template v-else-if="activeTab">
          <!-- 工具栏 -->
          <div class="ide-toolbar">
            <a-select
              v-if="activeTab.language === 'sql'"
              v-model="activeTab.datasourceId"
              size="small"
              placeholder="选择数据源"
              style="width: 200px"
            >
              <a-option v-for="ds in datasources" :key="ds.id" :value="ds.id">{{ ds.name }}</a-option>
            </a-select>
            <div style="flex:1" />
            <a-space size="small">
              <a-tag v-if="activeTab.readOnly" color="orange" size="small">🔒 只读（{{ activeTab.lockedBy }} 编辑中）</a-tag>
              <a-button size="small" :type="showParams ? 'primary' : 'secondary'" @click="showParams = !showParams">
                <template #icon><icon-settings /></template>
                参数
              </a-button>
              <a-button size="small" @click="openDqcModal">
                <template #icon>
                  <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
                </template>
                质量 {{ activeTab?.dqcRuleIds?.length ? `(${activeTab.dqcRuleIds.length})` : '' }}
              </a-button>
              <a-button v-if="userStore.hasPermission('component:write')" size="small" type="primary" :loading="running" :disabled="activeTab.readOnly" @click="runCode">
                <template #icon><icon-play-arrow /></template>
                运行
              </a-button>
              <a-button v-if="userStore.hasPermission('component:write')" size="small" :loading="saving" :disabled="activeTab.readOnly" @click="saveTab">
                <template #icon><icon-save /></template>
                保存
              </a-button>
              <a-button v-if="activeTab.componentId && userStore.hasPermission('component:publish')" size="small" :disabled="activeTab.readOnly" @click="quickPublish">
                <template #icon><icon-upload /></template>
                发布
              </a-button>
              <a-button v-if="activeTab.componentId" size="small" @click="openHistory">
                <template #icon><icon-history /></template>
                历史版本
              </a-button>
            </a-space>
          </div>

          <!-- 参数面板 -->
          <ParamEditor
            v-if="showParams"
            v-model="activeTab.params"
            @update:model-value="activeTab.dirty = true"
          />

          <!-- 编辑器 -->
          <div class="editor-area">
            <CodeEditor
              :key="activeKey"
              :model-value="activeTab ? activeTab.code : ''"
              :language="activeTab ? activeTab.language : 'sql'"
              :datasource-id="activeTab?.datasourceId"
              ref="editorRef"
              height="100%"
              @update:model-value="onCodeChange"
            />
          </div>

          <!-- 结果面板 -->
          <div v-if="result !== null || running" class="result-panel">
            <div class="result-header">
              <span class="result-info">
                <template v-if="running">运行中...</template>
                <template v-else-if="result">
                  <span v-if="result.type === 'table'" class="ok-text">
                    ✓ 共查询到 {{ result.row_count }} 行{{ result.row_count >= 2000 ? '（已达上限，仅展示前 2000 行）' : '' }} · {{ result.duration_ms }}ms
                  </span>
                  <span v-else-if="result.type === 'rowcount'" class="ok-text">✓ 影响 {{ result.affected }} 行 · {{ result.duration_ms }}ms</span>
                  <span v-else-if="result.type === 'log'" :class="result.ok ? 'ok-text' : 'err-text'">
                    {{ result.ok ? '✓' : '✗' }} exit {{ result.exit_code }} · {{ result.duration_ms }}ms
                  </span>
                  <span v-else-if="result.error" class="err-text">✗ {{ result.error }}</span>
                </template>
              </span>
              <a-button type="text" size="mini" @click="result = null">关闭</a-button>
            </div>
            <div class="result-body">
              <div v-if="running" class="result-spin"><a-spin /></div>
              <template v-else-if="result">
                <a-table
                  v-if="result.type === 'table'"
                  :columns="result.columns.map((c: string) => ({ title: c, dataIndex: c, ellipsis: true, width: 120 }))"
                  :data="result.rows"
                  :pagination="{ pageSize: 50, showTotal: true, size: 'mini' }"
                  size="mini"
                  :scroll="{ x: 'max-content' }"
                  class="result-table"
                />
                <div v-else-if="result.type === 'rowcount'" class="result-text ok-text">
                  执行成功，影响 {{ result.affected }} 行
                </div>
                <pre v-else-if="result.type === 'log'" :class="['result-log', result.ok ? 'log-ok' : 'log-err']">{{ result.log }}</pre>
                <div v-else-if="result.error" class="result-text err-text">{{ result.error }}</div>
              </template>
            </div>
          </div>
        </template>
      </template>
    </div><!-- /ide-main -->
    </div><!-- /ide-body -->

    <!-- 首次保存弹窗 -->
    <a-modal v-model:visible="saveModalVisible" title="保存组件" @ok="confirmSave" :ok-loading="saving" width="380px">
      <a-form-item label="组件名称">
        <a-input v-model="saveName" placeholder="如：dim_user_query" allow-clear />
      </a-form-item>
    </a-modal>

    <!-- 新建文件夹弹窗 -->
    <a-modal v-model:visible="newFolderVisible" title="新建文件夹" @ok="confirmNewFolder" width="360px">
      <a-form-item label="文件夹名称">
        <a-input v-model="newFolderName" placeholder="如：核心指标" allow-clear />
      </a-form-item>
    </a-modal>

    <!-- 全局右键菜单 -->
    <ContextMenu
      v-model:visible="contextMenu.visible"
      :x="contextMenu.x"
      :y="contextMenu.y"
      :items="contextMenu.items"
      @select="onMenuSelect"
    />

    <!-- 执行参数弹窗 -->
    <RunDialog
      v-model:visible="runDialogVisible"
      :params="pendingRunTab?.params || []"
      @run="onRunWithParams"
    />

    <!-- 历史版本弹窗 -->
    <a-modal
      v-model:visible="historyVisible"
      title="历史版本"
      width="580px"
      :footer="false"
    >
      <a-table
        :data="historyList"
        :loading="historyLoading"
        :pagination="false"
        size="small"
      >
        <template #columns>
          <a-table-column title="版本" data-index="version" :width="60" />
          <a-table-column title="状态" data-index="status_label" :width="80" />
          <a-table-column title="时间" data-index="created_at" :width="160" />
          <a-table-column title="备注" data-index="comment" />
          <a-table-column title="操作" :width="140">
            <template #cell="{ record }">
              <a-space size="mini">
                <a-button type="text" size="mini" @click="viewHistoryDetail(record.version)">查看</a-button>
                <a-button type="text" size="mini" status="warning" @click="doRollback(record.version)">回滚</a-button>
              </a-space>
            </template>
          </a-table-column>
        </template>
      </a-table>
    </a-modal>

    <!-- DQC 关联规则弹窗 -->
    <a-modal
      v-model:visible="dqcModalVisible"
      title="数据质量规则"
      width="560px"
      :footer="false"
    >
      <div v-if="!activeTab?.componentId" class="dqc-hint">
        请先保存组件后再关联质量规则
      </div>
      <div v-else>
        <div v-if="dqcRulesLoading" class="dqc-loading"><a-spin /></div>
        <div v-else-if="dqcRules.length === 0" class="dqc-hint">
          暂无关联规则
        </div>
        <div v-else class="dqc-list">
          <div v-for="r in dqcRules" :key="r.id" class="dqc-item">
            <div class="dqc-item-main">
              <span class="dqc-name">{{ r.name }}</span>
              <a-tag v-if="r.is_strong" color="red" size="small">强</a-tag>
              <a-tag v-else color="arcoblue" size="small">弱</a-tag>
            </div>
            <div class="dqc-item-sub">
              {{ r.table_name }}{{ r.column_name ? '.' + r.column_name : '' }} · {{ r.rule_type }} {{ r.operator }} {{ r.threshold }}{{ r.threshold_max ? ' ~ ' + r.threshold_max : '' }}
            </div>
            <a-button type="text" size="mini" status="danger" @click="removeDqcRule(r.id)">移除</a-button>
          </div>
        </div>
        <a-space style="margin-top: 16px;">
          <a-button type="primary" size="small" @click="openDqcSelectModal">
            <template #icon><icon-plus /></template>
            从规则中心选择
          </a-button>
          <a-button size="small" @click="goToNewDqcRule">新建规则</a-button>
        </a-space>
      </div>
    </a-modal>

    <!-- DQC 规则选择弹窗 -->
    <a-modal
      v-model:visible="dqcSelectModalVisible"
      title="选择质量规则"
      width="600px"
      @ok="confirmAddDqcRules"
      @cancel="dqcSelectModalVisible = false"
    >
      <a-table
        v-model:selectedKeys="selectedDqcRuleIds"
        :data="allDqcRules"
        :pagination="{ pageSize: 10 }"
        size="small"
        row-key="id"
        :row-selection="{ type: 'checkbox', showCheckedAll: true }"
      >
        <template #columns>
          <a-table-column title="规则名称" data-index="name" />
          <a-table-column title="表" data-index="table_name" :width="120" />
          <a-table-column title="类型" data-index="rule_type" :width="100" />
          <a-table-column title="级别" :width="80">
            <template #cell="{ record }">
              <a-tag v-if="record.is_strong" color="red" size="small">强</a-tag>
              <a-tag v-else color="arcoblue" size="small">弱</a-tag>
            </template>
          </a-table-column>
        </template>
      </a-table>
    </a-modal>

    <!-- 历史版本详情弹窗 -->
    <a-modal
      v-model:visible="historyDetailVisible"
      :title="`版本 ${historyDetail?.version} 详情`"
      width="640px"
      :footer="false"
    >
      <div v-if="historyDetail" class="history-detail">
        <a-descriptions :column="2" size="small" bordered>
          <a-descriptions-item label="版本">{{ historyDetail.version }}</a-descriptions-item>
          <a-descriptions-item label="状态">{{ historyDetail.status }}</a-descriptions-item>
          <a-descriptions-item label="时间">{{ historyDetail.created_at }}</a-descriptions-item>
          <a-descriptions-item label="备注">{{ historyDetail.comment || '-' }}</a-descriptions-item>
        </a-descriptions>
        <div class="history-code-label">代码 / 配置</div>
        <pre class="history-code">{{ historyDetail.code }}</pre>
        <div v-if="historyDetail.params?.length" class="history-code-label">参数</div>
        <pre v-if="historyDetail.params?.length" class="history-code">{{ JSON.stringify(historyDetail.params, null, 2) }}</pre>
      </div>
    </a-modal>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import LangIcon from '../components/LangIcon.vue'
import { Message } from '@arco-design/web-vue'
import {
  IconPlus, IconSearch, IconDown, IconRight, IconPlayArrow, IconSave, IconUpload,
  IconFolder, IconDelete, IconFolderAdd, IconFile, IconCode, IconList, IconSettings, IconHistory,
} from '@arco-design/web-vue/es/icon'
import CodeEditor from '../components/CodeEditor.vue'
import ContextMenu from '../components/ContextMenu.vue'
import type { MenuItem } from '../components/ContextMenu.vue'
import {
  getComponents, getComponent, createComponent, updateComponent, deleteComponent,
  getDatasources, runSqlAdhoc, runComponentScript, quickPublishComponent,
  getComponentFolders, createComponentFolder, renameComponentFolder, deleteComponentFolder,
  moveComponent, reorderComponents, moveComponentFolder,
  getProjects,
  getComponentHistory, getComponentHistoryDetail, rollbackComponent,
  acquireComponentLock, releaseComponentLock, heartbeatComponentLock,
  getDqcRules, deleteDqcRule,
} from '../api'
import DataXEditor from '../components/DataXEditor.vue'
import CompManagePanel from '../components/CompManagePanel.vue'
import { useUserStore } from '../stores/user'
import type { ComponentItem, DatasourceItem, FolderItem, ProjectItem, ComponentStatus, ComponentParam } from '../types/component'
import { statusLabel, statusColor } from '../types/component'
import ParamEditor from '../components/ParamEditor.vue'
import RunDialog from '../components/RunDialog.vue'

const userStore = useUserStore()

type Language = 'sql' | 'python' | 'shell' | 'datax'

interface Tab {
  key: string
  name: string
  code: string
  language: Language
  componentId?: number
  folderId?: number | null
  datasourceId?: number
  params: ComponentParam[]
  dqcRuleIds: number[]
  dirty: boolean
  lockedBy?: string
  readOnly?: boolean
}

const typeGroups = [
  { type: 'sql',    label: 'SQL 查询' },
  { type: 'python', label: 'Python 脚本' },
  { type: 'shell',  label: 'Shell 脚本' },
  { type: 'datax',  label: 'DataX 同步' },
]

const viewMode = ref<'ide' | 'manage'>('ide')
const managePanelRef = ref<any>(null)


const tabs = ref<Tab[]>([])
const activeKey = ref('')
const activeTab = computed<Tab | null>(() => tabs.value.find(t => t.key === activeKey.value) ?? null)

const components = ref<ComponentItem[]>([])
const datasources = ref<DatasourceItem[]>([])
const folders = ref<FolderItem[]>([])  // flat list from API
const projects = ref<ProjectItem[]>([])
const searchKw = ref('')

const grpCollapsed = reactive<Record<string, boolean>>({ sql: false, python: false, shell: false, datax: false })
const folderCollapsed = reactive<Record<number, boolean>>({})

const editorRef = ref<any>(null)
const running = ref(false)
const saving = ref(false)
const result = ref<any>(null)
const showParams = ref(false)
const runDialogVisible = ref(false)
const pendingRunTab = ref<Tab | null>(null)

const saveModalVisible = ref(false)
const saveName = ref('')
const pendingSaveTab = ref<Tab | null>(null)

const historyVisible = ref(false)
const historyList = ref<any[]>([])
const historyLoading = ref(false)
const historyDetailVisible = ref(false)
const historyDetail = ref<any>(null)

const dqcModalVisible = ref(false)
const dqcRules = ref<any[]>([])
const dqcRulesLoading = ref(false)
const dqcSelectModalVisible = ref(false)
const allDqcRules = ref<any[]>([])
const selectedDqcRuleIds = ref<number[]>([])

const lockHeartbeatTimer = ref<ReturnType<typeof setInterval> | null>(null)

const newFolderVisible = ref(false)
const newFolderName = ref('')
const newFolderContext = ref<{ type: string; parentId: number | null } | null>(null)

const renamingFolderId = ref<number | null>(null)
const renameValue = ref('')
const renameInputRef = ref<any>(null)

// ---- 右键菜单 ----
const contextMenu = reactive({
  visible: false,
  x: 0,
  y: 0,
  items: [] as MenuItem[],
})

// ---- 剪贴板 ----
const clipboard = ref<{ kind: 'component' | 'folder'; action: 'copy' | 'cut'; id: number; type?: string; folderType?: string } | null>(null)

// ---- 拖拽 ----
const dragState = reactive({
  draggingId: null as number | null,
  dragKind: null as 'component' | 'folder' | null,
  dragFolderType: null as string | null,
  dragFolderId: null as number | null,
  dropTargetId: null as number | string | null,
  dropKind: null as 'component' | 'folder' | 'group' | null,
  dropPosition: null as 'before' | 'after' | 'inside' | null,
})

let tabSeq = 0
function genKey() { return `tab-${++tabSeq}` }

function compCountByType(type: string) {
  return components.value.filter(c => c.type === type).length
}

// ---- 树结构 ----
interface FolderTreeNode {
  nodeKey: string
  kind: 'folder'
  id: number
  name: string
  depth: number
  folderType: string
  data: FolderItem
}
interface CompTreeNode {
  nodeKey: string
  kind: 'component'
  id: number
  name: string
  depth: number
  folderType: string
  data: ComponentItem
}
type TreeNode = FolderTreeNode | CompTreeNode

function flatTree(type: string): TreeNode[] {
  const kw = searchKw.value.toLowerCase()
  const searching = !!kw
  const typeFolders = folders.value.filter(f => f.type === type)
  const validFolderIds = new Set(typeFolders.map(f => f.id))
  const typeComps = components.value.filter(c => {
    if (c.type !== type) return false
    if (kw && !c.name.toLowerCase().includes(kw)) return false
    return true
  })

  // 搜索时：递归判断文件夹是否包含匹配项（直接子组件 / 后代组件）
  function folderHasMatch(folderId: number): boolean {
    if (typeComps.some(c => c.folder_id === folderId)) return true
    const subFolders = typeFolders.filter(f => f.parent_id === folderId)
    return subFolders.some(sub => folderHasMatch(sub.id))
  }

  const result: TreeNode[] = []

  function traverse(parentId: number | null, depth: number) {
    // Child folders
    const childFolders = typeFolders
      .filter(f => (f.parent_id ?? null) === parentId)
      .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0) || a.id - b.id)
    for (const f of childFolders) {
      // 搜索时只显示有匹配项的文件夹
      if (searching && !folderHasMatch(f.id)) continue
      result.push({ nodeKey: `f-${f.id}`, kind: 'folder', id: f.id, name: f.name, depth, folderType: type, data: f })
      // 搜索时强制展开；否则按用户折叠状态
      if (searching || !folderCollapsed[f.id]) {
        traverse(f.id, depth + 1)
      }
    }
    // Child components (orphaned components with invalid folder_id treated as root)
    const childComps = typeComps.filter(c => {
      const fid = c.folder_id ?? null
      if (parentId === null) {
        return fid === null || !validFolderIds.has(fid)
      }
      return fid === parentId
    })
    childComps.sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0) || b.id - a.id)
    for (const c of childComps) {
      result.push({ nodeKey: `c-${c.id}`, kind: 'component', id: c.id, name: c.name, depth, folderType: type, data: c })
    }
  }

  traverse(null, 0)
  return result
}

function toggleGrp(type: string) { grpCollapsed[type] = !grpCollapsed[type] }
function toggleFolder(id: number) { folderCollapsed[id] = !folderCollapsed[id] }

function isTabOpen(compId: number) {
  return tabs.value.some(t => t.componentId === compId)
}
function isTabActive(compId: number) {
  return activeTab.value?.componentId === compId
}

async function openComp(c: ComponentItem) {
  const existing = tabs.value.find(t => t.componentId === c.id)
  if (existing) { switchTab(existing.key); return }
  const key = genKey()
  const cfg = c.config_json || {}
  const code = cfg.sql || cfg.script || cfg.rawJson || c.code || ''
  const tab: Tab = {
    key,
    name: c.name,
    code,
    language: c.type as Language,
    componentId: c.id,
    folderId: c.folder_id ?? null,
    params: (c.params || []) as ComponentParam[],
    dqcRuleIds: c.dqc_rule_ids || [],
    datasourceId: (() => {
      const rawId = cfg.datasource_id || c.datasource_id || undefined
      if (rawId == null) return undefined
      const validIds = new Set(datasources.value.map((d) => d.id))
      return validIds.has(rawId) ? rawId : undefined
    })(),
    dirty: false,
  }
  tabs.value.push(tab)
  switchTab(key)
  // 尝试获取编辑锁
  if (c.id && userStore.hasPermission('component:write')) {
    try {
      const res: any = await acquireComponentLock(c.id)
      if (!res.locked) {
        tab.lockedBy = res.by || '其他用户'
        tab.readOnly = true
        Message.warning(`组件正被 ${tab.lockedBy} 编辑，当前为只读模式`)
      }
    } catch (e: any) { console.error(e) }
  }
}

function newBlankTab(lang: Language = 'sql', folderId?: number | null) {
  const key = genKey()
  const names: Record<string, string> = { sql: 'Untitled SQL', python: 'Untitled Python', shell: 'Untitled Shell', datax: 'Untitled DataX' }
  tabs.value.push({ key, name: names[lang] ?? 'Untitled', code: '', language: lang, folderId: folderId ?? null, params: [], dqcRuleIds: [], dirty: false })
  switchTab(key)
}

function switchTab(key: string) {
  activeKey.value = key
  result.value = null
  // 清理旧心跳
  if (lockHeartbeatTimer.value) {
    clearInterval(lockHeartbeatTimer.value)
    lockHeartbeatTimer.value = null
  }
  // 为新标签页启动心跳
  const tab = tabs.value.find(t => t.key === key)
  if (tab?.componentId && !tab.readOnly) {
    lockHeartbeatTimer.value = setInterval(() => {
      heartbeatComponentLock(tab.componentId!).catch((e: any) => console.error(e))
    }, 45000)
  }
}

async function closeTab(key: string) {
  const idx = tabs.value.findIndex(t => t.key === key)
  if (idx === -1) return
  const tab = tabs.value[idx]
  // 释放编辑锁
  if (tab.componentId && !tab.readOnly) {
    try { await releaseComponentLock(tab.componentId) } catch (e: any) { console.error(e); Message.error((e as any).message || '操作失败') }
  }
  tabs.value.splice(idx, 1)
  if (activeKey.value === key) {
    const nextKey = tabs.value[Math.max(0, idx - 1)]?.key ?? ''
    activeKey.value = nextKey
    // 如果切到新标签页，switchTab 会处理心跳
    if (nextKey) switchTab(nextKey)
  }
  result.value = null
}

function onCodeChange(v: string) {
  const tab = activeTab.value
  if (tab) { tab.code = v; tab.dirty = true }
}

// ---- 文件夹操作 ----
function startNewFolder(type: string, parentId: number | null) {
  newFolderContext.value = { type, parentId }
  newFolderName.value = ''
  newFolderVisible.value = true
}

async function confirmNewFolder() {
  if (!newFolderName.value.trim()) { Message.warning('请输入文件夹名称'); return }
  const ctx = newFolderContext.value!
  try {
    await createComponentFolder({
      name: newFolderName.value.trim(),
      type: ctx.type,
      parent_id: ctx.parentId,
    })
    newFolderVisible.value = false
    await loadFolders()
  } catch (e: any) { console.error(e) }
}

function startRename(node: TreeNode) {
  renamingFolderId.value = node.id
  renameValue.value = node.name
  nextTick(() => {
    const el = renameInputRef.value
    if (Array.isArray(el)) el[0]?.focus?.()
    else el?.focus?.()
  })
}

async function submitRename(id: number) {
  if (!renameValue.value.trim()) { renamingFolderId.value = null; return }
  try {
    await renameComponentFolder(id, renameValue.value.trim())
    await loadFolders()
  } catch (e: any) { console.error(e); Message.error((e as any).message || '操作失败') } finally {
    renamingFolderId.value = null
  }
}

async function deleteFolder(id: number) {
  try {
    await deleteComponentFolder(id)
    await loadFolders()
    Message.success('文件夹已删除')
  } catch (e: any) { console.error(e) }
}

// ---- 状态系统 ----
function hexToRgba(hex: string, alpha: number): string {
  const h = hex.replace('#', '')
  const r = parseInt(h.substring(0, 2), 16)
  const g = parseInt(h.substring(2, 4), 16)
  const b = parseInt(h.substring(4, 6), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}
function statusTagStyle(s: string) {
  const color = statusColor(s)
  return {
    background: hexToRgba(color, 0.12),
    color: color,
  }
}

async function confirmDeleteComp(c: ComponentItem) {
  if (!confirm(`确定删除组件「${c.name}」？此操作不可恢复`)) return
  try {
    // 后端 delete_component 对所有类型均已处理级联删除（包括 datax 的 SyncTask + Workflow）
    await deleteComponent(c.id)
    Message.success('已删除')
    const idx = tabs.value.findIndex(t => t.componentId === c.id)
    if (idx >= 0) closeTab(tabs.value[idx].key)
    await loadComponents()
  } catch (e: any) { console.error(e) }
}

// ---- 运行 ----
async function runCode() {
  const tab = activeTab.value
  if (!tab) return
  if (tab.language === 'sql' && !tab.datasourceId) { Message.warning('请先选择数据源'); return }

  // 有参数时弹出参数覆盖弹窗
  if ((tab.params || []).length > 0) {
    pendingRunTab.value = tab
    runDialogVisible.value = true
    return
  }
  await doRun(tab)
}

async function onRunWithParams(runtimeParams: Record<string, string>) {
  const tab = pendingRunTab.value
  if (!tab) return
  await doRun(tab, runtimeParams)
  pendingRunTab.value = null
}

async function doRun(tab: Tab, runtimeParams?: Record<string, string>) {
  // Convert list-of-lists rows to list-of-objects for a-table
  function normalizeResult(res: any): any {
    if (res?.type === 'table' && Array.isArray(res.rows) && Array.isArray(res.columns)) {
      const cols: string[] = res.columns
      res.rows = res.rows.map((row: any[]) =>
        Array.isArray(row) ? Object.fromEntries(cols.map((c, i) => [c, row[i]])) : row
      )
    }
    return res
  }

  result.value = null
  running.value = true
  try {
    if (tab.language === 'sql') {
      const sel: string = editorRef.value?.getSelectedText?.() ?? ''
      const sql = (sel || tab.code).trim()
      if (!sql) { Message.warning('请输入 SQL'); return }
      result.value = normalizeResult(await runSqlAdhoc({ datasource_id: tab.datasourceId!, sql }))
    } else {
      if (!tab.componentId) { Message.warning('请先保存后再运行'); return }
      if (tab.dirty) await doSave(tab)
      result.value = normalizeResult(await runComponentScript(tab.componentId!, tab.datasourceId, runtimeParams))
    }
  } catch (e: any) {
    result.value = { error: e?.response?.data?.detail || '执行失败' }
  } finally {
    running.value = false
  }
}

// ---- 保存 ----
async function saveTab() {
  const tab = activeTab.value
  if (!tab) return
  if (tab.readOnly) { Message.warning('当前组件为只读模式，无法保存'); return }
  if (!tab.componentId) {
    // 弹窗已打开时不覆盖，避免丢失正在命名的另一个标签
    if (saveModalVisible.value) {
      Message.warning('请先完成当前保存操作')
      return
    }
    pendingSaveTab.value = tab
    saveName.value = tab.name.startsWith('Untitled') ? '' : tab.name
    saveModalVisible.value = true
    return
  }
  await doSave(tab)
}

async function confirmSave() {
  if (!saveName.value.trim()) { Message.warning('请输入组件名称'); return }
  const tab = pendingSaveTab.value
  if (!tab) return
  tab.name = saveName.value.trim()
  await doSave(tab)
  saveModalVisible.value = false
  pendingSaveTab.value = null
}

async function onDataXSaved(comp: any) {
  await loadComponents()
  const tab = activeTab.value
  if (tab && tab.language === 'datax') {
    tab.componentId = comp.id
    tab.name = comp.name
    tab.dirty = false
  }
}

async function doSave(tab: Tab) {
  saving.value = true
  try {
    // 构造 config_json
    const langKey = tab.language === 'sql' ? 'sql' : 'script'
    const config_json: any = { [langKey]: tab.code }
    if (tab.datasourceId != null) config_json.datasource_id = tab.datasourceId

    const payload: any = {
      name: tab.name,
      type: tab.language,
      config_json,
      params: tab.params || [],
      folder_id: tab.folderId ?? null,
      dqc_rule_ids: tab.dqcRuleIds || [],
    }
    if (tab.componentId) {
      await updateComponent(tab.componentId, payload)
    } else {
      const res: any = await createComponent(payload)
      tab.componentId = res.id
    }
    tab.dirty = false
    Message.success('已保存')
    await loadComponents()
  } catch (e: any) { console.error(e) } finally {
    saving.value = false
  }
}

async function quickPublish() {
  const tab = activeTab.value
  if (!tab?.componentId) return
  if (tab.dirty) await doSave(tab)
  try {
    await quickPublishComponent(tab.componentId!)
    Message.success('已发布上线')
    await loadComponents()
  } catch (e: any) { console.error(e) }
}

// ---- 历史版本 ----
async function openHistory() {
  const tab = activeTab.value
  if (!tab?.componentId) {
    Message.warning('请先保存组件')
    return
  }
  historyVisible.value = true
  historyLoading.value = true
  try {
    const res: any = await getComponentHistory(tab.componentId)
    historyList.value = res.items || []
  } catch {
    historyList.value = []
  } finally {
    historyLoading.value = false
  }
}

async function viewHistoryDetail(version: number) {
  const tab = activeTab.value
  if (!tab?.componentId) return
  try {
    const res: any = await getComponentHistoryDetail(tab.componentId, version)
    const cfg = res.config_json || {}
    historyDetail.value = {
      ...res,
      code: cfg.sql || cfg.script || JSON.stringify(cfg, null, 2),
    }
    historyDetailVisible.value = true
  } catch (e: any) { console.error(e) }
}

async function doRollback(version: number) {
  const tab = activeTab.value
  if (!tab?.componentId) return
  try {
    await rollbackComponent(tab.componentId, version)
    Message.success(`已回滚到版本 ${version}`)
    historyVisible.value = false
    // 刷新当前 tab 数据
    const res: any = await getComponent(tab.componentId)
    tab.name = res.name
    tab.code = res.code
    tab.datasourceId = res.datasource_id
    tab.params = res.params || []
    tab.dqcRuleIds = res.dqc_rule_ids || []
    tab.dirty = false
  } catch (e: any) { console.error(e) }
}

// ---- 数据加载 ----
async function loadFolders() {
  try {
    const res: any = await getComponentFolders()
    folders.value = res || []
  } catch (e: any) { console.error(e) }
}

async function loadComponents() {
  try {
    const res: any = await getComponents({ page_size: 500 })
    components.value = res.items || []
  } catch (e: any) { console.error(e) }
}

async function loadDatasources() {
  try {
    const res: any = await getDatasources({ page_size: 100 })
    datasources.value = res.items || []
    // Clear stale datasourceId on any open tabs
    const validIds = new Set(datasources.value.map((d) => d.id))
    tabs.value.forEach(t => {
      if (t.datasourceId != null && !validIds.has(t.datasourceId)) {
        t.datasourceId = undefined
      }
    })
  } catch (e: any) { console.error(e) }
}

async function loadProjects() {
  try {
    const res: any = await getProjects({ page_size: 200 })
    projects.value = res.items || res || []
  } catch (e: any) { console.error(e) }
}

// ---- 右键菜单 ----
function typeLabel(type: string): string {
  const map: Record<string, string> = { sql: 'SQL 查询', python: 'Python 脚本', shell: 'Shell 脚本', datax: 'DataX 同步' }
  return map[type] || type
}

function buildCompMenuItems(node: TreeNode): MenuItem[] {
  if (node.kind !== 'component') return []
  const c = node.data
  const t = c.type as string
  const items: MenuItem[] = []

  items.push({ key: 'open', label: '打开' })
  if (t !== 'datax') {
    items.push({ key: 'run', label: '运行' })
  }
  items.push({ divider: true })
  items.push({ key: `new-${t}`, label: `新建${typeLabel(t)}` })
  items.push({ key: 'copy', label: '复制' })
  items.push({ key: 'cut', label: '剪切' })
  if (clipboard.value && clipboard.value.kind === 'component') {
    items.push({ key: 'paste', label: '粘贴' })
  }
  items.push({ divider: true })
  items.push({ key: 'rename', label: '重命名' })
  items.push({
    key: 'move',
    label: '移动到其他文件夹',
    children: buildMoveToFolderMenu(t, 'move-to'),
  })
  items.push({ divider: true })
  items.push({ key: 'delete', label: '删除', danger: true })
  return items
}

function buildFolderMenuItems(node: TreeNode): MenuItem[] {
  const items: MenuItem[] = []
  const collapsed = folderCollapsed[node.id]
  const t = node.folderType
  items.push({ key: collapsed ? 'expand' : 'collapse', label: collapsed ? '展开' : '折叠' })
  items.push({ divider: true })
  if (node.depth < 3) {
    items.push({ key: 'new-subfolder', label: '新建子文件夹' })
  }
  items.push({ key: `new-${t}`, label: `新建${typeLabel(t)}` })
  items.push({ divider: true })
  items.push({ key: 'rename', label: '重命名' })
  items.push({ key: 'cut', label: '剪切' })
  if (clipboard.value && clipboard.value.kind === 'folder') {
    items.push({ key: 'paste', label: '粘贴' })
  }
  items.push({ divider: true })
  items.push({ key: 'delete', label: '删除', danger: true })
  return items
}

function buildMoveToFolderMenu(type: string, prefix: string): MenuItem[] {
  const typeFolders = folders.value.filter(f => f.type === type)
  const roots = typeFolders.filter(f => f.parent_id == null)
  function buildSub(foldersList: FolderItem[]): MenuItem[] {
    return foldersList.map(f => {
      const children = typeFolders.filter(child => child.parent_id === f.id)
      const item: MenuItem = { key: `${prefix}-${f.id}`, label: f.name }
      if (children.length > 0) {
        item.children = buildSub(children)
      }
      return item
    })
  }
  const menu = buildSub(roots)
  // 添加"无文件夹"选项
  menu.unshift({ key: `${prefix}-0`, label: '（无文件夹）' })
  return menu
}

async function onMenuSelect(key: string) {
  // 从 contextMenu 的触发源中恢复当前节点 —— 通过最后一个右键事件记录
  const targetNode = lastContextNode.value
  if (!targetNode) return

  if (key === 'open') {
    if (targetNode.kind === 'component') openComp(targetNode.data)
  } else if (key === 'run') {
    if (targetNode.kind === 'component') {
      openComp(targetNode.data)
      await nextTick()
      runCode()
    }
  } else if (key === 'expand') {
    folderCollapsed[targetNode.id] = false
  } else if (key === 'collapse') {
    folderCollapsed[targetNode.id] = true
  } else if (key === 'copy') {
    if (targetNode.kind === 'component') {
      clipboard.value = { kind: 'component', action: 'copy', id: targetNode.id, type: targetNode.data.type }
    }
  } else if (key === 'cut') {
    if (targetNode.kind === 'component') {
      clipboard.value = { kind: 'component', action: 'cut', id: targetNode.id, type: targetNode.data.type }
    } else if (targetNode.kind === 'folder') {
      clipboard.value = { kind: 'folder', action: 'cut', id: targetNode.id, folderType: targetNode.folderType }
    }
  } else if (key === 'paste') {
    await doPaste(targetNode)
  } else if (key === 'rename') {
    if (targetNode.kind === 'folder') startRename(targetNode)
    else if (targetNode.kind === 'component') startRenameComponent(targetNode)
  } else if (key === 'delete') {
    if (targetNode.kind === 'component') await confirmDeleteComp(targetNode.data)
    else if (targetNode.kind === 'folder') await deleteFolder(targetNode.id)
  } else if (key === 'new-subfolder') {
    if (targetNode.kind === 'folder') startNewFolder(targetNode.folderType, targetNode.id)
  } else if (key.startsWith('move-to-')) {
    const folderId = parseInt(key.replace('move-to-', ''), 10)
    if (targetNode.kind === 'component') await doMoveComponent(targetNode.data.id, folderId)
  } else if (key.startsWith('new-')) {
    const lang = key.replace('new-', '') as Language
    const folderId = targetNode.kind === 'folder' ? targetNode.id : targetNode.data.folder_id ?? null
    newBlankTab(lang, folderId)
  }
}

const lastContextNode = ref<TreeNode | null>(null)

function showCompContextMenu(e: MouseEvent, node: TreeNode) {
  lastContextNode.value = node
  contextMenu.x = e.clientX
  contextMenu.y = e.clientY
  contextMenu.items = buildCompMenuItems(node)
  contextMenu.visible = true
}

function showFolderContextMenu(e: MouseEvent, node: TreeNode) {
  lastContextNode.value = node
  contextMenu.x = e.clientX
  contextMenu.y = e.clientY
  contextMenu.items = buildFolderMenuItems(node)
  contextMenu.visible = true
}

// ---- 剪贴板操作 ----
async function doPaste(targetNode: TreeNode) {
  const cb = clipboard.value
  if (!cb) return
  if (cb.kind === 'component') {
    const targetFolderId = targetNode.kind === 'folder' ? targetNode.id : targetNode.data.folder_id ?? null
    if (cb.action === 'copy') {
      // 复制：创建新组件
      const src = components.value.find(c => c.id === cb.id)
      if (!src) return
      try {
        const res: any = await createComponent({
          name: src.name + '_copy',
          type: src.type,
          description: src.description,
          config_json: src.config_json || {},
          folder_id: targetFolderId,
        })
        Message.success('已复制')
        await loadComponents()
        openComp(res)
      } catch (e: any) { console.error(e) }
    } else if (cb.action === 'cut') {
      await doMoveComponent(cb.id, targetFolderId ?? 0)
      clipboard.value = null
    }
  } else if (cb.kind === 'folder') {
    if (targetNode.kind !== 'folder') return
    if (cb.action === 'cut') {
      // 防止循环引用：不能把文件夹移动到自身或其子孙
      if (cb.id === targetNode.id || folderContains(cb.id, targetNode.id)) {
        Message.error('不能将文件夹移动到自身或其子文件夹中')
        return
      }
      await doMoveFolder(cb.id, targetNode.id)
      clipboard.value = null
    } else if (cb.action === 'copy') {
      // 复制文件夹：创建同名文件夹（不递归复制内容）
      const src = folders.value.find(f => f.id === cb.id)
      if (!src) return
      try {
        await createComponentFolder({
          name: src.name + '_copy',
          type: src.type,
          parent_id: targetNode.id,
        })
        Message.success('已复制文件夹')
        await loadFolders()
        clipboard.value = null
      } catch (e: any) { console.error(e) }
    }
  }
}

// ---- 组件重命名 ----
const renamingCompId = ref<number | null>(null)
const renameCompValue = ref('')
const renameCompInputRef = ref<any>(null)

function startRenameComponent(node: TreeNode) {
  renamingCompId.value = node.id
  renameCompValue.value = node.name
  nextTick(() => {
    const el = renameCompInputRef.value
    if (Array.isArray(el)) el[0]?.focus?.()
    else el?.focus?.()
  })
}

async function submitRenameComp(id: number) {
  if (!renameCompValue.value.trim()) { renamingCompId.value = null; return }
  try {
    await updateComponent(id, { name: renameCompValue.value.trim() })
    await loadComponents()
    // 更新已打开 tab 的名称
    const tab = tabs.value.find(t => t.componentId === id)
    if (tab) tab.name = renameCompValue.value.trim()
  } catch (e: any) { console.error(e) } finally {
    renamingCompId.value = null
  }
}

// ---- 拖拽 ----
function onDragStart(e: DragEvent, node: TreeNode) {
  dragState.draggingId = node.id
  dragState.dragKind = node.kind
  dragState.dragFolderType = node.folderType
  dragState.dragFolderId = node.kind === 'component' ? node.data.folder_id ?? null : null
  e.dataTransfer!.effectAllowed = 'move'
  e.dataTransfer!.setData('application/json', JSON.stringify({
    id: node.id,
    kind: node.kind,
    folderType: node.folderType,
    type: node.kind === 'component' ? node.data.type : undefined,
    folderId: node.kind === 'component' ? node.data.folder_id : undefined,
  }))
}

/** 检查拖拽文件夹是否包含目标文件夹（防止循环引用） */
function folderContains(parentId: number, childId: number): boolean {
  const children = folders.value.filter(f => f.parent_id === parentId)
  for (const child of children) {
    if (child.id === childId) return true
    if (folderContains(child.id, childId)) return true
  }
  return false
}

function onDragOver(e: DragEvent, targetNode: TreeNode) {
  e.preventDefault()
  // 同节点不处理
  if (dragState.draggingId === targetNode.id) {
    dragState.dropTargetId = null
    dragState.dropKind = null
    dragState.dropPosition = null
    e.dataTransfer!.dropEffect = 'none'
    return
  }

  // 跨类型阻止
  if (dragState.dragFolderType !== targetNode.folderType) {
    dragState.dropTargetId = null
    dragState.dropKind = null
    dragState.dropPosition = null
    e.dataTransfer!.dropEffect = 'none'
    return
  }

  // 文件夹不能拖到组件上
  if (dragState.dragKind === 'folder' && targetNode.kind === 'component') {
    dragState.dropTargetId = null
    dragState.dropKind = null
    dragState.dropPosition = null
    e.dataTransfer!.dropEffect = 'none'
    return
  }

  // 文件夹拖到文件夹：阻止循环引用（不能拖到自身或其子文件夹）
  if (dragState.dragKind === 'folder' && targetNode.kind === 'folder') {
    if (dragState.draggingId! === targetNode.id || folderContains(dragState.draggingId!, targetNode.id)) {
      dragState.dropTargetId = null
      dragState.dropKind = null
      dragState.dropPosition = null
      e.dataTransfer!.dropEffect = 'none'
      return
    }
  }

  e.dataTransfer!.dropEffect = 'move'
  dragState.dropTargetId = targetNode.id
  dragState.dropKind = targetNode.kind

  // 计算插入位置：文件夹 = inside，组件 = 根据鼠标位置判断 before/after
  if (targetNode.kind === 'folder') {
    dragState.dropPosition = 'inside'
  } else {
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
    const midY = rect.top + rect.height / 2
    dragState.dropPosition = e.clientY < midY ? 'before' : 'after'
  }
}

async function onDrop(e: DragEvent, targetNode: TreeNode) {
  e.preventDefault()
  const dataStr = e.dataTransfer!.getData('application/json')
  if (!dataStr) return
  const data = JSON.parse(dataStr)

  // 跨类型忽略
  if (dragState.dragFolderType !== targetNode.folderType) return

  const targetFolderId = targetNode.kind === 'component' ? targetNode.data.folder_id : null
  if (data.kind === 'component' && targetNode.kind === 'folder') {
    // 组件拖到文件夹 = 移动
    await doMoveComponent(data.id, targetNode.id)
  } else if (data.kind === 'component' && targetNode.kind === 'component') {
    // 组件拖到组件
    if (data.folderId === targetFolderId) {
      // 同文件夹 = 排序
      await doReorderBetween(data.id, targetNode.id, (dragState.dropPosition === 'inside' ? 'before' : dragState.dropPosition) ?? 'before')
    } else {
      // 跨文件夹 = 移到目标文件夹（根目录用 0）
      await doMoveComponent(data.id, targetFolderId ?? 0)
      // 等待数据刷新后再排序
      await loadComponents()
      await doReorderBetween(data.id, targetNode.id, (dragState.dropPosition === 'inside' ? 'before' : dragState.dropPosition) ?? 'before')
    }
  } else if (dragState.dragKind === 'folder' && targetNode.kind === 'folder') {
    // 文件夹拖到文件夹 = 嵌套移动
    if (dragState.draggingId! === targetNode.id || folderContains(dragState.draggingId!, targetNode.id)) return
    await doMoveFolder(data.id, targetNode.id)
  }

  dragState.draggingId = null
  dragState.dragKind = null
  dragState.dragFolderType = null
  dragState.dragFolderId = null
  dragState.dropTargetId = null
  dragState.dropKind = null
  dragState.dropPosition = null
}

/** 拖拽经过类型组标题：只允许同类型组件移回根目录 */
function onDragOverGroup(e: DragEvent, groupType: string) {
  e.preventDefault()
  if (dragState.dragFolderType !== groupType) {
    e.dataTransfer!.dropEffect = 'none'
    dragState.dropTargetId = null
    dragState.dropKind = null
    dragState.dropPosition = null
    return
  }
  if (dragState.dragKind === 'folder') {
    e.dataTransfer!.dropEffect = 'none'
    dragState.dropTargetId = null
    dragState.dropKind = null
    dragState.dropPosition = null
    return
  }
  e.dataTransfer!.dropEffect = 'move'
  dragState.dropTargetId = groupType
  dragState.dropKind = 'group'
  dragState.dropPosition = null
}

/** 组件拖到类型组标题 = 移到根目录 */
async function onDropGroup(e: DragEvent, groupType: string) {
  e.preventDefault()
  const dataStr = e.dataTransfer!.getData('application/json')
  if (!dataStr) return
  const data = JSON.parse(dataStr)
  if (dragState.dragFolderType !== groupType) return
  if (data.kind === 'component') {
    await doMoveComponent(data.id, 0)
  }
  dragState.draggingId = null
  dragState.dragKind = null
  dragState.dragFolderType = null
  dragState.dragFolderId = null
  dragState.dropTargetId = null
  dragState.dropKind = null
  dragState.dropPosition = null
}

function onDragEnd() {
  dragState.draggingId = null
  dragState.dragKind = null
  dragState.dragFolderType = null
  dragState.dragFolderId = null
  dragState.dropTargetId = null
  dragState.dropKind = null
  dragState.dropPosition = null
}

async function doMoveComponent(compId: number, folderId: number) {
  try {
    await moveComponent(compId, folderId)
    Message.success('移动成功')
    await loadComponents()
  } catch (e: any) { console.error(e) }
}

async function doReorderBetween(dragId: number, targetId: number, dropPosition: 'before' | 'after' = 'before') {
  // 获取同文件夹的所有组件，重新计算 sort_order
  const dragComp = components.value.find(c => c.id === dragId)
  const targetComp = components.value.find(c => c.id === targetId)
  if (!dragComp || !targetComp) return
  const sameFolder = components.value
    .filter(c => c.folder_id === targetComp.folder_id && c.type === targetComp.type)
    .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0) || b.id - a.id)

  const dragIdx = sameFolder.findIndex(c => c.id === dragId)
  const targetIdx = sameFolder.findIndex(c => c.id === targetId)
  if (dragIdx === -1 || targetIdx === -1) return

  // 移动数组元素，区分 before/after
  const item = sameFolder.splice(dragIdx, 1)[0]
  const insertIdx = dropPosition === 'after'
    ? (dragIdx < targetIdx ? targetIdx : targetIdx + 1)
    : (dragIdx > targetIdx ? targetIdx : targetIdx)
  sameFolder.splice(insertIdx, 0, item)

  // 重新分配 sort_order
  const orders = sameFolder.map((c, i) => ({ id: c.id, sort_order: i * 10 }))
  try {
    await reorderComponents(orders)
    await loadComponents()
  } catch (e: any) { console.error(e) }
}

async function doMoveFolder(folderId: number, parentId: number) {
  try {
    await moveComponentFolder(folderId, parentId)
    Message.success('移动成功')
    await loadFolders()
  } catch (e: any) { console.error(e) }
}

function switchToManage() {
  viewMode.value = 'manage'
  managePanelRef.value?.loadData()
}

function onManageOpen(comp: ComponentItem) {
  viewMode.value = 'ide'
  openComp(comp)
}

// ---- DQC 关联 ----
async function openDqcModal() {
  dqcModalVisible.value = true
  await loadDqcRulesForTab()
}

async function loadDqcRulesForTab() {
  const tab = activeTab.value
  if (!tab?.componentId) return
  dqcRulesLoading.value = true
  try {
    if (tab.dqcRuleIds?.length) {
      const res: any = await getDqcRules()
      const all = res.items || []
      dqcRules.value = all.filter((r: any) => tab.dqcRuleIds.includes(r.id))
    } else {
      dqcRules.value = []
    }
  } catch {
    dqcRules.value = []
  } finally {
    dqcRulesLoading.value = false
  }
}

async function removeDqcRule(ruleId: number) {
  const tab = activeTab.value
  if (!tab) return
  tab.dqcRuleIds = tab.dqcRuleIds.filter((id: number) => id !== ruleId)
  tab.dirty = true
  await loadDqcRulesForTab()
}

async function openDqcSelectModal() {
  dqcSelectModalVisible.value = true
  selectedDqcRuleIds.value = [...(activeTab.value?.dqcRuleIds || [])]
  try {
    const res: any = await getDqcRules()
    // 过滤掉已关联的，避免重复添加（但保留已选的以便取消）
    allDqcRules.value = res.items || []
  } catch {
    allDqcRules.value = []
  }
}

function confirmAddDqcRules() {
  const tab = activeTab.value
  if (!tab) return
  tab.dqcRuleIds = [...selectedDqcRuleIds.value]
  tab.dirty = true
  dqcSelectModalVisible.value = false
  loadDqcRulesForTab()
}

function goToNewDqcRule() {
  const tab = activeTab.value
  if (!tab) return
  // 预填当前组件的数据源和表名（表名从 SQL 中提取是尽力而为）
  const dsId = tab.datasourceId
  const tableGuess = extractTableName(tab.code)
  const query = new URLSearchParams()
  if (dsId) query.set('datasource_id', String(dsId))
  if (tableGuess) query.set('table_name', tableGuess)
  window.open(`/dqc?${query.toString()}`, '_blank')
}

function extractTableName(sql: string): string {
  // 尽力从简单 SELECT / INSERT / CREATE TABLE 中提取表名
  const m = sql.match(/\bfrom\s+[`"']?(\w+)[`"']?/i) ||
            sql.match(/\binto\s+[`"']?(\w+)[`"']?/i) ||
            sql.match(/\bjoin\s+[`"']?(\w+)[`"']?/i)
  return m?.[1] || ''
}

onMounted(() => Promise.all([loadFolders(), loadComponents(), loadDatasources(), loadProjects()]))

onBeforeUnmount(() => {
  if (lockHeartbeatTimer.value) {
    clearInterval(lockHeartbeatTimer.value)
    lockHeartbeatTimer.value = null
  }
})
</script>

<style scoped>
.ide-wrap {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 110px);
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

/* IDE 视图时 sidebar + main 横向排列 */
.ide-body {
  flex: 1;
  display: flex;
  flex-direction: row;
  overflow: hidden;
  min-height: 0;
}

/* ---- 视图切换头部 ---- */
.view-header {
  width: 100%;
  height: 44px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: #FAFBFC;
  border-bottom: 1px solid #E5E6EB;
}
.view-tabs {
  display: flex;
  gap: 4px;
}
.view-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 14px;
  border-radius: 6px;
  font-size: 13px;
  color: #4E5969;
  cursor: pointer;
  user-select: none;
  transition: all 0.15s;
}
.view-tab:hover { background: #EFF4FF; color: #2B5AED; }
.view-tab.active { background: #2B5AED; color: #FFFFFF; }

/* ---- 左侧 ---- */
.ide-sidebar {
  width: 280px;
  height: 100%;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: #FAFBFC;
  border-right: 1px solid #E5E6EB;
}
.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid #E5E6EB;
}
.sidebar-title { font-size: 14px; font-weight: 600; color: #1D2129; }
.sidebar-search { padding: 6px 10px; border-bottom: 1px solid #F2F3F5; }

.comp-tree { flex: 1; overflow-y: auto; padding: 6px 0; }
.comp-tree::-webkit-scrollbar { width: 6px; }
.comp-tree::-webkit-scrollbar-thumb { background: #E5E6EB; border-radius: 3px; }
.comp-tree::-webkit-scrollbar-thumb:hover { background: #C9CDD4; }

/* 类型组标题 */
.grp-header {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  font-size: 11px;
  font-weight: 600;
  color: #4E5969;
  cursor: pointer;
  user-select: none;
  border-radius: 4px;
  margin: 1px 4px;
  transition: background 0.15s;
}
.grp-header:hover { background: #F2F3F5; }
.grp-label { flex: 1; }
.grp-count {
  font-size: 11px;
  background: #E5E6EB;
  color: #86909C;
  padding: 0 6px;
  height: 16px;
  line-height: 16px;
  border-radius: 8px;
  flex-shrink: 0;
}
.grp-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 4px;
  color: #86909C;
  font-size: 14px;
  flex-shrink: 0;
  opacity: 0.6;
  transition: opacity 0.15s, background 0.15s, color 0.15s;
}
.grp-header:hover .grp-action { opacity: 1; }
.grp-action:hover { background: #FFFFFF; color: #2B5AED; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.caret { font-size: 11px; color: #86909C; flex-shrink: 0; }

/* 树节点通用 */
.tree-node {
  display: flex;
  align-items: center;
  gap: 5px;
  height: 26px;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.15s, color 0.15s;
  position: relative;
  padding-right: 4px;
}
.tree-node:hover { background: #F2F3F5; }

/* 文件夹节点 */
.folder-node { color: #4E5969; font-weight: 500; }
.folder-node:hover .node-actions { opacity: 1; }
.folder-icon { font-size: 13px; color: #F7BA1E; flex-shrink: 0; }
.node-toggle { display: flex; align-items: center; flex-shrink: 0; cursor: pointer; }
.node-toggle:hover { color: #2B5AED; }

/* 组件节点 */
.comp-node { color: #1D2129; }
.comp-node:hover { background: #EAF1FF; }
.comp-node:hover .status-dot-only { opacity: 1; }
.comp-node.comp-open {
  background: linear-gradient(90deg, #EAF1FF 0%, #F0F5FF 100%);
  color: #2B5AED;
  font-weight: 500;
  box-shadow: inset 3px 0 0 0 #2B5AED;
}

.node-name { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.comp-node :deep(.lang-icon) { flex-shrink: 0; order: -1; }
.rename-input { flex: 1; height: 20px; font-size: 12px; }

.node-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.15s;
  flex-shrink: 0;
  padding-right: 4px;
}
.node-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 4px;
  color: #86909C;
  font-size: 13px;
  transition: background 0.15s, color 0.15s;
}
.node-action:hover { background: #FFFFFF; color: #2B5AED; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.node-action.danger:hover { background: #FFECE8; color: #F53F3F; box-shadow: 0 1px 3px rgba(245,63,63,0.15); }



/* 状态改为纯小圆点，hover 时通过 tooltip 显示文字 */
.status-dot-only {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-right: 4px;
  opacity: 0.7;
  transition: opacity 0.15s;
}
/* 保留旧 status-tag 兼容性（不显示） */
.status-tag {
  display: none;
}
.status-dot-inline {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.opt-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-right: 8px;
  vertical-align: middle;
}
.opt-danger { color: #F53F3F !important; }
.opt-danger:hover { background: #FFECE8 !important; }

/* ---- 右侧 ---- */
.ide-main {
  flex: 1;
  height: 100%;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.ide-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: #86909C;
}
.empty-hint { font-size: 14px; }

/* Tab bar */
.tab-bar {
  display: flex;
  align-items: center;
  height: 38px;
  background: #F7F8FA;
  border-bottom: 1px solid #E5E6EB;
  flex-shrink: 0;
  overflow: hidden;
}
.tabs-scroll {
  display: flex;
  flex: 1;
  overflow-x: auto;
  overflow-y: hidden;
  height: 100%;
  scrollbar-width: none;
}
.tabs-scroll::-webkit-scrollbar { display: none; }
.tab-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 10px;
  height: 100%;
  white-space: nowrap;
  cursor: pointer;
  font-size: 13px;
  color: #4E5969;
  border-right: 1px solid #E5E6EB;
  flex-shrink: 0;
  transition: background 0.1s;
}
.tab-item:hover { background: #EAF1FF; }
.tab-item.active { background: #fff; color: #2B5AED; border-bottom: 2px solid #2B5AED; }
.tab-name { max-width: 140px; overflow: hidden; text-overflow: ellipsis; }
.tab-close {
  width: 16px; height: 16px;
  line-height: 14px;
  text-align: center;
  border-radius: 50%;
  font-size: 14px;
  color: #86909C;
  flex-shrink: 0;
}
.tab-close:hover { background: #F53F3F; color: #fff; }

.add-tab-btn { flex-shrink: 0; margin: 0 4px; }

/* Toolbar */
.ide-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-bottom: 1px solid #F2F3F5;
  background: #fff;
  flex-shrink: 0;
}

/* Editor */
.editor-area { flex: 1; min-height: 0; overflow: hidden; }

/* Result panel */
.result-panel {
  max-height: 360px;
  flex-shrink: 0;
  border-top: 1px solid #E5E6EB;
  display: flex;
  flex-direction: column;
  background: #fff;
}
.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 14px;
  border-bottom: 1px solid #F2F3F5;
  background: #FAFBFC;
  font-size: 13px;
  flex-shrink: 0;
}
.result-info { font-size: 13px; color: #4E5969; }
.ok-text { color: #00B42A; font-weight: 500; }
.err-text { color: #F53F3F; font-weight: 500; }
.result-body { flex: 1; min-height: 0; overflow: auto; }
.result-spin { display: flex; align-items: center; justify-content: center; padding: 40px; }
.result-table { font-size: 12px; }
.result-text { padding: 16px; font-size: 13px; }
.result-log {
  margin: 0; padding: 12px 14px;
  font-size: 12px;
  font-family: 'JetBrains Mono', Consolas, monospace;
  white-space: pre-wrap; word-break: break-all; line-height: 1.6;
}
.log-ok { color: #1D2129; }
.log-err { color: #F53F3F; }

/* ---- 拖拽状态 ---- */
.dragging {
  opacity: 0.6;
  background: #EAF1FF !important;
}
.drop-target {
  background: #EAF1FF !important;
  border-radius: 4px;
}
.folder-node.drop-target {
  background: #EAF1FF !important;
  box-shadow: inset 0 0 0 1px #2B5AED;
}
.comp-node.drop-target {
  background: transparent !important;
}
.comp-node.drop-before {
  box-shadow: inset 0 2px 0 0 #2B5AED;
}
/* drop-after 不显示线，因为等价于下一个节点的 drop-before */

/* 历史版本详情 */
.history-detail {
  padding: 4px 0;
}
.history-code-label {
  font-size: 13px;
  font-weight: 500;
  margin: 12px 0 6px;
  color: var(--color-text-2);
}
.history-code {
  background: var(--color-fill-2);
  border-radius: 4px;
  padding: 10px 12px;
  font-size: 12px;
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow: auto;
  margin: 0;
}

/* DQC 弹窗样式 */
.dqc-hint {
  padding: 24px;
  text-align: center;
  color: #86909C;
  font-size: 13px;
}
.dqc-loading {
  display: flex;
  justify-content: center;
  padding: 24px;
}
.dqc-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.dqc-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #F7F8FA;
  border-radius: 6px;
  font-size: 13px;
}
.dqc-item-main {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
}
.dqc-name {
  font-weight: 500;
  color: #1D2129;
}
.dqc-item-sub {
  flex: 2;
  color: #86909C;
  font-size: 12px;
}
</style>
