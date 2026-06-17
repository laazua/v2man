<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'
import type { Node } from '../types'

const nodes = ref<Node[]>([])
const editing = ref<Node | null>(null)
const showForm = ref(false)
const form = ref({ name: '', protocol: 'vless', address: '', port: 443, config: '{}', sort_order: 0, is_active: true })
const error = ref('')

onMounted(() => loadNodes())

async function loadNodes() {
  const { data } = await api.get('/admin/nodes/')
  nodes.value = data
}

function openCreate() {
  editing.value = null
  form.value = { name: '', protocol: 'vless', address: '', port: 443, config: '{}', sort_order: 0, is_active: true }
  showForm.value = true
}

function openEdit(node: Node) {
  editing.value = node
  form.value = {
    name: node.name,
    protocol: node.protocol,
    address: node.address,
    port: node.port,
    config: JSON.stringify(node.config, null, 2),
    sort_order: node.sort_order,
    is_active: true,
  }
  showForm.value = true
}

async function save() {
  error.value = ''
  try {
    let config: Record<string, string> = {}
    try { config = JSON.parse(form.value.config) } catch { error.value = '配置格式无效 (需 JSON)'; return }
    const payload = { ...form.value, config }
    if (editing.value) {
      await api.put(`/admin/nodes/${editing.value.id}/`, payload)
    } else {
      await api.post('/admin/nodes/', payload)
    }
    showForm.value = false
    await loadNodes()
  } catch (e: any) {
    error.value = e.response?.data?.detail || '保存失败'
  }
}

async function remove(node: Node) {
  if (!confirm(`确认删除节点 "${node.name}"？`)) return
  await api.delete(`/admin/nodes/${node.id}/`)
  await loadNodes()
}
</script>

<template>
  <div class="admin-page">
    <header>
      <h2>节点管理</h2>
      <button @click="openCreate" class="btn-primary">+ 新增节点</button>
    </header>

    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal">
        <h3>{{ editing ? '编辑节点' : '新增节点' }}</h3>
        <div class="form-grid">
          <label>名称 <input v-model="form.name" /></label>
          <label>协议
            <select v-model="form.protocol">
              <option v-for="p in ['vless','vmess','shadowsocks','trojan','hysteria2']" :key="p" :value="p">{{ p }}</option>
            </select>
          </label>
          <label>地址 <input v-model="form.address" /></label>
          <label>端口 <input v-model.number="form.port" type="number" /></label>
          <label>排序 <input v-model.number="form.sort_order" type="number" /></label>
        </div>
        <label>协议配置 (JSON)<textarea v-model="form.config" rows="4"></textarea></label>
        <p v-if="error" class="error">{{ error }}</p>
        <div class="form-actions">
          <button @click="showForm = false" class="btn-secondary">取消</button>
          <button @click="save" class="btn-primary">保存</button>
        </div>
      </div>
    </div>

    <div class="table-wrapper">
      <table class="data-table">
        <thead>
          <tr><th>名称</th><th>协议</th><th>地址</th><th>端口</th><th>排序</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="node in nodes" :key="node.id">
            <td>{{ node.name }}</td>
            <td><span class="badge">{{ node.protocol }}</span></td>
            <td>{{ node.address }}</td>
            <td>{{ node.port }}</td>
            <td>{{ node.sort_order }}</td>
            <td class="actions">
              <button @click="openEdit(node)" class="btn-sm">编辑</button>
              <button @click="remove(node)" class="btn-sm btn-danger">删除</button>
            </td>
          </tr>
          <tr v-if="!nodes.length"><td colspan="6" class="empty">暂无数据</td></tr>
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
.badge { background: var(--bg-hover); padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; color: var(--text-secondary); }
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
.modal { background: var(--bg-card); backdrop-filter: blur(12px); padding: 1.5rem; border-radius: var(--radius); border: 1px solid var(--border); width: 520px; max-height: 80vh; overflow-y: auto; box-shadow: var(--shadow); }
.modal h3 { margin-bottom: 1rem; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin: 1rem 0; }
label { display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.8rem; color: var(--text-secondary); }
input, select, textarea { padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-primary); color: var(--text-primary); outline: none; font-family: inherit; transition: border-color 0.2s; }
input:focus, select:focus, textarea:focus { border-color: var(--accent); }
.form-actions { display: flex; gap: 0.5rem; justify-content: flex-end; margin-top: 1rem; }
.error { color: var(--danger); font-size: 0.85rem; }
.empty { text-align: center; color: var(--text-muted); padding: 2rem; }
</style>
