<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { useSiteName } from '../api/site'

const router = useRouter()
const siteName = useSiteName()

const profile = ref({ username: '', email: '', balance: 0, is_staff: false })
const isDark = ref(true)
const sidebarCollapsed = ref(false)
const showSettings = ref(false)
const showOldPwd = ref(false)
const showNewPwd = ref(false)
const settingsForm = ref({ email: '', old_password: '', new_password: '' })
const settingsMsg = ref('')

onMounted(async () => {
  const saved = localStorage.getItem('theme')
  if (saved) {
    isDark.value = saved === 'dark'
  } else {
    isDark.value = !window.matchMedia('(prefers-color-scheme: light)').matches
  }
  applyTheme()
  sidebarCollapsed.value = localStorage.getItem('sidebar') === 'collapsed'
  try {
    const { data } = await api.get('/auth/profile/')
    profile.value = { username: data.username, email: data.email, balance: data.balance || 0, is_staff: data.is_staff }
  } catch {
    router.push('/login')
  }
})

function toggleTheme() {
  isDark.value = !isDark.value
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  applyTheme()
}

function applyTheme() {
  document.documentElement.classList.toggle('light', !isDark.value)
}

function logout() {
  localStorage.clear()
  router.push('/login')
}

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('sidebar', sidebarCollapsed.value ? 'collapsed' : '')
}

function openSettings() {
  settingsForm.value.email = profile.value.email
  settingsForm.value.old_password = ''
  settingsForm.value.new_password = ''
  settingsMsg.value = ''
  showSettings.value = true
}

async function saveSettings() {
  settingsMsg.value = ''
  try {
    const payload: any = {}
    if (settingsForm.value.email !== profile.value.email) payload.email = settingsForm.value.email
    if (settingsForm.value.new_password) {
      payload.old_password = settingsForm.value.old_password
      payload.new_password = settingsForm.value.new_password
    }
    if (Object.keys(payload).length === 0) { showSettings.value = false; return }
    await api.patch('/auth/profile/', payload)
    profile.value.email = settingsForm.value.email
    settingsMsg.value = '保存成功'
    setTimeout(() => { showSettings.value = false }, 1000)
  } catch (e: any) {
    settingsMsg.value = e.response?.data?.error || '保存失败'
  }
}
</script>

<template>
  <div class="app-layout">
    <header class="top-header">
      <div class="header-left">
        <span class="logo">{{ siteName }}</span>
      </div>
      <div class="header-right">
        <span class="balance">¥{{ (profile.balance / 100).toFixed(2) }}</span>
        <button @click="toggleTheme" class="btn-theme" :title="isDark ? '切换白天模式' : '切换黑夜模式'">
          <span v-if="isDark">☀️</span>
          <span v-else>🌙</span>
        </button>
        <div class="avatar" @click="openSettings" :title="profile.username">{{ profile.username.charAt(0).toUpperCase() }}</div>
        <button @click="logout" class="btn-logout">退出</button>
      </div>
    </header>

    <div v-if="showSettings" class="modal-overlay" @click.self="showSettings = false">
      <div class="modal">
        <h3>个人设置</h3>
        <div class="form-group">
          <label>邮箱</label>
          <input v-model="settingsForm.email" type="email" />
        </div>
        <div class="form-group">
          <label>当前密码</label>
          <div class="pwd-wrap">
            <input v-model="settingsForm.old_password" :type="showOldPwd ? 'text' : 'password'" placeholder="修改密码时必填" />
            <button type="button" @click="showOldPwd = !showOldPwd" class="eye-btn">{{ showOldPwd ? '🙈' : '👁️' }}</button>
          </div>
        </div>
        <div class="form-group">
          <label>新密码</label>
          <div class="pwd-wrap">
            <input v-model="settingsForm.new_password" :type="showNewPwd ? 'text' : 'password'" placeholder="留空不修改" />
            <button type="button" @click="showNewPwd = !showNewPwd" class="eye-btn">{{ showNewPwd ? '🙈' : '👁️' }}</button>
          </div>
        </div>
        <p v-if="settingsMsg" :class="['msg', settingsMsg === '保存成功' ? 'success' : 'error']">{{ settingsMsg }}</p>
        <div class="form-actions">
          <button @click="showSettings = false" class="btn-secondary">取消</button>
          <button @click="saveSettings" class="btn-primary">保存</button>
        </div>
      </div>
    </div>

    <div class="body">
      <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
        <div class="sidebar-header">
          <button @click="toggleSidebar" class="btn-collapse">{{ sidebarCollapsed ? '▶' : '◀' }}</button>
        </div>
        <router-link to="/" class="nav-item" exact-active-class="active">
          <span class="nav-icon">📊</span><span class="nav-label">仪表盘</span>
        </router-link>
        <router-link to="/nodes" class="nav-item" active-class="active">
          <span class="nav-icon">🖥</span><span class="nav-label">节点列表</span>
        </router-link>
        <router-link to="/plans" class="nav-item" active-class="active">
          <span class="nav-icon">📋</span><span class="nav-label">套餐方案</span>
        </router-link>
        <router-link to="/recharge" class="nav-item" active-class="active">
          <span class="nav-icon">💰</span><span class="nav-label">充值</span>
        </router-link>
        <div class="divider" v-if="profile.is_staff"></div>
        <div class="section-label" v-if="!sidebarCollapsed && profile.is_staff">管理</div>
        <template v-if="profile.is_staff">
          <router-link to="/admin" class="nav-item" active-class="active">
            <span class="nav-icon">📊</span><span class="nav-label">管理概览</span>
          </router-link>
          <router-link to="/admin/users" class="nav-item" active-class="active">
            <span class="nav-icon">👥</span><span class="nav-label">用户管理</span>
          </router-link>
          <router-link to="/admin/nodes" class="nav-item" active-class="active">
            <span class="nav-icon">🖥</span><span class="nav-label">节点管理</span>
          </router-link>
          <router-link to="/admin/plans" class="nav-item" active-class="active">
            <span class="nav-icon">📋</span><span class="nav-label">套餐管理</span>
          </router-link>
          <router-link to="/admin/recharges" class="nav-item" active-class="active">
            <span class="nav-icon">💰</span><span class="nav-label">充值审核</span>
          </router-link>
        </template>
      </aside>
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-layout { display: flex; flex-direction: column; height: 100vh; background: var(--bg-primary); color: var(--text-primary); }
.top-header { display: flex; align-items: center; justify-content: space-between; height: 56px; padding: 0 1.5rem; background: var(--bg-card); border-bottom: 1px solid var(--border); backdrop-filter: blur(12px); flex-shrink: 0; }
.header-left { display: flex; align-items: center; gap: 0.75rem; }
.logo { font-size: 1.125rem; font-weight: 700; }
.header-right { display: flex; align-items: center; gap: 0.75rem; }
.balance { color: var(--success); font-size: 0.875rem; font-weight: 600; }
.btn-theme { background: var(--bg-hover); color: var(--text-primary); border: 1px solid var(--border); padding: 0.375rem; border-radius: 6px; cursor: pointer; font-size: 1rem; line-height: 1; display: flex; align-items: center; transition: all 0.2s; }
.btn-theme:hover { background: var(--border-solid); }
.avatar { width: 32px; height: 32px; border-radius: 50%; background: var(--accent-gradient); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; font-weight: 700; cursor: pointer; transition: all 0.2s; user-select: none; }
.avatar:hover { transform: scale(1.1); box-shadow: 0 0 12px rgba(59,130,246,0.4); }
.btn-logout { background: var(--danger); color: #fff; border: none; padding: 0.375rem 0.75rem; border-radius: 6px; cursor: pointer; font-size: 0.8rem; transition: opacity 0.2s; }
.btn-logout:hover { opacity: 0.85; }
.body { display: flex; flex: 1; overflow: hidden; }
.sidebar { width: 220px; background: var(--bg-card); padding: 1rem 0.75rem; display: flex; flex-direction: column; gap: 0.25rem; overflow-y: auto; border-right: 1px solid var(--border); backdrop-filter: blur(12px); flex-shrink: 0; transition: width 0.25s; }
.sidebar.collapsed { width: 64px; }
.sidebar-header { display: flex; justify-content: flex-end; margin-bottom: 0.5rem; padding: 0 0.25rem; }
.sidebar.collapsed .sidebar-header { justify-content: center; }
.btn-collapse { background: var(--bg-hover); color: var(--text-secondary); border: 1px solid var(--border); padding: 0.25rem 0.375rem; border-radius: 6px; cursor: pointer; font-size: 0.75rem; transition: all 0.2s; }
.btn-collapse:hover { background: var(--border-solid); color: var(--text-primary); }
.divider { height: 1px; background: var(--border); margin: 0.5rem 0; }
.section-label { font-size: 0.7rem; color: var(--text-muted); padding: 0.5rem 0.75rem 0.25rem; text-transform: uppercase; letter-spacing: 0.05em; overflow: hidden; white-space: nowrap; }
.nav-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.625rem; color: var(--text-secondary); text-decoration: none; border-radius: var(--radius-sm); font-size: 0.875rem; transition: all 0.2s; white-space: nowrap; }
.sidebar.collapsed .nav-item { justify-content: center; padding: 0.625rem; }
.nav-item:hover { background: var(--bg-hover); color: var(--text-primary); }
.nav-item.active { background: var(--accent-gradient); color: #fff; }
.nav-icon { font-size: 1rem; flex-shrink: 0; }
.nav-label { transition: opacity 0.2s; }
.sidebar.collapsed .nav-label { display: none; }
.sidebar.collapsed .section-label { display: none; }
.main-content { flex: 1; padding: 1.5rem; overflow-y: auto; }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 100; backdrop-filter: blur(4px); }
.modal { background: var(--bg-card); backdrop-filter: blur(12px); padding: 1.5rem; border-radius: var(--radius); border: 1px solid var(--border); width: 400px; box-shadow: var(--shadow); }
.modal h3 { margin-bottom: 1rem; }
.form-group { margin-bottom: 0.75rem; }
.form-group label { display: block; font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.25rem; }
.form-group input { width: 100%; padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-primary); color: var(--text-primary); outline: none; }
.form-group input:focus { border-color: var(--accent); }
.pwd-wrap { position: relative; }
.pwd-wrap input { padding-right: 2.5rem; }
.eye-btn { position: absolute; right: 0.5rem; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; font-size: 1rem; padding: 0.25rem; color: var(--text-muted); line-height: 1; }
.eye-btn:hover { transform: translateY(-50%) scale(1.1); }
.form-actions { display: flex; gap: 0.5rem; justify-content: flex-end; margin-top: 1rem; }
.btn-primary { background: var(--accent-gradient); color: #fff; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 500; transition: all 0.2s; }
.btn-primary:hover { transform: translateY(-1px); }
.btn-secondary { background: var(--bg-hover); color: var(--text-primary); border: 1px solid var(--border); padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; font-size: 0.85rem; }
.msg { font-size: 0.85rem; margin-top: 0.5rem; }
.msg.success { color: var(--success); }
.msg.error { color: var(--danger); }
</style>
