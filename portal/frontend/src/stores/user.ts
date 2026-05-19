import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, logout as logoutApi, getMe, getMyPermissions } from '../api'

export const useUserStore = defineStore('user', () => {
  const userInfo = ref<any>(null)
  const permissions = ref<string[]>([])

  const isLoggedIn = computed(() => !!userInfo.value)
  const isAdmin = computed(() =>
    userInfo.value?.role === 'admin' || permissions.value.includes('user:manage')
  )

  function hasPermission(code: string): boolean {
    if (userInfo.value?.role === 'admin') return true
    return permissions.value.includes(code)
  }

  async function login(username: string, password: string) {
    const res: any = await loginApi({ username, password })
    userInfo.value = res.user
    await _fetchPermissions()
    return res
  }

  async function fetchUser() {
    try {
      const res: any = await getMe()
      userInfo.value = res
      await _fetchPermissions()
    } catch {
      userInfo.value = null
      permissions.value = []
    }
  }

  async function _fetchPermissions() {
    try {
      const res: any = await getMyPermissions()
      permissions.value = res.permissions || []
    } catch {
      permissions.value = []
    }
  }

  async function logout() {
    try { await logoutApi() } catch {}
    userInfo.value = null
    permissions.value = []
  }

  return { userInfo, permissions, isLoggedIn, isAdmin, hasPermission, login, fetchUser, logout }
})
