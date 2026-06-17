<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'

interface User {
  id: number; username: string; email: string; plan_name: string | null; traffic_used: number; traffic_total: number; expire_date: string | null; is_active?: boolean; balance?: number
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

onMounted(async () => {
  const [u, p] = await Promise.all([
    api.get('/admin/users/'),
    api.get('/admin/plans/'),
  ])
  users.value = u.data
  plans.value = p.data
})

function openEdit(u: User) {
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

  await api.patch(`/admin/users/${editing.value!.id}/update_user/`, payload)
  showEdit.value = false
  const { data } = await api.get('/admin/users/')
  users.value = data
}

function formatMB(mb: number) {
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`
  return `${mb} MB`
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
        <div class="form-actions">
          <button @click="showEdit = false" class="btn-secondary">取消</button>
          <button @click="saveEdit" class="btn-primary">保存</button>
        </div>
      </div>
    </div>

    <div class="table-wrapper">
      <table class="data-table">
        <thead><tr><th>ID</th><th>用户名</th><th>邮箱</th><th>套餐</th><th>已用/总量</th><th>到期</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td>{{ u.id }}</td>
            <td>{{ u.username }}</td>
            <td>{{ u.email }}</td>
            <td>{{ u.plan_name || '无' }}</td>
            <td>{{ formatMB(u.traffic_used) }} / {{ formatMB(u.traffic_total) }}</td>
            <td>{{ u.expire_date ? new Date(u.expire_date).toLocaleDateString('zh-CN') : '无' }}</td>
            <td><span :class="['badge', u.is_active !== false ? 'active' : 'inactive']">{{ u.is_active !== false ? '正常' : '停用' }}</span></td>
            <td><button @click="openEdit(u)" class="btn-sm">编辑</button></td>
          </tr>
          <tr v-if="!users.length"><td colspan="8" class="empty">暂无数据</td></tr>
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
</style>
