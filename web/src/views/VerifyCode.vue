<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../api'

const router = useRouter()
const route = useRoute()
const email = ref((route.query.email as string) || '')
const code = ref('')
const error = ref('')
const success = ref('')
const loading = ref(false)
const resendLoading = ref(false)
const cooldown = ref(0)
let timer: ReturnType<typeof setInterval> | null = null
let redirectTimer: ReturnType<typeof setTimeout> | null = null

onMounted(() => {
  if (!email.value) {
    error.value = '缺少邮箱信息，请重新注册'
  }
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (redirectTimer) clearTimeout(redirectTimer)
})

function startCooldown() {
  cooldown.value = 60
  timer = setInterval(() => {
    cooldown.value--
    if (cooldown.value <= 0) {
      if (timer) clearInterval(timer)
    }
  }, 1000)
}

async function activate() {
  if (!code.value || code.value.length !== 6) return
  loading.value = true
  error.value = ''
  success.value = ''
  try {
    await api.post('/auth/activate/', { email: email.value, code: code.value })
    success.value = '邮箱验证成功！即将跳转登录页...'
    redirectTimer = setTimeout(() => router.push('/login'), 2000)
  } catch (e: any) {
    error.value = e.response?.data?.error || '验证失败'
  } finally {
    loading.value = false
  }
}

async function resend() {
  if (cooldown.value > 0) return
  resendLoading.value = true
  error.value = ''
  try {
    await api.post('/auth/verification-code/resend/', { email: email.value })
    startCooldown()
    error.value = ''
  } catch (e: any) {
    error.value = e.response?.data?.error || '发送失败'
  } finally {
    resendLoading.value = false
  }
}
</script>

<template>
  <div class="verify-page">
    <div class="verify-card">
      <div class="icon-area">
        <div class="mail-icon">✉</div>
      </div>
      <h1>验证邮箱</h1>
      <p class="desc">验证码已发送至 <strong>{{ email }}</strong></p>
      <form @submit.prevent="activate">
        <div class="code-inputs">
          <input
            v-model="code"
            type="text"
            maxlength="6"
            placeholder="输入验证码"
            class="code-input"
            autocomplete="one-time-code"
            inputmode="numeric"
            pattern="[0-9]*"
          />
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <p v-if="success" class="success">{{ success }}</p>
        <button type="submit" :disabled="loading || code.length !== 6" class="verify-btn">
          {{ loading ? '验证中...' : '验证' }}
        </button>
      </form>
      <p class="resend">
        <button
          @click="resend"
          :disabled="resendLoading || cooldown > 0"
          class="resend-btn"
        >
          {{ cooldown > 0 ? `重新发送 (${cooldown}s)` : '重新发送验证码' }}
        </button>
      </p>
      <p class="link"><router-link to="/login">去登录</router-link></p>
    </div>
  </div>
</template>

<style scoped>
.verify-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(180deg, #dbeafe 0%, #eff6ff 30%, #f0fdf4 70%, #fefce8 100%);
}
.verify-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  padding: 2.5rem;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  width: 380px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.06);
  text-align: center;
}
.icon-area { margin-bottom: 1rem; }
.mail-icon {
  width: 60px;
  height: 60px;
  margin: 0 auto;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: #fff;
}
h1 { color: #1e293b; font-size: 1.5rem; font-weight: 700; margin: 0 0 0.5rem; }
.desc { color: #64748b; font-size: 0.9rem; margin: 0 0 1.5rem; }
.desc strong { color: #1e293b; }
.code-inputs { margin-bottom: 1rem; }
.code-input {
  width: 100%;
  padding: 0.8rem 1rem;
  border: 1.5px solid #e2e8f0;
  border-radius: 12px;
  font-size: 1.5rem;
  text-align: center;
  letter-spacing: 0.5em;
  outline: none;
  transition: border-color 0.2s;
}
.code-input:focus { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.08); }
.error { color: #ef4444; font-size: 0.8rem; margin: 0 0 0.75rem; }
.success { color: #22c55e; font-size: 0.8rem; margin: 0 0 0.75rem; }
.verify-btn {
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
}
.verify-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 8px 24px rgba(59,130,246,0.25); }
.verify-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.resend { margin-top: 1rem; }
.resend-btn {
  background: none;
  border: none;
  color: #3b82f6;
  cursor: pointer;
  font-size: 0.85rem;
  text-decoration: underline;
}
.resend-btn:disabled { color: #94a3b8; cursor: not-allowed; text-decoration: none; }
.link { margin-top: 1rem; }
.link a { color: #3b82f6; text-decoration: none; font-size: 0.85rem; }
</style>
