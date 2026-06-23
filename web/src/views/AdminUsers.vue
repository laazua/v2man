<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'
import { copyText, copiedKey } from '../api/copy'

interface User {
  id: number; username: string; email: string; uuid: string; plan_name: string | null; traffic_used: number; traffic_total: number; expire_date: string | null; is_active?: boolean; balance?: number
}

interface Plan {
  id: number; name: string
}

const users = ref<User[]>([])
const plans = ref<Plan[]>([])
const editing = ref<User | null>(null)
const editForm = ref({ plan_id: '', email: '', password: '', traffic_used: 0, traffic_total: 0, is_active: true, expire_date: '' })
const showEdit = ref(false)
const showPwd = ref(false)
const editError = ref('')

const topUpUser = ref<User | null>(null)
const topUpAmount = ref(0)
const showTopUp = ref(false)
const topUpMsg = ref('')

async function openTopUp(u: User) {
  topUpUser.value = u
  topUpAmount.value = 0
  topUpMsg.value = ''
  showTopUp.value = true
}

async function submitTopUp() {
  if (!topUpAmount.value || topUpAmount.value < 1) return
  try {
    const { data } = await api.post(`/admin/users/${topUpUser.value!.id}/top_up/`, {
      amount: topUpAmount.value * 100,
    })
    topUpMsg.value = data.message
    topUpUser.value!.balance = data.balance
    const { data: usersData } = await api.get('/admin/users/')
    users.value = usersData
  } catch (e: any) {
    topUpMsg.value = e.response?.data?.error || '充值失败'
  }
}

onMounted(async () => {
  const [u, p] = await Promise.all([
    api.get('/admin/users/'),
    api.get('/admin/plans/'),
  ])
  users.value = u.data
  plans.value = p.data
})

function openEdit(u: User) {
  editError.value = ''
  editing.value = u
  editForm.value = {
    plan_id: '',
    email: u.email,
    password: '',
    traffic_used: u.traffic_used,
    traffic_total: u.traffic_total,
    is_active: u.is_active ?? true,
    expire_date: u.expire_date ? u.expire_date.slice(0, 16) : '',
  }
  showEdit.value = true
}

async function saveEdit() {
  const payload: any = {}
  if (editForm.value.plan_id) payload.plan_id = Number(editForm.value.plan_id)
  if (editForm.value.traffic_used !== undefined) payload.traffic_used = editForm.value.traffic_used
  if (editForm.value.traffic_total !== undefined) payload.traffic_total = editForm.value.traffic_total
  payload.is_active = editForm.value.is_active
  if (editForm.value.expire_date) payload.expire_date = editForm.value.expire_date
  if (editForm.value.email !== editing.value?.email) payload.email = editForm.value.email
  if (editForm.value.password) payload.password = editForm.value.password

  try {
    await api.patch(`/admin/users/${editing.value!.id}/update_user/`, payload)
    showEdit.value = false
    const { data } = await api.get('/admin/users/')
    users.value = data
  } catch (e: any) {
    editError.value = e.response?.data?.error || e.response?.data?.detail || '保存失败'
  }
}

function formatMB(mb: number) {
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`
  return `${mb} MB`
}

const confirmTarget = ref<User | null>(null)
const deleteTarget = ref<User | null>(null)
const showInvalidateDialog = ref(false)
const invalidateResult = ref<any>(null)
const syncingId = ref<number | null>(null)
const openMenuId = ref<number | null>(null)
const menuDirUp = ref(false)

function toggleMenu(id: number, el?: EventTarget | null) {
  if (openMenuId.value === id) {
    openMenuId.value = null
    return
  }
  openMenuId.value = id
  if (el instanceof HTMLElement) {
    const rect = el.getBoundingClientRect()
    const spaceBelow = window.innerHeight - rect.bottom
    menuDirUp.value = spaceBelow < 240
  } else {
    menuDirUp.value = false
  }
}

function closeMenu() {
  openMenuId.value = null
}

function invalidateSub(u: User) {
  confirmTarget.value = u
}

async function doInvalidate() {
  const u = confirmTarget.value
  if (!u) return
  confirmTarget.value = null
  try {
    const res = await api.post(`/admin/users/${u.id}/invalidate_subscription/`)
    invalidateResult.value = res.data
    showInvalidateDialog.value = true
    const { data } = await api.get('/admin/users/')
    users.value = data
  } catch (e: any) {
    alert(e.response?.data?.error || '操作失败')
  }
}

function confirmDelete(u: User) {
  deleteTarget.value = u
  openMenuId.value = null
}

async function doDelete() {
  const u = deleteTarget.value
  if (!u) return
  deleteTarget.value = null
  try {
    await api.post(`/admin/users/${u.id}/destroy_user/`)
    const { data } = await api.get('/admin/users/')
    users.value = data
  } catch (e: any) {
    alert(e.response?.data?.error || '删除失败')
  }
}

async function syncConfig(u: User) {
  syncingId.value = u.id
  try {
    const res = await api.post(`/admin/users/${u.id}/sync_config/`)
    invalidateResult.value = res.data
    showInvalidateDialog.value = true
    const { data } = await api.get('/admin/users/')
    users.value = data
  } catch (e: any) {
    alert(e.response?.data?.error || '操作失败')
  } finally {
    syncingId.value = null
  }
}
</script>

<template>
  <div class="admin-page">
    <header><h2>用户管理</h2></header>

    <div v-if="showEdit" class="modal-overlay" @click.self="showEdit = false">
      <div class="modal">
        <h3>编辑用户: {{ editing?.username }}</h3>
        <div class="form-grid">
          <label>套餐
            <select v-model="editForm.plan_id">
              <option value="">无</option>
              <option v-for="p in plans" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </label>
          <label>启用 <select v-model="editForm.is_active"><option :value="true">是</option><option :value="false">否</option></select></label>
          <label>邮箱 <input v-model="editForm.email" type="email" /></label>
          <label>新密码
            <div class="pwd-wrap">
              <input v-model="editForm.password" :type="showPwd ? 'text' : 'password'" placeholder="留空不修改" />
              <button type="button" @click="showPwd = !showPwd" class="eye-btn">{{ showPwd ? '🙈' : '👁️' }}</button>
            </div>
          </label>
          <label>已用流量 (MB) <input v-model.number="editForm.traffic_used" type="number" /></label>
          <label>总流量 (MB) <input v-model.number="editForm.traffic_total" type="number" /></label>
          <label>到期时间 <input v-model="editForm.expire_date" type="datetime-local" /></label>
        </div>
        <p v-if="editError" class="error">{{ editError }}</p>
        <div class="form-actions">
          <button @click="showEdit = false" class="btn-secondary">取消</button>
          <button @click="saveEdit" class="btn-primary">保存</button>
        </div>
      </div>
    </div>

    <div v-if="showTopUp" class="modal-overlay" @click.self="showTopUp = false">
      <div class="modal modal-sm">
        <h3>充值 — {{ topUpUser?.username }}</h3>
        <p class="current-balance">当前余额: ¥{{ ((topUpUser?.balance ?? 0) / 100).toFixed(2) }}</p>
        <div class="topup-input">
          <span class="prefix">¥</span>
          <input v-model.number="topUpAmount" type="number" min="1" placeholder="输入金额" />
        </div>
        <p v-if="topUpMsg" :class="topUpMsg.includes('失败') ? 'error' : 'success'">{{ topUpMsg }}</p>
        <div class="form-actions">
          <button @click="showTopUp = false" class="btn-secondary">关闭</button>
          <button @click="submitTopUp" :disabled="!topUpAmount || topUpAmount < 1" class="btn-primary">确认充值</button>
        </div>
      </div>
    </div>

    <div v-if="confirmTarget" class="modal-overlay" @click.self="confirmTarget = null">
      <div class="modal invalidate-confirm">
        <div class="confirm-icon">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        </div>
        <h3>确认失效订阅？</h3>
        <p>将使 <strong>{{ confirmTarget?.username }}</strong> 的订阅链接失效，<br>并生成新的 UUID。</p>
        <p class="warn-note">用户需要重新订阅获取新配置，且需同步更新 V2Ray 服务端。</p>
        <div class="confirm-actions">
          <button @click="confirmTarget = null" class="btn-secondary">取消</button>
          <button @click="doInvalidate" class="btn-solid-danger">确认失效</button>
        </div>
      </div>
    </div>

    <div v-if="showInvalidateDialog" class="modal-overlay" @click.self="showInvalidateDialog = false">
      <div class="modal invalidate-modal">
        <div class="invalidate-header">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" :stroke="invalidateResult?.new_uuid ? '#ef4444' : '#38bdf8'" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          <div>
            <h3>{{ invalidateResult?.new_uuid ? '订阅已失效' : '配置已同步' }}</h3>
            <p class="invalidate-subtitle">{{ invalidateResult?.message }}</p>
          </div>
        </div>
        <div class="invalidate-body">
          <div v-if="invalidateResult?.new_uuid" class="uuid-section">
            <label>新 UUID</label>
            <div class="uuid-row">
              <code class="uuid-value">{{ invalidateResult?.new_uuid }}</code>
              <button class="copy-btn" @click="copyText(invalidateResult?.new_uuid || '', 'inv-uuid')">
                <svg v-if="copiedKey !== 'inv-uuid'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                {{ copiedKey === 'inv-uuid' ? '已复制' : '复制' }}
              </button>
            </div>
          </div>
          <div v-if="invalidateResult?.sync_results?.length" class="sync-section">
            <label>节点同步状态</label>
            <div v-for="r in invalidateResult.sync_results" :key="r.node_id" :class="['sync-item', r.uuid_found ? 'sync-found' : 'sync-ok', !r.success ? 'sync-fail' : '']">
              <svg v-if="r.success && r.uuid_found" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
              <svg v-else-if="r.success" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              <span>{{ r.node_name }}</span>
              <span v-if="!r.success" class="sync-err">{{ r.error }}</span>
              <span v-else-if="!r.uuid_found" class="sync-err">UUID 未在配置中找到</span>
            </div>
          </div>
        </div>
        <div class="invalidate-footer">
          <button @click="showInvalidateDialog = false" class="btn-primary">我知道了</button>
        </div>
      </div>
    </div>

    <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
      <div class="modal invalidate-confirm">
        <div class="confirm-icon">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
        </div>
        <h3>确认删除用户？</h3>
        <p>将永久删除 <strong>{{ deleteTarget?.username }}</strong> 的所有数据，<br>包括钱包余额、套餐记录等，<strong>此操作不可恢复</strong>。</p>
        <div class="confirm-actions">
          <button @click="deleteTarget = null" class="btn-secondary">取消</button>
          <button @click="doDelete" class="btn-solid-danger">确认删除</button>
        </div>
      </div>
    </div>

    <div class="table-wrapper">
      <table class="data-table">
        <thead><tr><th>ID</th><th>用户名</th><th>邮箱</th><th>UUID</th><th>套餐</th><th>余额</th><th>已用/总量</th><th>到期</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td>{{ u.id }}</td>
            <td>{{ u.username }}</td>
            <td>{{ u.email }}</td>
            <td><code style="font-size:0.75rem;cursor:pointer;color:var(--accent)" @click="copyText(u.uuid, 'uuid-'+u.id)">{{ u.uuid }}</code><span v-if="copiedKey === 'uuid-'+u.id" style="color:var(--success);font-size:0.7rem;margin-left:0.25rem">已复制</span></td>
            <td>{{ u.plan_name || '无' }}</td>
            <td>¥{{ ((u.balance ?? 0) / 100).toFixed(2) }}</td>
            <td>{{ formatMB(u.traffic_used) }} / {{ formatMB(u.traffic_total) }}</td>
            <td>{{ u.expire_date ? new Date(u.expire_date).toLocaleDateString('zh-CN') : '无' }}</td>
            <td><span :class="['badge', u.is_active !== false ? 'active' : 'inactive']">{{ u.is_active !== false ? '正常' : '停用' }}</span></td>
            <td class="action-cell">
              <div :class="['dropdown-wrap', { dropup: openMenuId === u.id && menuDirUp }]">
                <button @click.stop="toggleMenu(u.id, $event.target)" class="btn-more">···</button>
                <div v-if="openMenuId === u.id" class="dropdown-menu" @click.stop>
                  <button @click="openEdit(u); closeMenu()" class="dropdown-item">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                    编辑
                  </button>
                  <button @click="openTopUp(u); closeMenu()" class="dropdown-item">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                    充值
                  </button>
                  <button @click="syncConfig(u); closeMenu()" :disabled="syncingId === u.id" class="dropdown-item">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 7v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7"/><path d="M4 7V5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v2"/><line x1="8" y1="12" x2="16" y2="12"/></svg>
                    同步配置
                  </button>
                  <button @click="invalidateSub(u); closeMenu()" class="dropdown-item dropdown-danger">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                    失效订阅
                  </button>
                  <div class="dropdown-divider"></div>
                  <button @click="confirmDelete(u)" class="dropdown-item dropdown-danger">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                    删除用户
                  </button>
                </div>
              </div>
            </td>
          </tr>
          <tr v-if="!users.length"><td colspan="10" class="empty">暂无数据</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.admin-page { max-width: 1000px; }
header { margin-bottom: 1.5rem; }
.table-wrapper { background: var(--bg-card); backdrop-filter: blur(12px); border-radius: var(--radius); border: 1px solid var(--border); overflow: hidden; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { padding: 0.75rem 1rem; text-align: left; font-size: 0.875rem; }
.data-table th { background: var(--bg-primary); color: var(--text-secondary); font-weight: 500; border-bottom: 1px solid var(--border); }
.data-table td { border-bottom: 1px solid var(--border); }
.data-table tbody tr:last-child td { border-bottom: none; }
.data-table tbody tr:hover { background: var(--bg-hover); }
.badge { padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 500; }
.badge.active { background: rgba(34,197,94,0.15); color: var(--success); }
.badge.inactive { background: rgba(239,68,68,0.15); color: var(--danger); }
.btn-sm { background: var(--bg-hover); color: var(--text-primary); border: 1px solid var(--border); padding: 0.375rem 0.75rem; border-radius: 6px; cursor: pointer; font-size: 0.8rem; transition: all 0.2s; }
.btn-sm:hover { background: var(--border-solid); }
.btn-topup { border-color: transparent; background: rgba(34,197,94,0.15); color: var(--success); }
.btn-topup:hover { background: rgba(34,197,94,0.25); }
.btn-sync { border-color: transparent; background: rgba(56,189,248,0.15); color: var(--accent); }
.btn-sync:hover { background: rgba(56,189,248,0.25); }
.btn-sync:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-danger { border-color: transparent; background: rgba(239,68,68,0.12); color: var(--danger); }
.btn-danger:hover { background: rgba(239,68,68,0.25); }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 100; backdrop-filter: blur(4px); }
.modal { background: var(--bg-card); backdrop-filter: blur(12px); padding: 1.5rem; border-radius: var(--radius); border: 1px solid var(--border); width: 500px; box-shadow: var(--shadow); }
.modal h3 { margin-bottom: 1rem; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin: 1rem 0; }
label { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.8rem; color: var(--text-secondary); }
input, select { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-primary); color: var(--text-primary); outline: none; transition: border-color 0.2s; }
input:focus, select:focus { border-color: var(--accent); }
.pwd-wrap { position: relative; display: flex; }
.pwd-wrap input { flex: 1; padding-right: 2.5rem; }
.eye-btn { position: absolute; right: 0.5rem; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; font-size: 1rem; padding: 0.25rem; color: var(--text-muted); line-height: 1; }
.eye-btn:hover { transform: translateY(-50%) scale(1.1); }
.form-actions { display: flex; gap: 0.5rem; justify-content: flex-end; margin-top: 1rem; }
.btn-primary { background: var(--accent-gradient); color: #fff; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 500; transition: all 0.2s; }
.btn-primary:hover { transform: translateY(-1px); }
.btn-secondary { background: var(--bg-hover); color: var(--text-primary); border: 1px solid var(--border); padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; font-size: 0.85rem; transition: all 0.2s; }
.btn-secondary:hover { background: var(--border-solid); }
.empty { text-align: center; color: var(--text-muted); padding: 2rem; }
.invalidate-confirm { width: 380px; text-align: center; padding: 2rem 1.5rem; }
.confirm-icon { margin-bottom: 0.75rem; }
.invalidate-confirm h3 { margin: 0 0 0.5rem; font-size: 1.1rem; }
.invalidate-confirm p { margin: 0 0 0.5rem; font-size: 0.85rem; color: var(--text-secondary); line-height: 1.6; }
.warn-note { font-size: 0.78rem !important; color: var(--text-muted) !important; }
.confirm-actions { display: flex; gap: 0.75rem; justify-content: center; margin-top: 1.25rem; }
.btn-solid-danger { background: linear-gradient(135deg, #ef4444, #dc2626); color: #fff; border: none; padding: 0.5rem 1.25rem; border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 500; transition: all 0.2s; box-shadow: 0 2px 8px rgba(239,68,68,0.3); }
.btn-solid-danger:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(239,68,68,0.4); }
.current-balance { font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 0.75rem; }
.topup-input { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; }
.topup-input .prefix { font-size: 1.2rem; color: var(--text-secondary); }
.topup-input input { flex: 1; padding: 0.5rem; font-size: 1rem; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-primary); color: var(--text-primary); outline: none; }
.topup-input input:focus { border-color: var(--accent); }
.modal-sm { width: 360px; }
.invalidate-modal { width: 480px; padding: 0; overflow: hidden; }
.invalidate-header { display: flex; align-items: flex-start; gap: 0.75rem; padding: 1.25rem 1.5rem; background: var(--bg-primary); border-bottom: 1px solid var(--border); }
.invalidate-header h3 { margin: 0; font-size: 1rem; font-weight: 600; }
.invalidate-subtitle { margin: 0.25rem 0 0; font-size: 0.8rem; color: var(--text-secondary); }
.invalidate-body { padding: 1.25rem 1.5rem; }
.uuid-section label { display: block; font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }
.sync-section { margin-top: 1rem; }
.sync-section label { display: block; font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }
.sync-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0.5rem; border-radius: 6px; font-size: 0.8rem; margin-bottom: 0.25rem; }
.sync-ok { color: var(--success); background: rgba(34,197,94,0.06); }
.sync-found { color: var(--accent); background: rgba(56,189,248,0.06); }
.sync-fail { color: var(--danger); background: rgba(239,68,68,0.06); }
.sync-err { font-size: 0.75rem; color: var(--text-muted); margin-left: auto; }
.uuid-row { display: flex; align-items: center; gap: 0.5rem; background: var(--bg-primary); border: 1px solid var(--border); border-radius: 8px; padding: 0.5rem 0.75rem; }
.uuid-value { flex: 1; font-size: 0.85rem; color: var(--accent); word-break: break-all; font-family: 'SF Mono', 'Fira Code', monospace; user-select: all; }
.copy-btn { display: flex; align-items: center; gap: 0.35rem; background: var(--bg-hover); border: 1px solid var(--border); border-radius: 6px; padding: 0.35rem 0.65rem; cursor: pointer; font-size: 0.78rem; color: var(--text-primary); white-space: nowrap; transition: all 0.15s; }
.copy-btn:hover { background: var(--border-solid); border-color: var(--accent); color: var(--accent); }
.invalidate-tip { display: flex; align-items: flex-start; gap: 0.5rem; margin-top: 1rem; padding: 0.75rem; background: rgba(239,68,68,0.06); border: 1px solid rgba(239,68,68,0.15); border-radius: 8px; font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5; }
.invalidate-tip svg { flex-shrink: 0; margin-top: 1px; }
.invalidate-footer { padding: 1rem 1.5rem; border-top: 1px solid var(--border); display: flex; justify-content: flex-end; }
.error { color: var(--danger); font-size: 0.85rem; margin-bottom: 0.5rem; }
.success { color: var(--success); font-size: 0.85rem; margin-bottom: 0.5rem; }
.action-cell { position: relative; }
.dropdown-wrap { position: relative; display: inline-block; }
.dropup .dropdown-menu { top: auto; bottom: 100%; margin-top: 0; margin-bottom: 4px; }
.btn-more { background: var(--bg-hover); border: 1px solid var(--border); border-radius: 6px; cursor: pointer; font-size: 1.1rem; line-height: 1; padding: 0.25rem 0.6rem; color: var(--text-muted); letter-spacing: 2px; transition: all 0.2s; }
.btn-more:hover { background: var(--border-solid); color: var(--text-primary); }
.dropdown-menu { position: absolute; right: 0; top: 100%; margin-top: 4px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 10px; box-shadow: 0 8px 24px rgba(0,0,0,0.12); z-index: 50; min-width: 140px; padding: 0.35rem; backdrop-filter: blur(12px); }
.dropdown-item { display: flex; align-items: center; gap: 0.5rem; width: 100%; padding: 0.5rem 0.75rem; border: none; background: none; color: var(--text-primary); font-size: 0.8rem; cursor: pointer; border-radius: 6px; text-align: left; transition: background 0.15s; }
.dropdown-item:hover { background: var(--bg-hover); }
.dropdown-item:disabled { opacity: 0.4; cursor: not-allowed; }
.dropdown-danger { color: var(--danger); }
.dropdown-danger:hover { background: rgba(239,68,68,0.08); }
.dropdown-divider { height: 1px; background: var(--border); margin: 0.25rem 0.5rem; }
</style>
