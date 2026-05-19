import type { App, DirectiveBinding } from 'vue'
import { useUserStore } from '../stores/user'

export const permissionDirective = {
  mounted(el: HTMLElement, binding: DirectiveBinding) {
    const store = useUserStore()
    const code = binding.value as string
    if (code && !store.hasPermission(code)) {
      el.style.display = 'none'
    }
  },
  updated(el: HTMLElement, binding: DirectiveBinding) {
    const store = useUserStore()
    const code = binding.value as string
    if (code && !store.hasPermission(code)) {
      el.style.display = 'none'
    } else {
      el.style.display = ''
    }
  },
}

export function setupPermissionDirective(app: App) {
  app.directive('permission', permissionDirective)
}
