<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { useSiteName } from '../api/site'
import { profile, fetchProfile } from '../api/profile'

const router = useRouter()
const siteName = useSiteName()

const pageTitleMap: Record<string, string> = {
  Dashboard: '仪表盘',
  Nodes: '节点列表',
  Plans: '套餐方案',
  Recharge: '充值',
  Subscription: '订阅信息',
  Tutorials: '使用教程',
  Invite: '邀请系统',
  Contact: '联系管理员',
  Notifications: '通知中心',
  NotificationDetail: '通知详情',
  AdminHome: '管理后台',
  AdminUsers: '用户管理',
  AdminNodes: '节点管理',
  AdminPlans: '套餐管理',
  AdminRecharges: '充值管理',
  AdminInvite: '邀请管理',
  AdminNotifications: '通知管理',
  AdminContact: '联系管理',
  AdminPaymentQr: '收款码管理',
  AdminPaymentSettings: '充值设置',
}

interface BreadcrumbItem {
  label: string
  path: string
}

const breadcrumbs = computed<BreadcrumbItem[]>(() => {
  const matched = router.currentRoute.value.matched
  const items: BreadcrumbItem[] = []
  let adminInserted = false
  for (const record of matched) {
    const name = record.name as string | undefined
    if (!name || !pageTitleMap[name]) continue
    if (name.startsWith('Admin') && !adminInserted) {
      if (name !== 'AdminHome') {
        items.push({ label: '管理后台', path: '/admin' })
      }
      adminInserted = true
    }
    items.push({ label: pageTitleMap[name], path: record.path })
  }
  return items
})

const isDark = ref(true)
const sidebarCollapsed = ref(false)
const userSectionOpen = ref(localStorage.getItem('user_section') !== 'closed')
const adminSectionOpen = ref(localStorage.getItem('admin_section') !== 'closed')
const showUserMenu = ref(false)
const showSettings = ref(false)
const showOldPwd = ref(false)
const showNewPwd = ref(false)
const settingsForm = ref({ email: '', old_password: '', new_password: '' })
const settingsMsg = ref('')
const unreadCount = ref(0)
const contactUnread = ref(0)
const adminContactPending = ref(0)
let pollTimer: ReturnType<typeof setInterval> | null = null

async function fetchUnread() {
  try {
    const { data } = await api.get('/notifications/unread-count/')
    unreadCount.value = data.unread
  } catch {
    // not authenticated yet or error
  }
}

async function fetchContactUnread() {
  try {
    const after = localStorage.getItem('contact_last_viewed') || ''
    const { data } = await api.get(`/contact/unread-count/?after=${encodeURIComponent(after)}`)
    contactUnread.value = data.unread
  } catch {
    // not authenticated yet or error
  }
}

async function fetchAdminContactPending() {
  if (!profile.is_staff) return
  try {
    const { data } = await api.get('/admin/contact/pending_count/')
    adminContactPending.value = data.pending
  } catch {
    // not authenticated yet or error
  }
}

onMounted(async () => {
  const saved = localStorage.getItem('theme')
  if (saved) {
    isDark.value = saved === 'dark'
  } else {
    isDark.value = !window.matchMedia('(prefers-color-scheme: light)').matches
  }
  applyTheme()
  sidebarCollapsed.value = localStorage.getItem('sidebar') === 'collapsed'
  await fetchProfile()
  if (!profile.username) router.push('/login')
  await fetchUnread()
  await fetchContactUnread()
  await fetchAdminContactPending()
  pollTimer = setInterval(() => {
    fetchUnread()
    fetchContactUnread()
    fetchAdminContactPending()
  }, 15000)
})

onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer)
})

watch(() => router.currentRoute.value.path, () => {
  fetchUnread()
})

function toggleTheme() {
  isDark.value = !isDark.value
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  applyTheme()
  showUserMenu.value = false
}

function applyTheme() {
  document.documentElement.classList.toggle('light', !isDark.value)
}

function logout() {
  localStorage.clear()
  router.push('/login')
}

function handleAvatarClick() {
  showUserMenu.value = !showUserMenu.value
}

function closeUserMenu() {
  showUserMenu.value = false
}

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('sidebar', sidebarCollapsed.value ? 'collapsed' : '')
}

function toggleUserSection() {
  userSectionOpen.value = !userSectionOpen.value
  localStorage.setItem('user_section', userSectionOpen.value ? 'open' : 'closed')
}

function toggleAdminSection() {
  adminSectionOpen.value = !adminSectionOpen.value
  localStorage.setItem('admin_section', adminSectionOpen.value ? 'open' : 'closed')
}

function onWindowClick(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.user-menu-wrap')) {
    showUserMenu.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', onWindowClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onWindowClick)
})

function openSettings() {
  showUserMenu.value = false
  settingsForm.value.email = profile.email
  settingsForm.value.old_password = ''
  settingsForm.value.new_password = ''
  settingsMsg.value = ''
  showSettings.value = true
}

async function saveSettings() {
  settingsMsg.value = ''
  try {
    const payload: any = {}
    if (settingsForm.value.email !== profile.email) payload.email = settingsForm.value.email
    if (settingsForm.value.new_password) {
      payload.old_password = settingsForm.value.old_password
      payload.new_password = settingsForm.value.new_password
    }
    if (Object.keys(payload).length === 0) { showSettings.value = false; return }
    await api.patch('/auth/profile/', payload)
    profile.email = settingsForm.value.email
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
        <button class="btn-collapse" @click="toggleSidebar" :title="sidebarCollapsed ? '展开侧栏' : '收起侧栏'">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
        </button>
        <span class="logo">{{ siteName }}</span>
        <nav v-if="breadcrumbs.length" class="breadcrumb">
          <template v-for="(item, i) in breadcrumbs" :key="item.path">
            <router-link v-if="i < breadcrumbs.length - 1" :to="item.path" class="crumb-link">{{ item.label }}</router-link>
            <span v-else class="crumb-current">{{ item.label }}</span>
            <span v-if="i < breadcrumbs.length - 1" class="crumb-sep">/</span>
          </template>
        </nav>
      </div>
      <div class="header-right">
        <span v-if="profile.username && !profile.is_staff" class="balance">
          <svg class="balance-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v12"/><path d="M9 9h4.5a2 2 0 0 1 0 4H9"/></svg>
          <span class="balance-amount">{{ (profile.balance / 100).toFixed(2) }}</span>
        </span>
        <div class="user-menu-wrap">
          <div class="avatar" @click="handleAvatarClick" :title="profile.username">{{ (profile.username || '?').charAt(0).toUpperCase() }}</div>
          <div v-if="showUserMenu" class="user-dropdown">
            <div class="dropdown-header">
              <span class="dropdown-username">{{ profile.username }}</span>
              <span class="dropdown-email">{{ profile.email || '未设置邮箱' }}</span>
            </div>
            <div class="dropdown-divider"></div>
            <button class="dropdown-item" @click="openSettings(); closeUserMenu()">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
              <span>个人设置</span>
            </button>
            <button class="dropdown-item" @click="toggleTheme">
              <svg v-if="isDark" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
              <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
              <span>{{ isDark ? '切换白天模式' : '切换黑夜模式' }}</span>
            </button>
            <div class="dropdown-divider"></div>
            <button class="dropdown-item danger" @click="logout(); closeUserMenu()">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
              <span>退出登录</span>
            </button>
          </div>
        </div>
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
          <div class="logo-icon-wrap">
            <svg class="plane-icon" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 2L11 13"/><path d="M22 2L15 22L11 13L2 9L22 2Z"/>
            </svg>
          </div>
        </div>
        <!-- 用户功能 -->
        <div class="nav-section">
          <div class="section-header" @click="toggleUserSection">
            <span class="section-label">用户功能</span>
            <svg class="section-arrow" :class="{ open: userSectionOpen }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
          </div>
          <div v-show="userSectionOpen" class="section-body">
            <router-link to="/" class="nav-item" exact-active-class="active">
              <span class="nav-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg></span>
              <span class="nav-label">仪表盘</span>
            </router-link>
            <router-link to="/nodes" class="nav-item" active-class="active">
              <span class="nav-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><circle cx="6" cy="6" r="1" fill="currentColor"/><circle cx="6" cy="18" r="1" fill="currentColor"/></svg></span>
              <span class="nav-label">节点列表</span>
            </router-link>
            <router-link to="/plans" class="nav-item" active-class="active">
              <span class="nav-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/><line x1="9" y1="12" x2="15" y2="12"/><line x1="9" y1="16" x2="13" y2="16"/></svg></span>
              <span class="nav-label">套餐方案</span>
            </router-link>
            <router-link to="/recharge" class="nav-item" active-class="active">
              <span class="nav-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="6" width="22" height="12" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M1 10h22"/></svg></span>
              <span class="nav-label">充值</span>
            </router-link>
            <router-link to="/subscription" class="nav-item" active-class="active">
              <span class="nav-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg></span>
              <span class="nav-label">订阅</span>
            </router-link>
            <router-link to="/tutorials" class="nav-item" active-class="active">
              <span class="nav-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg></span>
              <span class="nav-label">使用教程</span>
            </router-link>
            <router-link to="/notifications" class="nav-item" active-class="active">
              <span class="nav-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
                <span v-if="unreadCount > 0" class="nav-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
              </span>
              <span class="nav-label">通知</span>
            </router-link>
            <router-link to="/invite" class="nav-item" active-class="active">
              <span class="nav-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg></span>
              <span class="nav-label">邀请返现</span>
            </router-link>
            <router-link to="/contact" class="nav-item" active-class="active">
              <span class="nav-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                <span v-if="contactUnread > 0" class="nav-badge">{{ contactUnread > 99 ? '99+' : contactUnread }}</span>
              </span>
              <span class="nav-label">联系管理员</span>
            </router-link>
          </div>
        </div>

        <!-- 管理功能 -->
        <div class="nav-section" v-if="profile.is_staff">
          <div class="section-header" @click="toggleAdminSection">
            <span class="section-label">管理功能</span>
            <svg class="section-arrow" :class="{ open: adminSectionOpen }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
          </div>
          <div v-show="adminSectionOpen" class="section-body">
            <router-link to="/admin" class="nav-item" exact-active-class="active">
              <span class="nav-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></span>
              <span class="nav-label">管理概览</span>
            </router-link>
            <router-link to="/admin/users" class="nav-item" active-class="active">
              <span class="nav-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg></span>
              <span class="nav-label">用户管理</span>
            </router-link>
            <router-link to="/admin/nodes" class="nav-item" active-class="active">
              <span class="nav-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><circle cx="6" cy="6" r="1" fill="currentColor"/><circle cx="6" cy="18" r="1" fill="currentColor"/></svg></span>
              <span class="nav-label">节点管理</span>
            </router-link>
            <router-link to="/admin/plans" class="nav-item" active-class="active">
              <span class="nav-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg></span>
              <span class="nav-label">套餐管理</span>
            </router-link>
            <router-link to="/admin/recharges" class="nav-item" active-class="active">
              <span class="nav-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="6" width="22" height="12" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M1 10h22"/></svg></span>
              <span class="nav-label">充值审核</span>
            </router-link>
            <router-link to="/admin/payment-qr" class="nav-item" active-class="active">
              <span class="nav-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5" fill="currentColor"/><path d="M21 15l-5-5L5 21"/></svg></span>
              <span class="nav-label">收款码管理</span>
            </router-link>
            <router-link to="/admin/payment-settings" class="nav-item" active-class="active">
              <span class="nav-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg></span>
              <span class="nav-label">充值设置</span>
            </router-link>
            <router-link to="/admin/invite" class="nav-item" active-class="active">
              <span class="nav-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg></span>
              <span class="nav-label">邀请管理</span>
            </router-link>
            <router-link to="/admin/notifications" class="nav-item" active-class="active">
              <span class="nav-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg></span>
              <span class="nav-label">通知管理</span>
            </router-link>
            <router-link to="/admin/contact" class="nav-item" active-class="active">
              <span class="nav-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                <span v-if="adminContactPending > 0" class="nav-badge">{{ adminContactPending > 99 ? '99+' : adminContactPending }}</span>
              </span>
              <span class="nav-label">联系管理</span>
            </router-link>
          </div>
        </div>
      </aside>
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-layout { display: flex; flex-direction: column; height: 100vh; background: var(--bg-primary); color: var(--text-primary); }

/* ── Header ── */
.top-header { display: flex; align-items: center; justify-content: space-between; height: 56px; padding: 0 1.5rem; background: linear-gradient(135deg, #141e33 0%, #1a2a45 100%); border-bottom: 1px solid rgba(56,189,248,0.15); box-shadow: 0 1px 12px rgba(0,0,0,0.2); flex-shrink: 0; position: relative; z-index: 10; }
.light .top-header { background: linear-gradient(135deg, #e8eff8 0%, #dce6f2 100%); border-bottom: 1px solid var(--border); }
.header-left { display: flex; align-items: center; gap: 0.5rem; min-width: 0; }
.btn-collapse { background: transparent; color: var(--text-tertiary); border: none; padding: 0.3rem; border-radius: 6px; cursor: pointer; display: flex; align-items: center; transition: all 0.2s; flex-shrink: 0; }
.btn-collapse:hover { background: rgba(255,255,255,0.08); color: var(--text-primary); }
.light .btn-collapse:hover { background: rgba(0,0,0,0.06); }
.logo { font-size: 1.125rem; font-weight: 700; background: var(--accent-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; white-space: nowrap; flex-shrink: 0; }

/* ── Breadcrumb ── */
.breadcrumb { display: flex; align-items: center; gap: 0.35rem; padding: 0.2rem 0 0.2rem 0.75rem; border-left: 1px solid var(--border); overflow: hidden; }
.crumb-link { font-size: 0.8rem; color: var(--text-muted); text-decoration: none; white-space: nowrap; transition: color 0.15s; }
.crumb-link:hover { color: var(--accent); }
.crumb-current { font-size: 0.85rem; color: var(--text-primary); font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.crumb-sep { font-size: 0.75rem; color: var(--text-muted); }
.header-right { display: flex; align-items: center; gap: 0.75rem; }
.balance { display: flex; align-items: center; gap: 0.35rem; color: #22c55e; font-size: 1rem; font-weight: 700; background: linear-gradient(135deg, rgba(34,197,94,0.12) 0%, rgba(34,197,94,0.06) 100%); padding: 0.25rem 0.75rem; border-radius: 8px; border: 1px solid rgba(34,197,94,0.25); box-shadow: 0 0 12px rgba(34,197,94,0.08); transition: all 0.2s; }
.balance:hover { background: linear-gradient(135deg, rgba(34,197,94,0.18) 0%, rgba(34,197,94,0.1) 100%); box-shadow: 0 0 20px rgba(34,197,94,0.15); }
.balance-icon { opacity: 0.9; flex-shrink: 0; }
.balance-amount { font-variant-numeric: tabular-nums; }

/* ── User Dropdown ── */
.user-menu-wrap { position: relative; }
.avatar { width: 32px; height: 32px; border-radius: 50%; background: var(--accent-gradient); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; font-weight: 700; cursor: pointer; transition: all 0.2s; user-select: none; box-shadow: 0 0 0 2px rgba(56,189,248,0.2); }
.avatar:hover { transform: scale(1.1); box-shadow: 0 0 0 2px rgba(56,189,248,0.4), 0 0 20px rgba(56,189,248,0.25); }
.user-dropdown { position: absolute; top: calc(100% + 8px); right: 0; width: 220px; background: var(--bg-card); backdrop-filter: blur(20px); border-radius: var(--radius); border: 1px solid var(--border); box-shadow: 0 8px 32px rgba(0,0,0,0.3); z-index: 100; overflow: hidden; animation: dropIn 0.15s ease; }
@keyframes dropIn { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: translateY(0); } }
.dropdown-header { padding: 0.85rem 1rem; display: flex; flex-direction: column; gap: 0.15rem; }
.dropdown-username { font-size: 0.9rem; font-weight: 600; color: var(--text-primary); }
.dropdown-email { font-size: 0.75rem; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dropdown-divider { height: 1px; background: var(--border); }
.dropdown-item { display: flex; align-items: center; gap: 0.5rem; width: 100%; padding: 0.65rem 1rem; border: none; background: transparent; color: var(--text-secondary); font-size: 0.85rem; cursor: pointer; transition: all 0.15s; text-align: left; }
.dropdown-item:hover { background: var(--bg-hover); color: var(--text-primary); }
.dropdown-item.danger:hover { background: rgba(239,68,68,0.1); color: var(--danger); }
.dropdown-item svg { flex-shrink: 0; }

/* ── Layout ── */
.body { display: flex; flex: 1; overflow: hidden; }

/* ── Sidebar ── */
.sidebar { width: var(--nav-width); background: var(--bg-secondary); padding: 0; display: flex; flex-direction: column; gap: 0; overflow-y: auto; border-right: 1px solid var(--border); flex-shrink: 0; transition: width 0.25s; scrollbar-width: thin; scrollbar-color: var(--border) transparent; }
.sidebar.collapsed { width: var(--nav-width-collapsed); }

.sidebar-header { display: flex; align-items: center; justify-content: center; padding: 1.25rem 0.75rem; border-bottom: 1px solid var(--border); position: relative; overflow: hidden; }
.sidebar-header::after { content: ''; position: absolute; bottom: 0; left: 50%; transform: translateX(-50%); width: 60%; height: 1px; background: linear-gradient(90deg, transparent, var(--accent), transparent); opacity: 0.4; }
.sidebar.collapsed .sidebar-header { padding: 1.25rem 0.5rem; }

.logo-icon-wrap { display: flex; align-items: center; justify-content: center; width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(135deg, rgba(56,189,248,0.12) 0%, rgba(56,189,248,0.06) 100%); border: 1px solid rgba(56,189,248,0.15); transition: all 0.3s; }
.sidebar.collapsed .logo-icon-wrap { width: 40px; height: 40px; }
.logo-icon-wrap:hover { background: linear-gradient(135deg, rgba(56,189,248,0.18) 0%, rgba(56,189,248,0.1) 100%); border-color: rgba(56,189,248,0.3); transform: scale(1.05); }
.plane-icon { color: var(--accent); flex-shrink: 0; }

/* ── Nav Sections ── */
.nav-section { border-bottom: 1px solid var(--border); padding-bottom: 0.25rem; }
.sidebar.collapsed .nav-section { border-bottom: none; padding-bottom: 0; }
.section-header { display: flex; align-items: center; justify-content: space-between; padding: 0.75rem 0.75rem 0.4rem; cursor: pointer; transition: background 0.15s; user-select: none; }
.section-header:hover { background: transparent; }
.sidebar.collapsed .section-header { display: none; }
.section-label { font-size: 0.7rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em; opacity: 0.6; }
.section-arrow { color: var(--text-muted); transition: transform 0.2s; flex-shrink: 0; opacity: 0.4; }
.section-arrow.open { transform: rotate(90deg); }
.section-body { display: flex; flex-direction: column; gap: 1px; padding: 0 0.5rem 0.25rem; }

/* ── Nav Items ── */
.nav-item { position: relative; display: flex; align-items: center; gap: 0.5rem; padding: 0.55rem 0.6rem; margin: 0; color: var(--text-secondary); text-decoration: none; border-radius: 8px; font-size: 0.9rem; transition: all 0.2s; white-space: nowrap; }
.sidebar.collapsed .nav-item { justify-content: center; padding: 0.55rem; margin: 0 0.25rem; }
.nav-item:hover { background: var(--bg-hover); color: var(--text-primary); }
.nav-item.active { background: linear-gradient(135deg, rgba(56,189,248,0.1) 0%, rgba(56,189,248,0.05) 100%); color: var(--accent); font-weight: 500; box-shadow: inset 0 1px 0 rgba(56,189,248,0.08); }
.nav-item.active::before { content: ''; position: absolute; left: -2px; top: 50%; transform: translateY(-50%); width: 3px; height: 18px; border-radius: 0 3px 3px 0; background: var(--accent-gradient); box-shadow: 0 0 8px rgba(56,189,248,0.3); }
.sidebar.collapsed .nav-item.active::before { left: -6px; }
.nav-icon { font-size: 1rem; flex-shrink: 0; display: flex; align-items: center; position: relative; }
.nav-icon svg { display: block; }
.nav-badge { position: absolute; top: -6px; right: -8px; min-width: 16px; height: 16px; padding: 0 4px; border-radius: 8px; background: var(--danger); color: #fff; font-size: 0.6rem; font-weight: 700; display: flex; align-items: center; justify-content: center; line-height: 1; box-shadow: 0 0 6px rgba(239,68,68,0.4); }
.sidebar.collapsed .nav-badge { top: -4px; right: -4px; }
.nav-label { transition: opacity 0.2s; }
.sidebar.collapsed .nav-label { display: none; }
.sidebar.collapsed .section-label { display: none; }

/* ── Main ── */
.main-content { flex: 1; padding: 1.5rem; overflow-y: auto; }

/* ── Modal ── */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 100; backdrop-filter: blur(4px); }
.modal { background: var(--bg-card); backdrop-filter: blur(16px); padding: 1.5rem; border-radius: var(--radius); border: 1px solid var(--border); width: 400px; box-shadow: var(--shadow); }
.modal h3 { margin-bottom: 1rem; }
.form-group { margin-bottom: 0.75rem; }
.form-group label { display: block; font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.25rem; }
.form-group input { width: 100%; padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-primary); color: var(--text-primary); outline: none; }
.form-group input:focus { border-color: var(--accent); }
.pwd-wrap { position: relative; }
.pwd-wrap input { padding-right: 2.5rem; }
.eye-btn { position: absolute; right: 0.5rem; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; font-size: 1rem; padding: 0.25rem; color: var(--text-muted); line-height: 1; }
.form-actions { display: flex; gap: 0.5rem; justify-content: flex-end; margin-top: 1rem; }
.btn-primary { background: var(--accent-gradient); color: #fff; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 500; transition: all 0.2s; }
.btn-primary:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(56,189,248,0.3); }
.btn-secondary { background: var(--bg-hover); color: var(--text-primary); border: 1px solid var(--border); padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; font-size: 0.85rem; }
.msg { font-size: 0.85rem; margin-top: 0.5rem; }
.msg.success { color: var(--success); }
.msg.error { color: var(--danger); }
</style>
