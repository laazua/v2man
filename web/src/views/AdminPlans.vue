<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'

interface Plan {
  id: number; name: string; price: string; traffic_limit: number; duration_days: number; is_active: boolean; sort_order: number
}

const plans = ref<Plan[]>([])
const editing = ref<Plan | null>(null)
const showForm = ref(false)
const form = ref({ name: '', price: 0, traffic_limit: 1024, duration_days: 30, is_active: true, sort_order: 0 })
const error = ref('')

onMounted(() => load())

async function load() {
  const { data } = await api.get('/admin/plans/')
  plans.value = data
}

function openCreate() {
  editing.value = null
  form.value = { name: '', price: 0, traffic_limit: 1024, duration_days: 30, is_active: true, sort_order: 0 }
  showForm.value = true
}

function openEdit(p: Plan) {
  editing.value = p
  form.value = { name: p.name, price: Number(p.price), traffic_limit: p.traffic_limit, duration_days: p.duration_days, is_active: p.is_active, sort_order: p.sort_order }
  showForm.value = true
}

async function save() {
  error.value = ''
  try {
    const payload = { ...form.value, price: String(form.value.price) }
    if (editing.value) {
      await api.put(`/admin/plans/${editing.value.id}/`, payload)
    } else {
      await api.post('/admin/plans/', payload)
    }
    showForm.value = false
    await load()
  } catch (e: any) {
    error.value = e.response?.data?.detail || '保存失败'
  }
}

async function remove(p: Plan) {
  if (!confirm(`确认删除 "${p.name}"？`)) return
  await api.delete(`/admin/plans/${p.id}/`)
  await load()
}
</script>

<template>
  <div class="admin-page">
    <header>
      <h2>套餐管理</h2>
      <button @click="openCreate" class="btn-primary">+ 新增套餐</button>
    </header>

    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal">
        <h3>{{ editing ? '编辑套餐' : '新增套餐' }}</h3>
        <div class="form-grid">
          <label>名称 <input v-model="form.name" /></label>
          <label>价格 (元) <input v-model.number="form.price" type="number" step="0.01" /></label>
          <label>流量上限 (MB) <input v-model.number="form.traffic_limit" type="number" /></label>
          <label>有效期 (天) <input v-model.number="form.duration_days" type="number" /></label>
          <label>排序 <input v-model.number="form.sort_order" type="number" /></label>
          <label>启用 <select v-model="form.is_active"><option :value="true">是</option><option :value="false">否</option></select></label>
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <div class="form-actions">
          <button @click="showForm = false" class="btn-secondary">取消</button>
          <button @click="save" class="btn-primary">保存</button>
        </div>
      </div>
    </div>

    <div class="table-wrapper">
      <table class="data-table">
        <thead><tr><th>名称</th><th>价格</th><th>流量</th><th>天数</th><th>启用</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="p in plans" :key="p.id">
            <td>{{ p.name }}</td><td>¥{{ p.price }}</td><td>{{ p.traffic_limit }} MB</td><td>{{ p.duration_days }} 天</td>
            <td>{{ p.is_active ? '是' : '否' }}</td>
            <td class="actions">
              <button @click="openEdit(p)" class="btn-sm">编辑</button>
              <button @click="remove(p)" class="btn-sm btn-danger">删除</button>
            </td>
          </tr>
          <tr v-if="!plans.length"><td colspan="6" class="empty">暂无数据</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.admin-page { max-width: 1000px; }
header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.table-wrapper { background: var(--bg-card); backdrop-filter: blur(12px); border-radius: var(--radius); border: 1px solid var(--border); overflow: hidden; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { padding: 0.75rem 1rem; text-align: left; font-size: 0.875rem; }
.data-table th { background: var(--bg-primary); color: var(--text-secondary); font-weight: 500; border-bottom: 1px solid var(--border); }
.data-table td { border-bottom: 1px solid var(--border); }
.data-table tbody tr:last-child td { border-bottom: none; }
.data-table tbody tr:hover { background: var(--bg-hover); }
.actions { display: flex; gap: 0.5rem; }
.btn-sm { background: var(--bg-hover); color: var(--text-primary); border: 1px solid var(--border); padding: 0.375rem 0.75rem; border-radius: 6px; cursor: pointer; font-size: 0.8rem; transition: all 0.2s; }
.btn-sm:hover { background: var(--border-solid); }
.btn-danger { border-color: transparent; background: rgba(239,68,68,0.15); color: var(--danger); }
.btn-danger:hover { background: rgba(239,68,68,0.25); }
.btn-primary { background: var(--accent-gradient); color: #fff; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 500; transition: all 0.2s; }
.btn-primary:hover { transform: translateY(-1px); }
.btn-secondary { background: var(--bg-hover); color: var(--text-primary); border: 1px solid var(--border); padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; font-size: 0.85rem; transition: all 0.2s; }
.btn-secondary:hover { background: var(--border-solid); }
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 100; backdrop-filter: blur(4px); }
.modal { background: var(--bg-card); backdrop-filter: blur(12px); padding: 1.5rem; border-radius: var(--radius); border: 1px solid var(--border); width: 500px; box-shadow: var(--shadow); }
.modal h3 { margin-bottom: 1rem; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin: 1rem 0; }
label { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.8rem; color: var(--text-secondary); }
input, select { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-primary); color: var(--text-primary); outline: none; transition: border-color 0.2s; }
input:focus, select:focus { border-color: var(--accent); }
.form-actions { display: flex; gap: 0.5rem; justify-content: flex-end; margin-top: 1rem; }
.error { color: var(--danger); font-size: 0.85rem; }
.empty { text-align: center; color: var(--text-muted); padding: 2rem; }
</style>
