export type FieldMappingKind = 'column' | 'constant' | 'variable'

export interface FieldMappingItem {
  kind: FieldMappingKind
  src: string
  dst: string
  type?: string
}

export interface DataXConfig {
  name: string
  source_id: number | undefined
  target_id: number | undefined
  source_table: string
  target_table: string
  sync_type: 'full' | 'increment'
  increment_column: string | undefined
  field_mapping: FieldMappingItem[]
  where_clause: string | undefined
  split_pk: string | undefined
  write_mode: 'insert' | 'replace' | 'update'
  channel: number
  pre_sql: string[] | undefined
  post_sql: string[] | undefined
  rawJson?: string
}

export function emptyDataXConfig(): DataXConfig {
  return {
    name: '',
    source_id: undefined,
    target_id: undefined,
    source_table: '',
    target_table: '',
    sync_type: 'full',
    increment_column: undefined,
    field_mapping: [],
    where_clause: undefined,
    split_pk: undefined,
    write_mode: 'insert',
    channel: 3,
    pre_sql: undefined,
    post_sql: undefined,
  }
}

export function configToJson(cfg: DataXConfig): string {
  try {
    return JSON.stringify(cfg, null, 2)
  } catch {
    return '{}'
  }
}

export function jsonToConfig(json: string): DataXConfig | { error: string } {
  try {
    const raw = JSON.parse(json)
    const cfg: DataXConfig = {
      name: raw.name || '',
      source_id: raw.source_id ?? undefined,
      target_id: raw.target_id ?? undefined,
      source_table: raw.source_table || '',
      target_table: raw.target_table || '',
      sync_type: raw.sync_type === 'increment' ? 'increment' : 'full',
      increment_column: raw.increment_column ?? undefined,
      field_mapping: Array.isArray(raw.field_mapping) ? raw.field_mapping : [],
      where_clause: raw.where_clause ?? undefined,
      split_pk: raw.split_pk ?? undefined,
      write_mode: ['insert', 'replace', 'update'].includes(raw.write_mode) ? raw.write_mode : 'insert',
      channel: Number.isFinite(raw.channel) ? Math.min(Math.max(Math.round(raw.channel), 1), 32) : 3,
      pre_sql: Array.isArray(raw.pre_sql) ? raw.pre_sql : undefined,
      post_sql: Array.isArray(raw.post_sql) ? raw.post_sql : undefined,
      rawJson: raw.rawJson,
    }
    return cfg
  } catch (e: any) {
    return { error: e.message || 'JSON 解析失败' }
  }
}

export function buildComponentPayload(cfg: DataXConfig, extra?: { code?: string; description?: string; folder_id?: number | null }) {
  const payload: Record<string, any> = {
    config_json: {
      name: cfg.name,
      source_id: cfg.source_id,
      target_id: cfg.target_id,
      source_table: cfg.source_table,
      target_table: cfg.target_table,
      sync_type: cfg.sync_type,
      increment_column: cfg.increment_column,
      field_mapping: cfg.field_mapping,
      where_clause: cfg.where_clause,
      split_pk: cfg.split_pk,
      write_mode: cfg.write_mode,
      channel: cfg.channel,
      pre_sql: cfg.pre_sql,
      post_sql: cfg.post_sql,
    },
  }
  if (cfg.rawJson) {
    payload.config_json.rawJson = cfg.rawJson
  }
  if (extra?.code !== undefined) {
    payload.code = extra.code
  }
  if (extra?.description !== undefined) {
    payload.description = extra.description
  }
  if (extra?.folder_id !== undefined) {
    payload.folder_id = extra.folder_id
  }
  return payload
}
