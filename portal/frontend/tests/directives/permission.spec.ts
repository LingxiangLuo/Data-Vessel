import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { useUserStore } from '../../src/stores/user'
import { permissionDirective } from '../../src/directives/permission'

vi.mock('../../src/api', () => ({
  login: vi.fn(),
  logout: vi.fn(),
  getMe: vi.fn(),
  getMyPermissions: vi.fn(),
}))

describe('v-permission directive', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  function mountWithPerm(code: string, hasPerm: boolean) {
    const store = useUserStore()
    store.userInfo = { role: 'developer' }
    store.permissions = hasPerm ? [code] : []

    return mount({
      template: `<div v-permission="'${code}'">content</div>`,
      directives: { permission: permissionDirective },
    })
  }

  it('shows element when permission granted', () => {
    const wrapper = mountWithPerm('component:read', true)
    expect((wrapper.element as HTMLElement).style.display).not.toBe('none')
  })

  it('hides element when permission denied', () => {
    const wrapper = mountWithPerm('component:write', false)
    expect((wrapper.element as HTMLElement).style.display).toBe('none')
  })
})
