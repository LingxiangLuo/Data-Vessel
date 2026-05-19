import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '../../src/stores/user'

vi.mock('../../src/api', () => ({
  login: vi.fn(),
  logout: vi.fn(),
  getMe: vi.fn(),
  getMyPermissions: vi.fn(),
}))

describe('useUserStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should not be logged in by default', () => {
    const store = useUserStore()
    expect(store.isLoggedIn).toBe(false)
    expect(store.isAdmin).toBe(false)
    expect(store.hasPermission('any')).toBe(false)
  })

  it('admin role bypasses all permission checks', () => {
    const store = useUserStore()
    store.userInfo = { role: 'admin', username: 'admin' }
    expect(store.isAdmin).toBe(true)
    expect(store.hasPermission('workflow:publish')).toBe(true)
    expect(store.hasPermission('nonexistent')).toBe(true)
  })

  it('non-admin checks permissions list', () => {
    const store = useUserStore()
    store.userInfo = { role: 'developer', username: 'dev' }
    store.permissions = ['component:read', 'workflow:read']
    expect(store.hasPermission('component:read')).toBe(true)
    expect(store.hasPermission('workflow:read')).toBe(true)
    expect(store.hasPermission('component:write')).toBe(false)
    expect(store.isAdmin).toBe(false)
  })

  it('user:manage in permissions grants admin-like access', () => {
    const store = useUserStore()
    store.userInfo = { role: 'developer', username: 'ops' }
    store.permissions = ['user:manage']
    expect(store.isAdmin).toBe(true)
  })

  it('logout clears state', async () => {
    const store = useUserStore()
    store.userInfo = { role: 'admin' }
    store.permissions = ['all']
    await store.logout()
    expect(store.userInfo).toBeNull()
    expect(store.permissions).toEqual([])
    expect(store.isLoggedIn).toBe(false)
  })
})
