<template>
  <Teleport to="body">
    <Transition name="cm-fade">
      <div v-if="visible" class="cm-overlay" @click="onOverlayClick">
        <div
          ref="menuRef"
          class="cm-menu"
          :style="menuStyle"
          @click.stop
        >
          <MenuList :items="items" @select="onSelect" />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onUnmounted, h, defineComponent } from 'vue'

export interface MenuItem {
  key?: string
  label?: string
  icon?: string
  disabled?: boolean
  danger?: boolean
  children?: MenuItem[]
  divider?: boolean
}

const props = defineProps<{
  visible: boolean
  x: number
  y: number
  items: MenuItem[]
}>()

const emit = defineEmits<{
  (e: 'update:visible', v: boolean): void
  (e: 'select', key: string): void
}>()

const menuRef = ref<HTMLElement>()

const menuStyle = computed(() => ({
  left: `${props.x}px`,
  top: `${props.y}px`,
}))

function close() {
  emit('update:visible', false)
}

function onOverlayClick() {
  close()
}

function onSelect(key: string) {
  emit('select', key)
  close()
}

watch(() => props.visible, (v) => {
  if (v) {
    nextTick(() => {
      document.addEventListener('mousedown', outsideHandler)
    })
  } else {
    document.removeEventListener('mousedown', outsideHandler)
  }
})

function outsideHandler(e: MouseEvent) {
  if (!menuRef.value?.contains(e.target as Node)) {
    close()
  }
}

onUnmounted(() => {
  document.removeEventListener('mousedown', outsideHandler)
})

const MenuList: any = defineComponent({
  name: 'MenuList',
  props: {
    items: { type: Array as () => MenuItem[], required: true },
    nested: { type: Boolean, default: false },
  },
  emits: ['select'],
  setup(menuProps: { items: MenuItem[]; nested: boolean }, { emit: menuEmit }: { emit: (e: 'select', key: string) => void }) {
    const activeKey = ref<string | null>(null)
    let hideTimer: any = null

    function onItemClick(item: MenuItem) {
      if (item.disabled || item.children?.length) return
      menuEmit('select', item.key!)
    }

    function onMouseEnter(item: MenuItem) {
      if (hideTimer) { clearTimeout(hideTimer); hideTimer = null }
      activeKey.value = item.children?.length ? (item.key ?? null) : null
    }

    function onMouseLeave() {
      hideTimer = setTimeout(() => { activeKey.value = null }, 300)
    }

    return (): any => h('ul', { class: ['cm-list', { 'cm-nested': menuProps.nested }] },
      menuProps.items.map((item): any => {
        if (item.divider) {
          return h('li', { class: 'cm-divider' })
        }
        const hasChildren = !!item.children?.length
        const isActive = activeKey.value === item.key
        return h('li', {
          class: [
            'cm-item',
            {
              'cm-disabled': item.disabled,
              'cm-danger': item.danger,
              'cm-active': isActive,
            },
          ],
          onClick: () => onItemClick(item),
          onMouseenter: () => onMouseEnter(item),
          onMouseleave: onMouseLeave,
        }, [
          h('span', { class: 'cm-label' }, item.label),
          hasChildren && h('span', { class: 'cm-arrow' }, '▶'),
          hasChildren && isActive && h('div', {
            class: 'cm-submenu',
            onMouseenter: () => {
              if (hideTimer) { clearTimeout(hideTimer); hideTimer = null }
              activeKey.value = item.key ?? null
            },
            onMouseleave: onMouseLeave,
          }, [
            h(MenuList, {
              items: item.children!,
              nested: true,
              onSelect: (key: string) => menuEmit('select', key),
            }),
          ]),
        ])
      })
    )
  },
})
</script>

<style>
.cm-overlay {
  position: fixed;
  inset: 0;
  z-index: 9998;
}

.cm-menu {
  position: fixed;
  z-index: 9999;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.14), 0 1px 4px rgba(0, 0, 0, 0.08);
  padding: 6px 0;
  min-width: 200px;
  font-size: 13px;
  line-height: 1;
  user-select: none;
  overflow: visible;
}

.cm-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.cm-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 28px 0 14px;
  height: 30px;
  cursor: pointer;
  color: #1d1d1d;
  transition: background 0.1s;
  white-space: nowrap;
  margin: 2px 6px;
  border-radius: 5px;
}

.cm-item:hover {
  background: #e8e8e8;
}

.cm-item.cm-active {
  background: #d8d8d8;
}

.cm-item.cm-danger {
  color: #d13438;
}

.cm-item.cm-danger:hover {
  background: #fde7e9;
}

.cm-item.cm-danger.cm-active {
  background: #d13438;
  color: #fff;
}

.cm-item.cm-disabled {
  color: #a0a0a0;
  cursor: default;
}

.cm-item.cm-disabled:hover,
.cm-item.cm-disabled.cm-active {
  background: transparent;
  color: #a0a0a0;
}

.cm-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 400;
}

.cm-arrow {
  font-size: 8px;
  color: #888;
  flex-shrink: 0;
  margin-left: auto;
  transform: scale(0.75);
}

.cm-item:hover .cm-arrow,
.cm-item.cm-active .cm-arrow {
  color: #444;
}

.cm-divider {
  height: 1px;
  background: #e8e8e8;
  margin: 5px 0;
  list-style: none;
}

.cm-submenu {
  position: absolute;
  left: calc(100% + 2px);
  top: -6px;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.14), 0 1px 4px rgba(0, 0, 0, 0.08);
  padding: 6px 0;
  min-width: 180px;
  z-index: 10000;
  overflow: visible;
}

.cm-nested .cm-item {
  height: 28px;
  font-size: 13px;
  padding: 0 24px 0 14px;
  margin: 2px 6px;
  border-radius: 5px;
}

.cm-fade-enter-active,
.cm-fade-leave-active {
  transition: opacity 0.1s ease;
}

.cm-fade-enter-from,
.cm-fade-leave-to {
  opacity: 0;
}

.cm-fade-enter-to,
.cm-fade-leave-from {
  opacity: 1;
}
</style>
