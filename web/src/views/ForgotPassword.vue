<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import { useSiteName } from '../api/site'

const route = useRoute()
const router = useRouter()
const siteName = useSiteName()

const step = ref((route.name === 'ResetPassword' && !route.query.uid) ? 'invalid' : route.query.uid ? 'reset' : 'email')
const email = ref('')
const password = ref('')
const confirmPwd = ref('')
const showPwd = ref(false)
const showConfirm = ref(false)
const msg = ref('')
const error = ref('')
const loading = ref(false)
const timers: ReturnType<typeof setTimeout>[] = []
onUnmounted(() => timers.forEach(clearTimeout))

async function sendReset() {
  if (loading.value) return
  loading.value = true
  msg.value = ''
  error.value = ''
  try {
    const baseUrl = window.location.origin
    await api.post('/auth/password-reset/', { email: email.value, base_url: baseUrl })
    msg.value = '重置链接已发送，请检查您的邮箱'
  } catch (e: any) {
    error.value = e.response?.data?.error || '发送失败'
  } finally {
    loading.value = false
  }
}

async function confirmReset() {
  if (loading.value) return
  loading.value = true
  error.value = ''
  if (password.value !== confirmPwd.value) {
    error.value = '两次密码不一致'
    loading.value = false
    return
  }
  if (password.value.length < 6) {
    error.value = '密码至少6位'
    loading.value = false
    return
  }
  try {
    await api.post('/auth/password-reset/confirm/', {
      uid: route.query.uid,
      token: route.query.token,
      password: password.value,
    })
    msg.value = '密码已重置，即将跳转登录'
    const t = setTimeout(() => router.push('/login'), 2000)
    timers.push(t)
  } catch (e: any) {
    error.value = e.response?.data?.error || '重置失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page">
    <div class="bg">
      <div class="sky-gradient"></div>
      <svg class="butterfly butterfly-1" viewBox="0 0 80 60" fill="none">
        <path d="M40 30 C20 10 5 15 5 30 C5 45 20 50 40 30 Z" fill="url(#bf1)" opacity="0.35"/>
        <path d="M40 30 C60 10 75 15 75 30 C75 45 60 50 40 30 Z" fill="url(#bf2)" opacity="0.35"/>
        <path d="M40 30 C28 18 15 22 15 30 C15 38 28 42 40 30 Z" fill="url(#bf1)" opacity="0.5"/>
        <path d="M40 30 C52 18 65 22 65 30 C65 38 52 42 40 30 Z" fill="url(#bf2)" opacity="0.5"/>
        <line x1="40" y1="30" x2="40" y2="55" stroke="url(#bf3)" stroke-width="1.5" opacity="0.3"/>
        <circle cx="40" cy="28" r="2" fill="url(#bf3)" opacity="0.2"/>
        <defs>
          <linearGradient id="bf1" x1="5" y1="15" x2="40" y2="30"><stop offset="0%" stop-color="#3b82f6"/><stop offset="100%" stop-color="#06b6d4"/></linearGradient>
          <linearGradient id="bf2" x1="75" y1="15" x2="40" y2="30"><stop offset="0%" stop-color="#8b5cf6"/><stop offset="100%" stop-color="#3b82f6"/></linearGradient>
          <linearGradient id="bf3" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#3b82f6"/><stop offset="100%" stop-color="#8b5cf6"/></linearGradient>
        </defs>
      </svg>
      <svg class="butterfly butterfly-2" viewBox="0 0 80 60" fill="none">
        <path d="M40 30 C20 10 5 15 5 30 C5 45 20 50 40 30 Z" fill="url(#bf1)" opacity="0.2"/>
        <path d="M40 30 C60 10 75 15 75 30 C75 45 60 50 40 30 Z" fill="url(#bf2)" opacity="0.2"/>
        <path d="M40 30 C28 18 15 22 15 30 C15 38 28 42 40 30 Z" fill="url(#bf1)" opacity="0.3"/>
        <path d="M40 30 C52 18 65 22 65 30 C65 38 52 42 40 30 Z" fill="url(#bf2)" opacity="0.3"/>
        <line x1="40" y1="30" x2="40" y2="55" stroke="url(#bf3)" stroke-width="1.5" opacity="0.2"/>
        <circle cx="40" cy="28" r="2" fill="url(#bf3)" opacity="0.15"/>
      </svg>
      <svg class="butterfly butterfly-3" viewBox="0 0 80 60" fill="none">
        <path d="M40 30 C20 10 5 15 5 30 C5 45 20 50 40 30 Z" fill="url(#bf1)" opacity="0.12"/>
        <path d="M40 30 C60 10 75 15 75 30 C75 45 60 50 40 30 Z" fill="url(#bf2)" opacity="0.12"/>
        <line x1="40" y1="30" x2="40" y2="55" stroke="url(#bf3)" stroke-width="1.5" opacity="0.1"/>
      </svg>
      <div class="cloud cloud-1"></div>
      <div class="cloud cloud-2"></div>
      <div class="cloud cloud-3"></div>
    </div>
    <div class="card">
      <div class="logo-area">
        <div class="v-badge">V</div>
        <h1>{{ siteName }}</h1>
        <p class="subtitle">{{ step === 'email' ? '重置密码' : '设置新密码' }}</p>
      </div>

      <div v-if="step === 'email'">
        <div class="input-group">
          <label>注册邮箱</label>
          <div class="input-wrap">
            <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="2" y="4" width="20" height="16" rx="2"/>
              <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
            </svg>
            <input v-model="email" type="email" placeholder="请输入注册时使用的邮箱" />
          </div>
        </div>
        <p v-if="msg" class="success">{{ msg }}</p>
        <p v-if="error" class="error">{{ error }}</p>
        <button @click="sendReset" class="btn-primary" :class="{ loading }" :disabled="loading">
          <span v-if="loading" class="spinner"></span>
          <span>{{ loading ? '发送中...' : '发送重置链接' }}</span>
        </button>
        <p class="link"><router-link to="/login">返回登录</router-link></p>
      </div>

      <div v-if="step === 'invalid'">
        <p class="error">无效的重置链接，请重新申请。</p>
        <p class="link"><router-link to="/forgot-password">重新申请</router-link></p>
      </div>

      <div v-else-if="step === 'reset'">
        <div class="input-group">
          <label>新密码</label>
          <div class="input-wrap">
            <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            <input v-model="password" :type="showPwd ? 'text' : 'password'" placeholder="至少6位" />
            <button type="button" @click="showPwd = !showPwd" class="eye-btn">
              <svg v-if="showPwd" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
            </button>
          </div>
        </div>
        <div class="input-group">
          <label>确认密码</label>
          <div class="input-wrap">
            <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            <input v-model="confirmPwd" :type="showConfirm ? 'text' : 'password'" placeholder="再次输入新密码" />
            <button type="button" @click="showConfirm = !showConfirm" class="eye-btn">
              <svg v-if="showConfirm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                <line x1="1" y1="1" x2="23" y2="23"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
            </button>
          </div>
        </div>
        <p v-if="msg" class="success">{{ msg }}</p>
        <p v-if="error" class="error">{{ error }}</p>
        <button @click="confirmReset" class="btn-primary" :class="{ loading }" :disabled="loading">
          <span v-if="loading" class="spinner"></span>
          <span>{{ loading ? '重置中...' : '重置密码' }}</span>
        </button>
        <p class="link"><router-link to="/login">返回登录</router-link></p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(180deg, #dbeafe 0%, #eff6ff 30%, #f0fdf4 70%, #fefce8 100%);
  position: relative;
  overflow: hidden;
}

.bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.sky-gradient {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 20% 30%, rgba(147, 197, 253, 0.3) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, rgba(167, 139, 250, 0.15) 0%, transparent 40%),
    radial-gradient(ellipse at 50% 80%, rgba(134, 239, 172, 0.1) 0%, transparent 40%);
}

.butterfly {
  position: absolute;
  opacity: 0.6;
}

.butterfly-1 {
  width: 100px;
  top: 12%;
  left: 10%;
  animation: fly1 18s ease-in-out infinite;
}

.butterfly-2 {
  width: 70px;
  top: 25%;
  right: 15%;
  animation: fly2 22s ease-in-out infinite;
}

.butterfly-3 {
  width: 50px;
  top: 8%;
  left: 45%;
  animation: fly1 25s ease-in-out infinite 3s;
}

@keyframes fly1 {
  0%, 100% { transform: translate(0, 0) scale(1) rotate(0deg); }
  25% { transform: translate(80px, -30px) scale(1.05) rotate(3deg); }
  50% { transform: translate(40px, 20px) scale(0.95) rotate(-2deg); }
  75% { transform: translate(120px, -10px) scale(1.02) rotate(5deg); }
}

@keyframes fly2 {
  0%, 100% { transform: translate(0, 0) scale(1) rotate(0deg); }
  25% { transform: translate(-60px, 40px) scale(0.95) rotate(-4deg); }
  50% { transform: translate(-100px, -20px) scale(1.05) rotate(2deg); }
  75% { transform: translate(-30px, 30px) scale(1.02) rotate(-3deg); }
}

.cloud {
  position: absolute;
  background: rgba(255, 255, 255, 0.6);
  border-radius: 100px;
  filter: blur(2px);
}

.cloud::before, .cloud::after {
  content: '';
  position: absolute;
  background: inherit;
  border-radius: 50%;
}

.cloud-1 {
  width: 200px;
  height: 30px;
  top: 18%;
  left: -40px;
  animation: cloudDrift 30s linear infinite;
}

.cloud-1::before {
  width: 60px;
  height: 60px;
  top: -30px;
  left: 30px;
}

.cloud-1::after {
  width: 80px;
  height: 50px;
  top: -20px;
  left: 80px;
}

.cloud-2 {
  width: 160px;
  height: 25px;
  top: 10%;
  left: -60px;
  animation: cloudDrift 40s linear infinite 5s;
}

.cloud-2::before {
  width: 50px;
  height: 50px;
  top: -25px;
  left: 20px;
}

.cloud-2::after {
  width: 65px;
  height: 40px;
  top: -18px;
  left: 65px;
}

.cloud-3 {
  width: 140px;
  height: 22px;
  top: 22%;
  left: -30px;
  animation: cloudDrift 35s linear infinite 10s;
}

.cloud-3::before {
  width: 40px;
  height: 40px;
  top: -22px;
  left: 15px;
}

.cloud-3::after {
  width: 55px;
  height: 35px;
  top: -16px;
  left: 55px;
}

@keyframes cloudDrift {
  0% { transform: translateX(0); }
  100% { transform: translateX(calc(100vw + 200px)); }
}

.card {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: 2.5rem;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  width: 380px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.06), 0 1px 4px rgba(0, 0, 0, 0.04);
}

.logo-area {
  text-align: center;
  margin-bottom: 2rem;
}

.v-badge {
  width: 48px;
  height: 48px;
  margin: 0 auto 1rem;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 1.3rem;
  font-weight: 800;
  font-family: 'Courier New', monospace;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.2);
}

h1 {
  color: #1e293b;
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 0.4rem;
}

.subtitle {
  color: #64748b;
  font-size: 0.85rem;
  margin: 0;
  letter-spacing: 0.08em;
}

.input-group {
  margin-bottom: 1rem;
}

.input-group label {
  display: block;
  color: #475569;
  font-size: 0.8rem;
  font-weight: 600;
  margin-bottom: 0.4rem;
}

.input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 0.85rem;
  width: 18px;
  height: 18px;
  color: #94a3b8;
  z-index: 1;
  pointer-events: none;
}

.input-wrap input {
  width: 100%;
  padding: 0.75rem 1rem 0.75rem 2.75rem;
  border: 1.5px solid #e2e8f0;
  border-radius: 12px;
  background: #fff;
  color: #1e293b;
  outline: none;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.input-wrap input::placeholder {
  color: #94a3b8;
}

.input-wrap input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.08);
}

.eye-btn {
  position: absolute;
  right: 0.65rem;
  background: none;
  border: none;
  cursor: pointer;
  width: 20px;
  height: 20px;
  padding: 0;
  color: #94a3b8;
  transition: color 0.2s;
  z-index: 1;
  line-height: 1;
}

.eye-btn:hover {
  color: #64748b;
  box-shadow: none;
  transform: none;
}

.eye-btn svg {
  width: 100%;
  height: 100%;
}

.error {
  color: #ef4444;
  font-size: 0.8rem;
  margin: 0 0 0.75rem;
  padding: 0.5rem 0.75rem;
  background: #fef2f2;
  border-radius: 10px;
  border: 1px solid #fecaca;
}

.success {
  color: #16a34a;
  font-size: 0.8rem;
  margin: 0 0 0.75rem;
  padding: 0.5rem 0.75rem;
  background: #f0fdf4;
  border-radius: 10px;
  border: 1px solid #bbf7d0;
}

.btn-primary {
  width: 100%;
  padding: 0.8rem;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  color: #fff;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 600;
  transition: all 0.25s;
  letter-spacing: 0.02em;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.25);
}

.btn-primary:active:not(:disabled) {
  transform: translateY(0);
}

.btn-primary:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading {
  cursor: not-allowed;
  opacity: 0.7;
}

.link {
  text-align: center;
  margin-top: 1.5rem;
  color: #64748b;
  font-size: 0.85rem;
}

.link a {
  color: #3b82f6;
  text-decoration: none;
  font-weight: 500;
}

.link a:hover {
  text-decoration: underline;
}
</style>
