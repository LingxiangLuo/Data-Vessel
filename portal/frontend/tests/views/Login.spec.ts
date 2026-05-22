import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import Login from '../../src/views/Login.vue'

// Mock vue-router
const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush }),
}))

// Mock Arco Design components
vi.mock('@arco-design/web-vue', () => ({
  Message: { success: vi.fn(), error: vi.fn() },
}))

vi.mock('@arco-design/web-vue/es/icon', () => ({
  IconUser: { template: '<span>user-icon</span>' },
  IconLock: { template: '<span>lock-icon</span>' },
}))

// Mock user store
const mockLogin = vi.fn()
const mockFetchUser = vi.fn()
vi.mock('../../src/stores/user', () => ({
  useUserStore: () => ({
    login: mockLogin,
    fetchUser: mockFetchUser,
  }),
}))

// Mock API
vi.mock('../../src/api', () => ({
  adminGetSsoPublic: vi.fn().mockResolvedValue([]),
}))

function mountLogin(overrides: Record<string, any> = {}) {
  return mount(Login, {
    global: {
      stubs: {
        'a-form': { template: '<form @submit.prevent><slot /></form>' },
        'a-form-item': { template: '<div><slot /></div>' },
        'a-input': { template: '<input />' },
        'a-input-password': { template: '<input type="password" />' },
        'a-button': { template: '<button><slot /></button>' },
      },
    },
    ...overrides,
  })
}

describe('Login.vue', () => {
  let localStorageMock: Record<string, string> = {}
  let originalLocalStorage: Storage
  let matchMediaMock: { matches: boolean; addEventListener: ReturnType<typeof vi.fn> }

  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock = {}
    originalLocalStorage = window.localStorage

    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn((key: string) => localStorageMock[key] || null),
        setItem: vi.fn((key: string, val: string) => { localStorageMock[key] = val }),
        removeItem: vi.fn((key: string) => { delete localStorageMock[key] }),
      },
      writable: true,
    })

    matchMediaMock = {
      matches: false,
      addEventListener: vi.fn(),
    }
    window.matchMedia = vi.fn().mockReturnValue(matchMediaMock)
  })

  afterEach(() => {
    vi.restoreAllMocks()
    Object.defineProperty(window, 'localStorage', { value: originalLocalStorage, writable: true })
  })

  it('should use saved theme from localStorage when available', () => {
    localStorageMock['login_theme'] = 'light'
    const wrapper = mountLogin()
    expect(wrapper.find('.login-page').classes()).toContain('light-mode')
  })

  it('should default to light theme when system prefers light and no saved preference', () => {
    matchMediaMock.matches = false
    const wrapper = mountLogin()
    expect(wrapper.find('.login-page').classes()).toContain('light-mode')
  })

  it('should follow system dark preference when no saved theme', () => {
    matchMediaMock.matches = true
    const wrapper = mountLogin()
    expect(wrapper.find('.login-page').classes()).not.toContain('light-mode')
  })

  it('should toggle theme and persist to localStorage when button clicked', async () => {
    matchMediaMock.matches = false
    const wrapper = mountLogin()
    const btn = wrapper.find('.theme-toggle')

    expect(wrapper.find('.login-page').classes()).toContain('light-mode')

    await btn.trigger('click')
    expect(wrapper.find('.login-page').classes()).not.toContain('light-mode')
    expect(window.localStorage.setItem).toHaveBeenCalledWith('login_theme', 'dark')

    await btn.trigger('click')
    expect(wrapper.find('.login-page').classes()).toContain('light-mode')
    expect(window.localStorage.setItem).toHaveBeenCalledWith('login_theme', 'light')
  })

  it('should prefill username from localStorage', () => {
    localStorageMock['login_username'] = 'saveduser'
    mountLogin()
    expect(window.localStorage.getItem).toHaveBeenCalledWith('login_username')
  })

  it('should save username to localStorage on successful login when remember is checked', async () => {
    mockLogin.mockResolvedValueOnce({ user: { username: 'testuser' } })
    const wrapper = mountLogin()

    const checkbox = wrapper.find('.glass-toggle input')
    expect(checkbox.exists()).toBe(true)
    await checkbox.setValue(true)

    await (wrapper.vm as any).handleLogin()
    expect(window.localStorage.setItem).toHaveBeenCalledWith('login_username', expect.any(String))
  })

  it('should remove saved username on successful login when remember is unchecked', async () => {
    mockLogin.mockResolvedValueOnce({ user: { username: 'testuser' } })
    localStorageMock['login_username'] = 'olduser'
    const wrapper = mountLogin()

    const checkbox = wrapper.find('.glass-toggle input')
    expect(checkbox.exists()).toBe(true)
    await checkbox.setValue(false)

    await (wrapper.vm as any).handleLogin()
    expect(window.localStorage.removeItem).toHaveBeenCalledWith('login_username')
  })

  it('should navigate to /dashboard on successful login', async () => {
    mockLogin.mockResolvedValueOnce({ user: { username: 'testuser' } })
    const wrapper = mountLogin()
    await (wrapper.vm as any).handleLogin()
    expect(mockPush).toHaveBeenCalledWith('/dashboard')
  })

  it('should show error message on login failure', async () => {
    const { Message } = await import('@arco-design/web-vue')
    mockLogin.mockRejectedValueOnce({ response: { data: { detail: '密码错误' } } })
    const wrapper = mountLogin()
    await (wrapper.vm as any).handleLogin()
    expect(Message.error).toHaveBeenCalledWith('密码错误')
  })
})
