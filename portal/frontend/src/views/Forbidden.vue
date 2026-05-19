<template>
  <div class="forbidden-page">
    <div class="code">403</div>
    <div class="title">权限不足</div>
    <div class="desc">您没有访问该页面的权限，请联系管理员。</div>
    <a-button type="primary" @click="$router.push('/dashboard')">返回工作台</a-button>
  </div>
</template>

<style scoped>
.forbidden-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 400px;
  gap: 12px;
}
.code { font-size: 72px; font-weight: 700; color: #E5E8ED; line-height: 1; }
.title { font-size: 20px; font-weight: 600; color: #1D2129; }
.desc { color: #86909C; font-size: 14px; }
</style>
