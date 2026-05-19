<template>
  <slot v-if="hasAccess" />
  <slot v-else name="fallback" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useUserStore } from '../stores/user'

interface Props {
  code?: string
}

const props = withDefaults(defineProps<Props>(), { code: '' })
const store = useUserStore()

const hasAccess = computed(() => !props.code || store.hasPermission(props.code))
</script>
