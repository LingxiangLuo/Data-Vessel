import { api, reportFrontendError } from './client'

// 统一导出（保持向后兼容，新代码可直接从子模块导入）
export { api, reportFrontendError }
export * from './auth'
export * from './component'
export * from './workflow'
export * from './dqc'
export * from './ds'

// ─── Dashboard ─────────────────────────────────────────────────────────────
export const getDashboardStats = () => api.get('/dashboard/stats')

// ─── DataSources ───────────────────────────────────────────────────────────
export const getDatasources = (params?: any) => api.get('/datasources', { params })
export const getDatasource = (id: number) => api.get(`/datasources/${id}`)
export const createDatasource = (data: any) => api.post('/datasources', data)
export const updateDatasource = (id: number, data: any) => api.put(`/datasources/${id}`, data)
export const deleteDatasource = (id: number) => api.delete(`/datasources/${id}`)
export const testDatasource = (id: number) => api.post(`/datasources/${id}/test`)

// ─── Sync Tasks ────────────────────────────────────────────────────────────
export const getSyncTasks = (params?: any) => api.get('/sync-tasks', { params })
export const getSyncTask = (id: number) => api.get(`/sync-tasks/${id}`)
export const createSyncTask = (data: any) => api.post('/sync-tasks', data)
export const updateSyncTask = (id: number, data: any) => api.put(`/sync-tasks/${id}`, data)
export const deleteSyncTask = (id: number) => api.delete(`/sync-tasks/${id}`)
export const setSyncTaskStatus = (id: number, status: string) => api.patch(`/sync-tasks/${id}/status`, null, { params: { status } })
export const previewSyncTaskDataX = (id: number) => api.get(`/sync-tasks/${id}/preview-datax`)
export const previewDataXConfig = (data: any) => api.post('/components/preview-datax', data)
export const previewSyncTaskUnsaved = previewDataXConfig
export const testSyncTaskConnection = (data: { datasource_id: number; table?: string }) =>
  api.post('/sync-tasks/test-connection', data)
export const runSyncTask = (_id: number) => Promise.reject(new Error('已废弃：请通过工作流运行数据同步任务'))
export const publishSyncTaskAsWorkflow = (id: number) => api.post(`/sync-tasks/${id}/publish-as-workflow`)

// ─── Alert Rules ───────────────────────────────────────────────────────────
export const getAlertRules = () => api.get('/alert-rules')
export const createAlertRule = (data: any) => api.post('/alert-rules', data)
export const updateAlertRule = (id: number, data: any) => api.put(`/alert-rules/${id}`, data)
export const deleteAlertRule = (id: number) => api.delete(`/alert-rules/${id}`)
export const toggleAlertRule = (id: number) => api.patch(`/alert-rules/${id}/toggle`)
export const testAlertNotify = (data: { notify_type?: string; notify_config?: any; channel_id?: number; channel_ids?: number[] }) =>
  api.post('/alert-rules/test-notify', data)

// ─── Word Roots ────────────────────────────────────────────────────────────
export const getWordRoots = (params?: any) => api.get('/word-roots', { params })
export const createWordRoot = (data: any) => api.post('/word-roots', data)
export const updateWordRoot = (id: number, data: any) => api.put(`/word-roots/${id}`, data)
export const deleteWordRoot = (id: number) => api.delete(`/word-roots/${id}`)
export const importWordRoots = (file: File) => {
  const fd = new FormData(); fd.append('file', file)
  return api.post('/word-roots/import', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
}
export const suggestNaming = (q: string) => api.get('/word-roots/suggest', { params: { q } })

// ─── Metadata ──────────────────────────────────────────────────────────────
export const getMetadataStats = () => api.get('/metadata/stats')
export const getMetadataLineage = () => api.get('/metadata/lineage')
export const getMetadataTables = (datasource_id: number, keyword?: string, limit = 100) =>
  api.get('/metadata/tables', { params: { datasource_id, keyword, limit } })
export const getMetadataColumns = (datasource_id: number, table: string) => api.get('/metadata/columns', { params: { datasource_id, table } })
export const getMetadataPreview = (datasource_id: number, table: string, limit = 10) => api.get('/metadata/preview', { params: { datasource_id, table, limit } })
export const getMetadataQuality = (datasource_id: number, table: string) => api.get('/metadata/quality', { params: { datasource_id, table } })
export const generateDDL = (data: { datasource_id: number; target_table: string; columns: any[] }) =>
  api.post('/metadata/generate-ddl', data)
export const executeDDL = (data: { datasource_id: number; ddl?: string; statements?: string[] }) =>
  api.post('/metadata/execute-ddl', data)

// ─── Projects ──────────────────────────────────────────────────────────────
export const getProjects = (params?: any) => api.get('/projects', { params })
export const getProject = (id: number) => api.get(`/projects/${id}`)
export const createProject = (data: any) => api.post('/projects', data)
export const updateProject = (id: number, data: any) => api.put(`/projects/${id}`, data)
export const deleteProject = (id: number, moveTo?: number) =>
  api.delete(`/projects/${id}`, { params: moveTo !== undefined ? { move_to: moveTo } : {} })

// ─── System ────────────────────────────────────────────────────────────────
export const getSystemServices = () => api.get('/system/services')

// ─── Notifications ─────────────────────────────────────────────────────────
export const getNotifications = (params?: any) => api.get('/notifications', { params })
export const getUnreadCount = () => api.get('/notifications/unread-count')
export const markNotifRead = (id: number) => api.put(`/notifications/${id}/read`)
export const markAllRead = () => api.put('/notifications/read-all')

// ─── Admin ─────────────────────────────────────────────────────────────────
export const adminListUsers = (params?: any) => api.get('/admin/users', { params })
export const adminCreateUser = (data: any) => api.post('/admin/users', data)
export const adminUpdateUser = (id: number, data: any) => api.put(`/admin/users/${id}`, data)
export const adminDeleteUser = (id: number) => api.delete(`/admin/users/${id}`)

export const adminListRoles = () => api.get('/admin/roles')
export const adminCreateRole = (data: any) => api.post('/admin/roles', data)
export const adminUpdateRole = (id: number, data: any) => api.put(`/admin/roles/${id}`, data)
export const adminDeleteRole = (id: number) => api.delete(`/admin/roles/${id}`)

export const adminListPermissions = () => api.get('/admin/permissions')

export const adminListSso = () => api.get('/admin/sso')
export const adminUpdateSso = (provider: string, data: any) => api.put(`/admin/sso/${provider}`, data)
export const adminGetSsoPublic = () => api.get('/admin/sso/public')

export const adminGetConfig = (key: string) => api.get(`/admin/config/${key}`)
export const adminSetConfig = (key: string, data: any) => api.put(`/admin/config/${key}`, data)
export const adminTestSmtp = () => api.post('/admin/config/smtp/test')

export const adminListResourceAccess = (resource_type: string, resource_id: number) =>
  api.get('/admin/resource-access', { params: { resource_type, resource_id } })
export const adminGrantResourceAccess = (data: {
  resource_type: string; resource_id: number
  subject_type: string; subject_id: number; permission: string
}) => api.post('/admin/resource-access', data)
export const adminRevokeResourceAccess = (data: {
  resource_type: string; resource_id: number
  subject_type: string; subject_id: number
}) => api.delete('/admin/resource-access', { data })

// ─── Notify Channels ───────────────────────────────────────────────────────
export const adminListChannels = () => api.get('/admin/notify-channels')
export const adminCreateChannel = (data: any) => api.post('/admin/notify-channels', data)
export const adminUpdateChannel = (id: number, data: any) => api.put(`/admin/notify-channels/${id}`, data)
export const adminDeleteChannel = (id: number) => api.delete(`/admin/notify-channels/${id}`)
export const adminTestChannel = (id: number) => api.post(`/admin/notify-channels/${id}/test`)

export default api
