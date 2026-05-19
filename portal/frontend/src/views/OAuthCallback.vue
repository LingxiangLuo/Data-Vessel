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
  // token 在 hash fragment 中（#token=xxx），不会出现在服务器日志
  const hash = window.location.hash.slice(1)  // 去掉 '#'
  const params = new URLSearchParams(hash)
  const token = params.get('token')

  // 立即清除 hash，避免 token 留在浏览器历史
  window.history.replaceState(null, '', window.location.pathname)

  if (!token) {
    Message.error('OAuth 登录失败：未获取到 token')
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
