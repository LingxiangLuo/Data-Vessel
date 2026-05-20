import { api } from './client'

// Component Folders
export const getComponentFolders = (type?: string) =>
  api.get('/components/folders', { params: type ? { type } : {} })
export const createComponentFolder = (data: { name: string; type: string; parent_id?: number | null }) =>
  api.post('/components/folders', data)
export const renameComponentFolder = (id: number, name: string) =>
  api.put(`/components/folders/${id}`, { name })
export const deleteComponentFolder = (id: number) =>
  api.delete(`/components/folders/${id}`)

// Components
export const getComponents = (params?: any) => api.get('/components', { params })
export const getComponent = (id: number) => api.get(`/components/${id}`)
export const createComponent = (data: any) => api.post('/components', data)
export const updateComponent = (id: number, data: any) => api.put(`/components/${id}`, data)
export const deleteComponent = (id: number) => api.delete(`/components/${id}`)
export const testComponent = (id: number, runtimeParams?: Record<string, string>) => api.post(`/components/${id}/test`, { runtime_params: runtimeParams })
export const publishComponent = (id: number) => api.post(`/components/${id}/publish`)
export const offlineComponent = (id: number) => api.post(`/components/${id}/offline`)
export const runComponent = (id: number, runtimeParams?: Record<string, string>) => api.post(`/components/${id}/run`, { runtime_params: runtimeParams })
export const publishComponentAsWorkflow = (id: number) =>
  api.post(`/components/${id}/publish-as-workflow`)
export const runSqlAdhoc = (data: { datasource_id: number; sql: string }) =>
  api.post('/components/run-sql', data, { timeout: 60000 })
export const runComponentScript = (id: number, datasourceId?: number, runtimeParams?: Record<string, string>) =>
  api.post(`/components/${id}/run${datasourceId ? `?datasource_id=${datasourceId}` : ''}`, { runtime_params: runtimeParams }, { timeout: 120000 })
export const quickPublishComponent = (id: number) =>
  api.post(`/components/${id}/quick-publish`)

// Component History
export const getComponentHistory = (id: number) => api.get(`/components/${id}/history`)
export const getComponentHistoryDetail = (id: number, version: number) =>
  api.get(`/components/${id}/history/${version}`)
export const rollbackComponent = (id: number, version: number, comment?: string) =>
  api.post(`/components/${id}/history/${version}/rollback`, { comment })

// Component Lock
export const acquireComponentLock = (id: number) => api.post(`/components/${id}/lock`)
export const releaseComponentLock = (id: number) => api.delete(`/components/${id}/lock`)
export const heartbeatComponentLock = (id: number) => api.put(`/components/${id}/lock/heartbeat`)
export const getComponentLockStatus = (id: number) => api.get(`/components/${id}/lock`)

// Component Move / Reorder
export const moveComponent = (id: number, folderId?: number | null, sortOrder?: number) =>
  api.put(`/components/${id}/move`, { folder_id: folderId ?? 0, sort_order: sortOrder })
export const reorderComponents = (orders: { id: number; sort_order: number }[]) =>
  api.post('/components/reorder', { orders })
export const moveComponentFolder = (id: number, parentId?: number | null, sortOrder?: number) =>
  api.put(`/components/folders/${id}/move`, { parent_id: parentId ?? 0, sort_order: sortOrder })
