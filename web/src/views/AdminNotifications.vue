<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'

const notifications = ref<any[]>([])
const showForm = ref(false)
const editing = ref<any | null>(null)
const form = ref({ title: '', content: '', is_pinned: false, is_active: true })
const error = ref('')

async function load() {
  try {
    const { data } = await api.get('/admin/notifications/')
    notifications.value = data
  } catch {
    // fail silently
  }
}

function openCreate() {
  editing.value = null
  form.value = { title: '', content: '', is_pinned: false, is_active: true }
  error.value = ''
  showForm.value = true
}

function openEdit(n: any) {
  editing.value = n
  form.value = { title: n.title, content: n.content, is_pinned: n.is_pinned, is_active: n.is_active }
  error.value = ''
  showForm.value = true
}

async function save() {
  error.value = ''
  if (!form.value.title.trim()) { error.value = '标题不能为空'; return }
  if (!form.value.content.trim()) { error.value = '内容不能为空'; return }
  try {
    if (editing.value) {
      await api.patch(`/admin/notifications/${editing.value.id}/`, form.value)
    } else {
      await api.post('/admin/notifications/', form.value)
    }
    showForm.value = false
    await load()
  } catch {
    error.value = '保存失败'
  }
}

async function remove(n: any) {
  if (!confirm(`确认删除通知 "${n.title}"？`)) return
  await api.delete(`/admin/notifications/${n.id}/`)
  await load()
}

onMounted(load)
</script>

<template>
  <div class="admin-page">
    <header>
      <h2>通知管理</h2>
      <button @click="openCreate" class="btn-primary">+ 发布通知</button>
    </header>

    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal">
        <h3>{{ editing ? '编辑通知' : '发布新通知' }}</h3>
        <div class="form-group">
          <label>标题</label>
          <input v-model="form.title" placeholder="通知标题" />
        </div>
        <div class="form-group">
          <label>内容</label>
          <textarea v-model="form.content" rows="5" placeholder="通知内容..."></textarea>
        </div>
        <div class="form-row">
          <label class="checkbox-label">
            <input v-model="form.is_pinned" type="checkbox" /> 置顶
          </label>
          <label class="checkbox-label">
            <input v-model="form.is_active" type="checkbox" /> 显示
          </label>
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <div class="form-actions">
          <button @click="showForm = false" class="btn-secondary">取消</button>
          <button @click="save" class="btn-primary">{{ editing ? '保存修改' : '立即发布' }}</button>
        </div>
      </div>
    </div>

    <div v-if="!notifications.length" class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
      <p>暂无通知，点击上方"+ 发布通知"创建第一条通知</p>
    </div>

    <div v-else class="table-wrapper">
      <table class="data-table">
        <thead><tr><th>标题</th><th>置顶</th><th>显示</th><th>时间</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="n in notifications" :key="n.id">
            <td class="cell-title">{{ n.title }}</td>
            <td><span v-if="n.is_pinned" class="badge badge-pin">置顶</span></td>
            <td><span :class="['badge', n.is_active ? 'badge-active' : 'badge-inactive']">{{ n.is_active ? '显示' : '隐藏' }}</span></td>
            <td class="cell-date">{{ new Date(n.created_at).toLocaleDateString('zh-CN') }}</td>
            <td class="cell-actions">
              <button @click="openEdit(n)" class="btn-action">编辑</button>
              <button @click="remove(n)" class="btn-action btn-action-danger">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.admin-page { max-width: 800px; }
header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; }
header h2 { margin: 0; }

.empty-state { display: flex; flex-direction: column; align-items: center; gap: 1rem; padding: 3rem; background: var(--bg-card); backdrop-filter: blur(12px); border-radius: var(--radius); border: 1px solid var(--border); text-align: center; color: var(--text-muted); font-size: 0.9rem; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 100; backdrop-filter: blur(4px); }
.modal { background: var(--bg-card); backdrop-filter: blur(16px); padding: 1.5rem; border-radius: var(--radius); border: 1px solid var(--border); width: 520px; box-shadow: var(--shadow); }
.modal h3 { margin-bottom: 1rem; font-size: 1.05rem; }
.form-group { margin-bottom: 0.85rem; }
.form-group label { display: block; font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.3rem; font-weight: 500; }
.form-group input, .form-group textarea { width: 100%; padding: 0.55rem 0.65rem; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-primary); color: var(--text-primary); outline: none; font-family: inherit; font-size: 0.9rem; transition: border-color 0.2s; }
.form-group input:focus, .form-group textarea:focus { border-color: var(--accent); }
.form-row { display: flex; gap: 1.5rem; margin-bottom: 0.75rem; }
.checkbox-label { display: flex; align-items: center; gap: 0.4rem; font-size: 0.85rem; color: var(--text-secondary); cursor: pointer; }
.checkbox-label input { width: auto; margin: 0; }
.form-actions { display: flex; gap: 0.5rem; justify-content: flex-end; margin-top: 1.25rem; }
.error { color: var(--danger); font-size: 0.85rem; margin-bottom: 0.5rem; }

.table-wrapper { background: var(--bg-card); backdrop-filter: blur(12px); border-radius: var(--radius); border: 1px solid var(--border); overflow: hidden; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { padding: 0.7rem 1rem; text-align: left; font-size: 0.875rem; }
.data-table th { background: var(--bg-primary); color: var(--text-secondary); font-weight: 500; border-bottom: 1px solid var(--border); white-space: nowrap; }
.data-table td { border-bottom: 1px solid var(--border); }
.data-table tbody tr:last-child td { border-bottom: none; }
.data-table tbody tr:hover { background: var(--bg-hover); }
.cell-title { font-weight: 500; }
.cell-date { color: var(--text-muted); font-size: 0.8rem; white-space: nowrap; }
.cell-actions { white-space: nowrap; }
.badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.72rem; font-weight: 500; }
.badge-pin { background: var(--accent-soft); color: var(--accent); }
.badge-active { background: rgba(34,197,94,0.15); color: var(--success); }
.badge-inactive { background: rgba(239,68,68,0.15); color: var(--danger); }
.btn-action { background: var(--bg-hover); color: var(--text-primary); border: 1px solid var(--border); padding: 0.35rem 0.7rem; border-radius: 5px; cursor: pointer; font-size: 0.8rem; transition: all 0.15s; margin-right: 0.3rem; }
.btn-action:hover { background: var(--border-solid); }
.btn-action-danger { border-color: transparent; background: rgba(239,68,68,0.12); color: var(--danger); }
.btn-action-danger:hover { background: rgba(239,68,68,0.25); }
.btn-primary { background: var(--accent-gradient); color: #fff; border: none; padding: 0.5rem 1.1rem; border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 500; transition: all 0.2s; white-space: nowrap; }
.btn-primary:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(56,189,248,0.3); }
.btn-secondary { background: var(--bg-hover); color: var(--text-primary); border: 1px solid var(--border); padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; font-size: 0.85rem; transition: all 0.2s; }
.btn-secondary:hover { background: var(--border-solid); }
</style>
