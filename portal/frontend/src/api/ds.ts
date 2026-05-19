import { api } from './client'

export const getDSWorkflows = (params?: any) => api.get('/ds/workflows', { params })
export const runDSWorkflow = (code: number) => api.post(`/ds/workflows/${code}/run`)
export const onlineDSWorkflow = (code: number) => api.post(`/ds/workflows/${code}/online`)
export const offlineDSWorkflow = (code: number) => api.post(`/ds/workflows/${code}/offline`)
export const rerunDSWorkflow = (code: number) => api.post(`/ds/workflows/${code}/rerun`)
export const complementDSWorkflow = (code: number, startDate: string, endDate: string) =>
  api.post(`/ds/workflows/${code}/complement?start_date=${startDate}&end_date=${endDate}`)
export const getDSInstances = (params?: any) => api.get('/ds/instances', { params })
export const getDSCalendar = (days?: number) => api.get('/ds/instances/calendar', { params: { days } })
export const getDSInstanceTasks = (instanceId: number) => api.get(`/ds/instances/${instanceId}/tasks`)
export const getDSInstanceDetail = (instanceId: number) => api.get(`/ds/instances/${instanceId}/detail`)
export const getDSTaskLog = (taskId: number) => api.get(`/ds/tasks/${taskId}/log`)
export const rerunDSInstance = (instanceId: number) => api.post(`/ds/instances/${instanceId}/rerun`)
export const getDSMonitor = () => api.get('/ds/monitor')
