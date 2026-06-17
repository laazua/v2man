<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import { useSiteName } from '../api/site'

const route = useRoute()
const router = useRouter()
const siteName = useSiteName()

const step = ref(route.query.uid ? 'reset' : 'email')
const email = ref('')
const password = ref('')
const confirmPwd = ref('')
const showPwd = ref(false)
const showConfirm = ref(false)
const msg = ref('')
const error = ref('')

async function sendReset() {
  msg.value = ''
  error.value = ''
  try {
    const baseUrl = window.location.origin
    await api.post('/auth/password-reset/', { email: email.value, base_url: baseUrl })
    msg.value = '重置链接已发送，请检查您的邮箱'
  } catch (e: any) {
    error.value = e.response?.data?.error || '发送失败'
  }
}

async function confirmReset() {
  error.value = ''
  if (password.value !== confirmPwd.value) {
    error.value = '两次密码不一致'
    return
  }
  if (password.value.length < 6) {
    error.value = '密码至少6位'
    return
  }
  try {
    await api.post('/auth/password-reset/confirm/', {
      uid: route.query.uid,
      token: route.query.token,
      password: password.value,
    })
    msg.value = '密码已重置，即将跳转登录'
    setTimeout(() => router.push('/login'), 2000)
  } catch (e: any) {
    error.value = e.response?.data?.error || '重置失败'
  }
}
</script>

<template>
  <div class="page">
    <div class="card">
      <h1>{{ siteName }}</h1>
      <p class="subtitle">{{ step === 'email' ? '重置密码' : '设置新密码' }}</p>

      <div v-if="step === 'email'">
        <div class="form-group">
          <label>注册邮箱</label>
          <input v-model="email" type="email" placeholder="请输入注册时使用的邮箱" />
        </div>
        <p v-if="msg" class="success">{{ msg }}</p>
        <p v-if="error" class="error">{{ error }}</p>
        <button @click="sendReset" class="btn-primary">发送重置链接</button>
        <p class="link"><router-link to="/login">返回登录</router-link></p>
      </div>

      <div v-if="step === 'reset'">
        <div class="form-group">
          <label>新密码</label>
          <div class="pwd-wrap">
            <input v-model="password" :type="showPwd ? 'text' : 'password'" placeholder="至少6位" />
            <button type="button" @click="showPwd = !showPwd" class="eye-btn">{{ showPwd ? '🙈' : '👁️' }}</button>
          </div>
        </div>
        <div class="form-group">
          <label>确认密码</label>
          <div class="pwd-wrap">
            <input v-model="confirmPwd" :type="showConfirm ? 'text' : 'password'" placeholder="再次输入新密码" />
            <button type="button" @click="showConfirm = !showConfirm" class="eye-btn">{{ showConfirm ? '🙈' : '👁️' }}</button>
          </div>
        </div>
        <p v-if="msg" class="success">{{ msg }}</p>
        <p v-if="error" class="error">{{ error }}</p>
        <button @click="confirmReset" class="btn-primary">重置密码</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { display: flex; align-items: center; justify-content: center; min-height: 100vh; background: var(--bg-primary); }
.card { background: var(--bg-card); backdrop-filter: blur(12px); padding: 2.5rem; border-radius: var(--radius); border: 1px solid var(--border); width: 400px; box-shadow: var(--shadow); }
h1 { text-align: center; margin-bottom: 0.25rem; font-size: 1.5rem; }
.subtitle { text-align: center; color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 1.5rem; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.25rem; }
.form-group input { width: 100%; padding: 0.65rem 0.75rem; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--bg-primary); color: var(--text-primary); outline: none; font-size: 0.9rem; }
.form-group input:focus { border-color: var(--accent); }
.pwd-wrap { position: relative; }
.pwd-wrap input { padding-right: 2.5rem; }
.eye-btn { position: absolute; right: 0.5rem; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; font-size: 1rem; padding: 0.25rem; color: var(--text-muted); line-height: 1; }
.eye-btn:hover { transform: translateY(-50%) scale(1.1); }
.btn-primary { width: 100%; padding: 0.75rem; background: var(--accent-gradient); color: #fff; border: none; border-radius: var(--radius-sm); cursor: pointer; font-size: 0.9rem; font-weight: 500; margin-top: 0.5rem; }
.btn-primary:hover { transform: translateY(-1px); }
.success { color: var(--success); font-size: 0.85rem; text-align: center; margin-bottom: 0.5rem; }
.error { color: var(--danger); font-size: 0.85rem; text-align: center; margin-bottom: 0.5rem; }
.link { text-align: center; margin-top: 1.25rem; font-size: 0.85rem; }
.link a { color: var(--accent); text-decoration: none; }
</style>
