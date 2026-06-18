<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'
import type { Node } from '../types'

const nodes = ref<Node[]>([])
const editing = ref<Node | null>(null)
const showForm = ref(false)
const sshAuthType = ref<'key' | 'password'>('key')
const form = ref({
  name: '', protocol: 'vless', address: '', port: 443,
  config: '{}', config_path: '/etc/v2ray/config.json',
  reload_cmd: 'systemctl restart v2ray',
  sort_order: 0, is_active: true,
  ssh_host: '', ssh_port: 22, ssh_user: 'root',
  ssh_key: '', ssh_password: '',
})
const error = ref('')
const deploying = ref<number | null>(null)
const deployMsg = ref('')

onMounted(() => loadNodes())

async function loadNodes() {
  const { data } = await api.get('/admin/nodes/')
  nodes.value = data
}

function openCreate() {
  editing.value = null
  sshAuthType.value = 'key'
  form.value = { name: '', protocol: 'vless', address: '', port: 443, config: '{}', config_path: '/etc/v2ray/config.json', reload_cmd: 'systemctl restart v2ray', sort_order: 0, is_active: true, ssh_host: '', ssh_port: 22, ssh_user: 'root', ssh_key: '', ssh_password: '' }
  showForm.value = true
}

function openEdit(node: Node) {
  editing.value = node
  sshAuthType.value = 'key'
  form.value = {
    name: node.name,
    protocol: node.protocol,
    address: node.address,
    port: node.port,
    config: JSON.stringify(node.config, null, 2),
    config_path: node.config_path,
    reload_cmd: node.reload_cmd,
    sort_order: node.sort_order,
    is_active: true,
    ssh_host: node.ssh_host || '',
    ssh_port: node.ssh_port || 22,
    ssh_user: node.ssh_user || 'root',
    ssh_key: '',
    ssh_password: '',
  }
  showForm.value = true
}

async function save() {
  error.value = ''
  try {
    let config: Record<string, string> = {}
    const raw = form.value.config.trim()
    if (raw) {
      try { config = JSON.parse(raw) } catch { error.value = '配置格式无效 (需 JSON)'; return }
    }
    const payload: Record<string, any> = { ...form.value, config }
    if (sshAuthType.value === 'key') {
      delete payload.ssh_password
      if (!payload.ssh_key) delete payload.ssh_key
    } else {
      delete payload.ssh_key
      if (!payload.ssh_password) delete payload.ssh_password
    }
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

async function deploy(node: Node) {
  deployMsg.value = ''
  deploying.value = node.id
  try {
    const { data } = await api.post(`/admin/nodes/${node.id}/deploy/`)
    if (data.success) {
      deployMsg.value = `${node.name} 部署成功`
    } else {
      deployMsg.value = `部署失败: ${data.error}`
    }
    await loadNodes()
  } catch (e: any) {
    deployMsg.value = e.response?.data?.error || '请求失败'
  } finally {
    deploying.value = null
  }
}
</script>

<template>
  <div class="admin-page">
    <header>
      <h2>节点管理</h2>
      <button @click="openCreate" class="btn-primary">+ 新增节点</button>
    </header>

    <p v-if="deployMsg" :class="deployMsg.includes('成功') ? 'success' : 'error'" style="margin-bottom:0.75rem">{{ deployMsg }}</p>

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
          <label>V2Ray 配置路径 <input v-model="form.config_path" /></label>
          <label>重启命令 <input v-model="form.reload_cmd" /></label>
        </div>
        <label>协议配置 (JSON)<textarea v-model="form.config" rows="4" placeholder='{"id":"uuid-xxxx","tls":true}'></textarea></label>
        <h4 style="margin-top:1rem;margin-bottom:0.5rem;font-size:0.85rem">SSH 连接</h4>
        <div class="form-grid">
          <label>SSH 地址 <input v-model="form.ssh_host" placeholder="留空使用节点地址" /></label>
          <label>SSH 端口 <input v-model.number="form.ssh_port" type="number" /></label>
          <label>SSH 用户 <input v-model="form.ssh_user" /></label>
          <label>认证方式
            <select v-model="sshAuthType">
              <option value="key">私钥</option>
              <option value="password">密码</option>
            </select>
          </label>
        </div>
        <label v-if="sshAuthType === 'key'">SSH 私钥
          <textarea v-model="form.ssh_key" rows="3" :placeholder="editing ? '留空不修改' : '-----BEGIN RSA PRIVATE KEY-----...'"></textarea>
        </label>
        <label v-else>SSH 密码
          <input v-model="form.ssh_password" type="password" :placeholder="editing ? '留空不修改' : '输入密码'" />
        </label>
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
          <tr><th>名称</th><th>协议</th><th>地址</th><th>端口</th><th>SSH</th><th>部署</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="node in nodes" :key="node.id">
            <td>{{ node.name }}</td>
            <td><span class="badge">{{ node.protocol }}</span></td>
            <td>{{ node.address }}</td>
            <td>{{ node.port }}</td>
            <td><span :class="node.ssh_configured ? 'badge badge-ok' : 'badge badge-miss'">{{ node.ssh_configured ? '已配置' : '未配置' }}</span></td>
            <td>
              <button v-if="node.ssh_configured" @click="deploy(node)" :disabled="deploying === node.id" class="btn-sm btn-deploy">
                {{ deploying === node.id ? '部署中...' : '部署 V2Ray' }}
              </button>
              <span v-else style="color:var(--text-muted);font-size:0.78rem">需先配置 SSH</span>
            </td>
            <td class="actions">
              <button @click="openEdit(node)" class="btn-sm">编辑</button>
              <button @click="remove(node)" class="btn-sm btn-danger">删除</button>
            </td>
          </tr>
          <tr v-if="!nodes.length"><td colspan="7" class="empty">暂无数据</td></tr>
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
.badge-ok { background: rgba(34,197,94,0.15); color: var(--success); }
.badge-miss { background: rgba(239,68,68,0.1); color: var(--text-muted); }
.actions { display: flex; gap: 0.5rem; }
.btn-sm { background: var(--bg-hover); color: var(--text-primary); border: 1px solid var(--border); padding: 0.375rem 0.75rem; border-radius: 6px; cursor: pointer; font-size: 0.8rem; transition: all 0.2s; }
.btn-sm:hover { background: var(--border-solid); }
.btn-danger { border-color: transparent; background: rgba(239,68,68,0.15); color: var(--danger); }
.btn-danger:hover { background: rgba(239,68,68,0.25); }
.btn-deploy { border-color: transparent; background: rgba(56,189,248,0.15); color: var(--accent); }
.btn-deploy:hover { background: rgba(56,189,248,0.25); }
.btn-deploy:disabled { opacity: 0.5; cursor: not-allowed; }
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
.success { color: var(--success); font-size: 0.85rem; }
.empty { text-align: center; color: var(--text-muted); padding: 2rem; }
</style>