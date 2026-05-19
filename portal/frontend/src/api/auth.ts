import { api } from './client'

export const login = (data: { username: string; password: string }) =>
  api.post('/auth/login', data)

export const logout = () => api.post('/auth/logout')
export const getMe = () => api.get('/auth/me')
export const getMyPermissions = () => api.get('/auth/me/permissions')
