<template>
  <div class="oauth-callback">
    <a-spin :loading="true" tip="正在登录..." />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

onMounted(async () => {
  const hash = window.location.hash.slice(1)
  const params = new URLSearchParams(hash)
  const status = params.get('status')

  window.history.replaceState(null, '', window.location.pathname)

  if (status !== 'ok') {
    Message.error('OAuth 登录失败')
    router.push('/login')
    return
  }

  // token 已由后端写入 httponly cookie，这里只需拉取用户信息
  try {
    await userStore.fetchUser()
    Message.success('登录成功')
    router.push('/dashboard')
  } catch {
    Message.error('获取用户信息失败')
    router.push('/login')
  }
})
</script>

<style scoped>
.oauth-callback {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
