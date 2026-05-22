<template>
  <div class="login-page" :class="{ 'light-mode': !isDark }">
    <!-- 流动背景层 -->
    <div class="flow-bg" ref="flowBgRef">
      <!-- 底层均匀光晕，消除纯黑死角 -->
      <div class="flow-glow"></div>
      <!-- 旋转色轮 -->
      <div class="flow-wheel"></div>
      <!-- 光斑由JS动态生成 -->
      <div
        v-for="(b, i) in blobs"
        :key="i"
        class="flow-blob"
        :style="b.style"
      ></div>
      <!-- 粒子由JS动态生成 -->
      <div
        v-for="(p, i) in particles"
        :key="'p' + i"
        class="flow-particle"
        :style="p.style"
      ></div>
      <!-- 流动线条 -->
      <div class="flow-lines"></div>
      <!-- 噪点纹理 -->
      <div class="flow-noise"></div>
    </div>

    <!-- 登录卡片 -->
    <div class="login-card">
      <!-- 主题切换 -->
      <button class="theme-toggle" @click="toggleTheme" :title="isDark ? '切换浅色' : '切换深色'">
        <svg v-if="isDark" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="5"/>
          <line x1="12" y1="1" x2="12" y2="3"/>
          <line x1="12" y1="21" x2="12" y2="23"/>
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
          <line x1="1" y1="12" x2="3" y2="12"/>
          <line x1="21" y1="12" x2="23" y2="12"/>
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
        </svg>
        <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
      </button>

      <div class="login-header">
        <div class="login-logo">
          <svg width="40" height="40" viewBox="0 0 36 36" fill="none">
            <defs>
              <linearGradient id="logo-grad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#2B5AED"/>
                <stop offset="100%" stop-color="#00C9A7"/>
              </linearGradient>
            </defs>
            <rect width="36" height="36" rx="8" fill="url(#logo-grad)"/>
            <path d="M9 10h18v2.5H11.5v5h13v2.5h-13v5H27V27.5H9V10z" fill="white"/>
          </svg>
        </div>
        <h2 class="login-title">欢迎登录</h2>
        <p class="login-subtitle">Data Platform</p>
      </div>

      <a-form :model="form" @submit-success="handleLogin" layout="vertical">
        <a-form-item field="username" label="用户名" :rules="[{ required: true, message: '请输入用户名' }]">
          <a-input
            v-model="form.username"
            placeholder="请输入用户名"
            size="large"
            autocomplete="username"
            :disabled="loading"
          >
            <template #prefix><icon-user /></template>
          </a-input>
        </a-form-item>

        <a-form-item field="password" label="密码" :rules="[{ required: true, message: '请输入密码' }]">
          <a-input-password
            v-model="form.password"
            placeholder="请输入密码"
            size="large"
            autocomplete="current-password"
            :disabled="loading"
          >
            <template #prefix><icon-lock /></template>
          </a-input-password>
        </a-form-item>

        <a-form-item style="margin-bottom: 8px;">
          <div class="remember-row">
            <label class="glass-toggle">
              <input type="checkbox" v-model="form.remember" :disabled="loading">
              <span class="toggle-track">
                <span class="toggle-thumb"></span>
              </span>
            </label>
            <span class="remember-label">记住用户名</span>
            <span class="forget-hint">忘记密码请联系管理员</span>
          </div>
        </a-form-item>

        <a-form-item>
          <a-button type="primary" html-type="submit" long size="large" :loading="loading" class="login-btn">
            登 录
          </a-button>
        </a-form-item>
      </a-form>

      <!-- SSO 登录区 -->
      <template v-if="enabledProviders.length > 0">
        <div class="sso-divider"><span>或使用企业账号登录</span></div>
        <div class="sso-buttons">
          <a-button
            v-for="p in enabledProviders"
            :key="p.provider"
            class="sso-btn"
            :disabled="loading"
            @click="ssoLogin(p.provider)"
          >
            <span class="sso-icon" :style="{ background: p.color }">{{ p.abbr }}</span>
            {{ p.label }}登录
          </a-button>
        </div>
      </template>

      <div class="login-footer">
        <span>请联系管理员获取账号</span>
      </div>
    </div>

    <!-- 底部版权 -->
    <div class="copyright">
      &copy; 2026 数据中台 MVP &middot; 金融行业离线数据处理平台
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { IconUser, IconLock } from '@arco-design/web-vue/es/icon'
import { useUserStore } from '../stores/user'
import { adminGetSsoPublic } from '../api'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const flowBgRef = ref<HTMLElement>()

const SAVED_USERNAME_KEY = 'login_username'
const THEME_KEY = 'login_theme'

// 初始化主题：优先用保存的偏好，否则跟随系统
function getInitialTheme(): boolean {
  const saved = localStorage.getItem(THEME_KEY)
  if (saved) return saved === 'dark'
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

const isDark = ref(getInitialTheme())

const form = reactive({
  username: localStorage.getItem(SAVED_USERNAME_KEY) || '',
  password: '',
  remember: !!localStorage.getItem(SAVED_USERNAME_KEY),
})

const _ALL_PROVIDERS = [
  { provider: 'dingtalk', label: '钉钉', abbr: 'DD', color: '#1677FF' },
  { provider: 'feishu',   label: '飞书', abbr: 'FS', color: '#3370FF' },
  { provider: 'wecom',    label: '企微', abbr: 'WX', color: '#07C160' },
]
const enabledProviders = ref<typeof _ALL_PROVIDERS>([])

// 随机光斑
interface BlobDef { style: Record<string, string> }
const blobs = ref<BlobDef[]>([])

// 随机粒子
interface ParticleDef { style: Record<string, string> }
const particles = ref<ParticleDef[]>([])

function rand(min: number, max: number) {
  return Math.random() * (max - min) + min
}

function randInt(min: number, max: number) {
  return Math.floor(rand(min, max + 1))
}

function pick<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)]
}

function buildBlobs() {
  const colors = [
    ['rgba(0,150,255,0.42)', 'rgba(0,80,180,0.14)'],
    ['rgba(0,201,167,0.38)', 'rgba(0,122,107,0.12)'],
    ['rgba(0,180,220,0.35)', 'rgba(0,100,140,0.1)'],
    ['rgba(60,180,255,0.32)', 'rgba(30,100,180,0.09)'],
    ['rgba(0,220,180,0.35)', 'rgba(0,140,120,0.1)'],
    ['rgba(80,170,255,0.3)', 'rgba(40,100,180,0.08)'],
    ['rgba(0,200,200,0.32)', 'rgba(0,120,130,0.09)'],
  ]
  const anims = ['flowA', 'flowB', 'flowC', 'flowD', 'flowE']

  const list: BlobDef[] = []
  for (let i = 0; i < 18; i++) {
    const size = rand(25, 65)
    const [c1, c2] = pick(colors)
    const anim = pick(anims)
    const duration = rand(10, 22)
    const delay = rand(-15, 0)
    const top = rand(-20, 80)
    const left = rand(-20, 80)
    const borderR = rand(40, 60)

    list.push({
      style: {
        width: `${size}vmax`,
        height: `${size}vmax`,
        top: `${top}%`,
        left: `${left}%`,
        borderRadius: `${borderR}%`,
        background: `radial-gradient(circle, ${c1} 0%, ${c2} 40%, transparent 65%)`,
        animation: `${anim} ${duration}s ease-in-out infinite ${delay}s, pulse ${rand(4, 8)}s ease-in-out infinite ${rand(-4, 0)}s`,
        opacity: String(rand(0.3, 0.7)),
      },
    })
  }
  blobs.value = list
}

function buildParticles() {
  const list: ParticleDef[] = []
  for (let i = 0; i < 25; i++) {
    const size = rand(2, 5)
    const top = rand(0, 100)
    const left = rand(0, 100)
    const duration = rand(15, 40)
    const delay = rand(-20, 0)
    const driftX = rand(-30, 30)
    const driftY = rand(-30, 30)

    list.push({
      style: {
        width: `${size}px`,
        height: `${size}px`,
        top: `${top}%`,
        left: `${left}%`,
        opacity: String(rand(0.1, 0.4)),
        animation: `drift ${duration}s linear infinite ${delay}s, twinkle ${rand(3, 7)}s ease-in-out infinite ${rand(-5, 0)}s`,
        '--drift-x': `${driftX}vw`,
        '--drift-y': `${driftY}vh`,
      } as Record<string, string>,
    })
  }
  particles.value = list
}

function toggleTheme() {
  isDark.value = !isDark.value
  localStorage.setItem(THEME_KEY, isDark.value ? 'dark' : 'light')
}

async function loadSsoProviders() {
  try {
    const res: any = await adminGetSsoPublic()
    const enabledSet = new Set((res || []).map((c: any) => c.provider))
    enabledProviders.value = _ALL_PROVIDERS.filter(p => enabledSet.has(p.provider))
  } catch {
    enabledProviders.value = []
  }
}

function ssoLogin(provider: string) {
  window.location.href = `/api/auth/oauth/${provider}`
}

async function handleLogin() {
  loading.value = true
  try {
    await userStore.login(form.username, form.password)
    if (form.remember) {
      localStorage.setItem(SAVED_USERNAME_KEY, form.username)
    } else {
      localStorage.removeItem(SAVED_USERNAME_KEY)
    }
    Message.success('登录成功')
    router.push('/dashboard')
  } catch (e: any) {
    Message.error(e?.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  buildBlobs()
  buildParticles()
  loadSsoProviders()

  // 监听系统主题变化（仅在用户未手动选择时）
  const mq = window.matchMedia('(prefers-color-scheme: dark)')
  mq.addEventListener('change', (e) => {
    if (!localStorage.getItem(THEME_KEY)) {
      isDark.value = e.matches
    }
  })
})
</script>

<style scoped>
/* ========== 深色模式（默认） ========== */
.login-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: #0f2248;
  padding: 40px 20px;
}

/* 主题切换颜色过渡 */
.login-page,
.login-page * {
  transition: background-color 0.5s ease, border-color 0.5s ease, color 0.5s ease, box-shadow 0.5s ease, opacity 0.5s ease;
}

/* 排除背景动效元素（它们有自己的 animation） */
.flow-wheel,
.flow-glow,
.flow-blob,
.flow-particle,
.flow-lines,
.flow-noise {
  transition: none !important;
}

/* 排除需要保留原有交互 transition 的元素 */
.login-btn {
  transition: transform 0.3s ease, box-shadow 0.3s ease, background 0.3s ease !important;
}
.toggle-thumb {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), background 0.3s ease, box-shadow 0.3s ease !important;
}
.toggle-track {
  transition: background 0.3s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.3s ease, box-shadow 0.3s ease !important;
}
.theme-toggle svg {
  transition: none !important;
}

/* 流动背景层 */
.flow-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

/* 底层均匀光晕 */
.flow-glow {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 20% 30%, rgba(0, 150, 255, 0.2) 0%, transparent 50%),
    radial-gradient(ellipse at 70% 60%, rgba(0, 201, 167, 0.14) 0%, transparent 45%),
    radial-gradient(ellipse at 85% 25%, rgba(74, 159, 255, 0.16) 0%, transparent 45%),
    radial-gradient(ellipse at 40% 80%, rgba(0, 200, 200, 0.12) 0%, transparent 50%),
    radial-gradient(ellipse at 90% 80%, rgba(0, 120, 220, 0.1) 0%, transparent 45%);
  animation: glowShift 20s ease-in-out infinite alternate;
  pointer-events: none;
}

@keyframes glowShift {
  from { transform: translate(-3%, -2%) scale(1); }
  to   { transform: translate(3%, 2%) scale(1.1); }
}

/* 旋转色轮 */
.flow-wheel {
  position: absolute;
  width: 220vmax;
  height: 220vmax;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: conic-gradient(
    from 0deg,
    #0a1a35 0%,
    #1a3a6a 14%,
    #2B5AED 28%,
    #00C9A7 40%,
    #00b4d8 52%,
    #4a9fff 65%,
    #0d2e5a 80%,
    #0a1a35 100%
  );
  animation: wheelSpin 25s linear infinite;
  opacity: 0.75;
  filter: blur(80px);
}

@keyframes wheelSpin {
  from { transform: translate(-50%, -50%) rotate(0deg); }
  to   { transform: translate(-50%, -50%) rotate(360deg); }
}

/* 光斑 */
.flow-blob {
  position: absolute;
  filter: blur(50px);
  will-change: transform, opacity;
  pointer-events: none;
}

/* 粒子 */
.flow-particle {
  position: absolute;
  border-radius: 50%;
  background: rgba(150, 190, 255, 0.6);
  will-change: transform, opacity;
  pointer-events: none;
}

/* 5 种流动路径 */
@keyframes flowA {
  0%, 100% { transform: translate(0, 0) scale(1); }
  20%      { transform: translate(12vw, 8vh) scale(1.25); }
  40%      { transform: translate(-6vw, 18vh) scale(0.85); }
  60%      { transform: translate(18vw, -10vh) scale(1.15); }
  80%      { transform: translate(-10vw, -6vh) scale(1.05); }
}
@keyframes flowB {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25%      { transform: translate(-15vw, -12vh) scale(1.2); }
  50%      { transform: translate(8vw, -20vh) scale(1.35); }
  75%      { transform: translate(-18vw, 8vh) scale(0.9); }
}
@keyframes flowC {
  0%, 100% { transform: translate(0, 0) scale(1) rotate(0deg); }
  33%      { transform: translate(-12vw, 15vh) scale(1.3) rotate(20deg); }
  66%      { transform: translate(10vw, -8vh) scale(0.95) rotate(-15deg); }
}
@keyframes flowD {
  0%, 100% { transform: translate(0, 0) scale(1); }
  20%      { transform: translate(20vw, 5vh) scale(1.1); }
  50%      { transform: translate(-5vw, 25vh) scale(1.4); }
  80%      { transform: translate(15vw, -15vh) scale(0.8); }
}
@keyframes flowE {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25%      { transform: translate(-8vw, -18vh) scale(1.25); }
  50%      { transform: translate(20vw, 10vh) scale(1.1); }
  75%      { transform: translate(-15vw, 5vh) scale(1.3); }
}

/* 脉冲闪烁 */
@keyframes pulse {
  0%, 100% { opacity: 0.5; }
  50%      { opacity: 0.9; }
}

/* 粒子漂移 */
@keyframes drift {
  from { transform: translate(0, 0); }
  to   { transform: translate(var(--drift-x, 20vw), var(--drift-y, -20vh)); }
}
@keyframes twinkle {
  0%, 100% { opacity: 0.1; }
  50%      { opacity: 0.5; }
}

/* 流动线条网格 */
.flow-lines {
  position: absolute;
  inset: 0;
  background:
    repeating-linear-gradient(
      90deg,
      transparent,
      transparent 100px,
      rgba(79, 140, 255, 0.025) 100px,
      rgba(79, 140, 255, 0.025) 101px
    ),
    repeating-linear-gradient(
      0deg,
      transparent,
      transparent 100px,
      rgba(0, 201, 167, 0.015) 100px,
      rgba(0, 201, 167, 0.015) 101px
    );
  animation: lineDrift 40s linear infinite;
  pointer-events: none;
}

@keyframes lineDrift {
  from { transform: translate(0, 0); }
  to   { transform: translate(100px, 100px); }
}

/* 噪点纹理 */
.flow-noise {
  position: absolute;
  inset: 0;
  opacity: 0.035;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  pointer-events: none;
}

/* 登录卡片 - 玻璃拟态 */
.login-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 400px;
  padding: 40px;
  border-radius: 16px;
  background: rgba(5, 10, 22, 0.6);
  backdrop-filter: blur(48px) saturate(1.2);
  border: 1px solid rgba(255, 255, 255, 0.22);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.4),
    inset 0 1px 1px rgba(255, 255, 255, 0.1);
  animation: cardIn 0.5s ease-out;
}

@keyframes cardIn {
  from { opacity: 0; transform: translateY(16px) scale(0.98); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

/* 主题切换按钮 */
.theme-toggle {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(8px);
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  z-index: 2;
}
.theme-toggle:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-logo {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.login-title {
  font-size: 24px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 4px;
}

.login-subtitle {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
  letter-spacing: 1px;
}

.login-btn {
  height: 44px;
  font-size: 15px;
  font-weight: 500;
  background: linear-gradient(135deg, #00a8e8, #0077b6) !important;
  border: none !important;
  border-radius: 8px !important;
  letter-spacing: 4px;
  transition: all 0.3s ease;
}
.login-btn:hover {
  background: linear-gradient(135deg, #00b4d8, #0096c7) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 168, 232, 0.35);
}

/* 记住用户名行 */
.remember-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 液态玻璃 toggle */
.glass-toggle {
  position: relative;
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  flex-shrink: 0;
}
.glass-toggle input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}
.toggle-track {
  width: 36px;
  height: 20px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(8px) saturate(1.2);
  position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.2);
}
.toggle-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.7);
  box-shadow:
    0 1px 3px rgba(0, 0, 0, 0.3),
    0 0 0 1px rgba(255, 255, 255, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.glass-toggle input:checked + .toggle-track {
  background: rgba(0, 180, 240, 0.45);
  border-color: rgba(0, 200, 255, 0.7);
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1), 0 0 12px rgba(0, 200, 255, 0.35);
}
.glass-toggle input:checked + .toggle-track .toggle-thumb {
  transform: translateX(16px);
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
}
.glass-toggle input:disabled + .toggle-track {
  opacity: 0.4;
  cursor: not-allowed;
}

.remember-label {
  color: rgba(255, 255, 255, 0.75);
  font-size: 13px;
  white-space: nowrap;
}

.forget-hint {
  margin-left: 16px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  flex-shrink: 0;
  white-space: nowrap;
}

.login-footer {
  text-align: center;
  color: rgba(255, 255, 255, 0.45);
  font-size: 12px;
  margin-top: 16px;
}

.sso-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 16px 0;
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
}
.sso-divider::before,
.sso-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: rgba(255, 255, 255, 0.12);
}

.sso-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sso-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 38px;
  border-radius: 8px !important;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
}
.sso-btn:hover {
  background: rgba(255, 255, 255, 0.1) !important;
}

.sso-icon {
  width: 22px;
  height: 22px;
  border-radius: 5px;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.copyright {
  position: relative;
  z-index: 1;
  margin-top: 32px;
  color: rgba(255, 255, 255, 0.3);
  font-size: 12px;
  letter-spacing: 0.5px;
  text-align: center;
}

/* Arco 样式覆盖 - 深色主题 */
:deep(.arco-form-item-label) {
  color: rgba(255, 255, 255, 0.8) !important;
  font-size: 13px !important;
}
:deep(.arco-input-wrapper),
:deep(.arco-input-password) {
  background: rgba(255, 255, 255, 0.1) !important;
  border: 1px solid rgba(255, 255, 255, 0.18) !important;
  border-radius: 8px !important;
}
:deep(.arco-input-wrapper:hover),
:deep(.arco-input-password:hover) {
  border-color: rgba(255, 255, 255, 0.3) !important;
  background: rgba(255, 255, 255, 0.14) !important;
}
:deep(.arco-input-wrapper input),
:deep(.arco-input-password input) {
  color: #fff !important;
}
:deep(.arco-input-wrapper .arco-input-prefix),
:deep(.arco-input-password .arco-input-prefix) {
  color: rgba(255, 255, 255, 0.7) !important;
}
:deep(.arco-input-wrapper input::placeholder),
:deep(.arco-input-password input::placeholder) {
  color: rgba(255, 255, 255, 0.55) !important;
}

/* ========== 浅色模式覆盖 ========== */
.login-page.light-mode {
  background: #e8edf3;
}

.light-mode .flow-glow {
  opacity: 0.35;
}

.light-mode .flow-wheel {
  opacity: 0.25;
}

.light-mode .flow-blob {
  opacity: 0.4 !important;
}

.light-mode .flow-noise {
  opacity: 0.015;
}

.light-mode .login-card {
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(24px) saturate(1.1);
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.08),
    inset 0 1px 1px rgba(255, 255, 255, 0.5);
}

.light-mode .theme-toggle {
  border-color: rgba(0, 0, 0, 0.12);
  background: rgba(0, 0, 0, 0.04);
  color: rgba(0, 0, 0, 0.5);
}
.light-mode .theme-toggle:hover {
  background: rgba(0, 0, 0, 0.08);
  color: rgba(0, 0, 0, 0.7);
}

.light-mode .login-title {
  color: #1d2129;
}

.light-mode .login-subtitle {
  color: rgba(0, 0, 0, 0.45);
}

.light-mode .toggle-track {
  background: rgba(0, 0, 0, 0.06);
  border-color: rgba(0, 0, 0, 0.12);
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.08);
}
.light-mode .toggle-thumb {
  background: rgba(0, 0, 0, 0.45);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}
.light-mode .glass-toggle input:checked + .toggle-track {
  background: rgba(0, 168, 232, 0.35);
  border-color: rgba(0, 168, 232, 0.55);
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05), 0 0 10px rgba(0, 168, 232, 0.15);
}
.light-mode .glass-toggle input:checked + .toggle-track .toggle-thumb {
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

.light-mode .remember-label {
  color: rgba(0, 0, 0, 0.65);
}

.light-mode .forget-hint {
  color: rgba(0, 0, 0, 0.4);
}

.light-mode .login-footer {
  color: rgba(0, 0, 0, 0.35);
}

.light-mode .sso-divider {
  color: rgba(0, 0, 0, 0.4);
}
.light-mode .sso-divider::before,
.light-mode .sso-divider::after {
  background: rgba(0, 0, 0, 0.08);
}

.light-mode .sso-btn {
  color: rgba(0, 0, 0, 0.7);
  background: rgba(0, 0, 0, 0.03) !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
}
.light-mode .sso-btn:hover {
  background: rgba(0, 0, 0, 0.06) !important;
}

.light-mode .copyright {
  color: rgba(0, 0, 0, 0.3);
}

.light-mode :deep(.arco-form-item-label) {
  color: rgba(0, 0, 0, 0.6) !important;
}
.light-mode :deep(.arco-input-wrapper),
.light-mode :deep(.arco-input-password) {
  background: rgba(0, 0, 0, 0.03) !important;
  border: 1px solid rgba(0, 0, 0, 0.1) !important;
}
.light-mode :deep(.arco-input-wrapper:hover),
.light-mode :deep(.arco-input-password:hover) {
  border-color: rgba(0, 0, 0, 0.18) !important;
  background: rgba(0, 0, 0, 0.05) !important;
}
.light-mode :deep(.arco-input-wrapper input),
.light-mode :deep(.arco-input-password input) {
  color: #1d2129 !important;
}
.light-mode :deep(.arco-input-wrapper .arco-input-prefix),
.light-mode :deep(.arco-input-password .arco-input-prefix) {
  color: rgba(0, 0, 0, 0.45) !important;
}
.light-mode :deep(.arco-input-wrapper input::placeholder),
.light-mode :deep(.arco-input-password input::placeholder) {
  color: rgba(0, 0, 0, 0.35) !important;
}

@media (max-width: 480px) {
  .login-card {
    padding: 32px 24px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .flow-wheel,
  .flow-glow,
  .flow-blob,
  .flow-particle,
  .flow-lines,
  .login-card,
  .login-btn {
    animation: none !important;
  }
}
</style>
