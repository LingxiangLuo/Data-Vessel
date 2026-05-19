export type Language = 'sql' | 'python' | 'shell' | 'datax'

export type ComponentStatus =
  | 'draft'
  | 'developing'
  | 'testing'
  | 'reviewing'
  | 'tested'
  | 'online'
  | 'offline'
  | 'paused'
  | 'deprecated'
  | 'archived'

export interface ComponentParam {
  key: string
  value: string
  desc?: string
}

export interface ComponentItem {
  id: number
  name: string
  type: Language
  description?: string
  config_json: Record<string, any>
  params: ComponentParam[]
  version: number
  status: ComponentStatus
  status_label: string
  status_color: string
  ds_task_code?: number
  folder_id?: number
  sort_order: number
  code: string
  datasource_id?: number
  dqc_rule_ids?: number[]
  created_by?: number
  created_by_name?: string
  previous_status?: string
  created_at?: string
  updated_at?: string
}

export interface FolderItem {
  id: number
  name: string
  type: string
  parent_id?: number | null
  sort_order: number
  depth?: number
}

export interface DatasourceItem {
  id: number
  name: string
  type: string
  host: string
  port: number
  database_name: string
  username: string
  description?: string
  status: number
  last_check_time?: string
  created_at?: string
}

export interface ProjectItem {
  id: number
  name: string
  description?: string
}

export interface StatusDef {
  label: string
  color: string
  manual: boolean
}

export const STATUS_DEFS: Record<ComponentStatus, StatusDef> = {
  draft:       { label: '草稿',   color: '#86909C', manual: false },
  developing:  { label: '开发中', color: '#2B5AED', manual: true  },
  testing:     { label: '测试中', color: '#FF7D00', manual: true  },
  reviewing:   { label: '审核中', color: '#14B8A6', manual: true  },
  tested:      { label: '已测试', color: '#A3C644', manual: true  },
  online:      { label: '已上线', color: '#00B42A', manual: false },
  offline:     { label: '已下线', color: '#C9CDD4', manual: true  },
  paused:      { label: '已暂停', color: '#F53F3F', manual: true  },
  deprecated:  { label: '已废弃', color: '#6B7280', manual: true  },
  archived:    { label: '已归档', color: '#722ED1', manual: true  },
}

export const STATUS_TRANSITIONS: Record<ComponentStatus, ComponentStatus[]> = {
  draft:      ['developing', 'testing', 'deprecated', 'archived'],
  developing: ['testing', 'paused', 'deprecated'],
  testing:    ['reviewing', 'tested', 'paused', 'deprecated'],
  reviewing:  ['tested', 'paused', 'developing'],
  tested:     ['online', 'paused', 'testing'],
  online:     ['offline', 'paused'],
  offline:    ['online', 'archived', 'paused', 'developing'],
  paused:     [],
  deprecated: ['archived'],
  archived:   [],
}

export function statusLabel(s: string): string {
  return STATUS_DEFS[s as ComponentStatus]?.label || s
}

export function statusColor(s: string): string {
  return STATUS_DEFS[s as ComponentStatus]?.color || '#86909C'
}

export function manualStatusOptions(current: ComponentStatus) {
  if (current === 'paused' || current === 'archived') return []
  const allowed = STATUS_TRANSITIONS[current] ?? []
  return allowed
    .filter(k => STATUS_DEFS[k]?.manual)
    .map(k => ({ value: k, label: STATUS_DEFS[k].label, color: STATUS_DEFS[k].color }))
}
