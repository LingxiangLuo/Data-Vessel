export type Language = 'sql' | 'python' | 'shell' | 'datax'

export type ComponentStatus = 'draft' | 'tested' | 'online' | 'offline'

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
}

export const STATUS_DEFS: Record<ComponentStatus, StatusDef> = {
  draft:   { label: '草稿',   color: '#86909C' },
  tested:  { label: '已测试', color: '#0FC6C2' },
  online:  { label: '已上线', color: '#00B42A' },
  offline: { label: '已下线', color: '#FF7D00' },
}

export function statusLabel(s: string): string {
  return STATUS_DEFS[s as ComponentStatus]?.label || s
}

export function statusColor(s: string): string {
  return STATUS_DEFS[s as ComponentStatus]?.color || '#86909C'
}
