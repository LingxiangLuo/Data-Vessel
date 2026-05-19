import { api } from './client'

export const getDqcRules = (params?: any) => api.get('/dqc-rules', { params })
export const getDqcRule = (id: number) => api.get(`/dqc-rules/${id}`)
export const createDqcRule = (data: any) => api.post('/dqc-rules', data)
export const updateDqcRule = (id: number, data: any) => api.put(`/dqc-rules/${id}`, data)
export const deleteDqcRule = (id: number) => api.delete(`/dqc-rules/${id}`)
export const toggleDqcRule = (id: number) => api.patch(`/dqc-rules/${id}/toggle`)
export const runDqcCheck = (id: number) => api.post(`/dqc-rules/${id}/check`)
export const getDqcRuleHistory = (id: number, limit?: number) => api.get(`/dqc-rules/${id}/history`, { params: limit ? { limit } : {} })
export const getDqcChecks = (params?: any) => api.get('/dqc-rules/checks/all', { params })
export const getDqcStats = (days?: number) => api.get('/dqc-rules/checks/stats', { params: days ? { days } : {} })
