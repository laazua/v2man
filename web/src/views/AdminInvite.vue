<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'

const settings = ref({ referral_percentage: '20', withdrawal_min: '3000' })
const settingsMsg = ref('')
const withdrawals = ref<any[]>([])
const tab = ref<'settings' | 'withdrawals'>('settings')

async function load() {
  const [s, w] = await Promise.all([
    api.get('/admin/invite/settings/').catch(() => ({ data: { referral_percentage: '20', withdrawal_min: '3000' } })),
    api.get('/admin/invite/withdrawals/').catch(() => ({ data: [] })),
  ])
  settings.value = s.data
  withdrawals.value = w.data
}

async function saveSettings() {
  settingsMsg.value = ''
  try {
    await api.put('/admin/invite/settings/', settings.value)
    settingsMsg.value = '保存成功'
  } catch {
    settingsMsg.value = '保存失败'
  }
}

async function handleWithdraw(id: number, action: 'approve' | 'reject') {
  try {
    await api.post(`/admin/invite/withdrawals/${id}/action/`, { action })
    await load()
  } catch {
    // fail silently
  }
}

onMounted(load)
</script>

<template>
  <div class="admin-page">
    <h2>邀请管理</h2>

    <div class="tabs">
      <button :class="['tab', { active: tab === 'settings' }]" @click="tab = 'settings'">返现设置</button>
      <button :class="['tab', { active: tab === 'withdrawals' }]" @click="tab = 'withdrawals'">提现审核 <span v-if="withdrawals.filter(w => w.status === 'pending').length" class="badge">{{ withdrawals.filter(w => w.status === 'pending').length }}</span></button>
    </div>

    <div v-if="tab === 'settings'" class="settings-section">
      <div class="form-group">
        <label>返现比例 (%)</label>
        <input v-model="settings.referral_percentage" type="number" min="0" max="100" />
      </div>
      <div class="form-group">
        <label>最低提现金额 (分)</label>
        <input v-model="settings.withdrawal_min" type="number" min="0" />
        <p class="hint">当前为 ¥{{ (Number(settings.withdrawal_min) / 100).toFixed(2) }}</p>
      </div>
      <button @click="saveSettings" class="btn-primary">保存设置</button>
      <p v-if="settingsMsg" class="msg">{{ settingsMsg }}</p>
    </div>

    <div v-else class="withdrawals-section">
      <div v-if="!withdrawals.length" class="empty">暂无提现申请</div>
      <div v-for="w in withdrawals" :key="w.id" class="w-row">
        <div class="w-info">
          <strong>{{ w.username }}</strong>
          <span>¥{{ (w.amount / 100).toFixed(2) }}</span>
          <span :class="['status-badge', w.status]">{{ ({ pending: '待审核', approved: '已通过', rejected: '已拒绝' } as Record<string, string>)[w.status] || w.status }}</span>
          <span class="date">{{ new Date(w.created_at).toLocaleDateString('zh-CN') }}</span>
        </div>
        <div v-if="w.status === 'pending'" class="w-actions">
          <button @click="handleWithdraw(w.id, 'approve')" class="btn-approve">通过</button>
          <button @click="handleWithdraw(w.id, 'reject')" class="btn-reject">拒绝</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-page { max-width: 700px; }
h2 { margin-bottom: 1.5rem; }

.tabs { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }
.tab { padding: 0.5rem 1rem; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-card); color: var(--text-secondary); cursor: pointer; font-size: 0.85rem; transition: all 0.2s; }
.tab.active { background: var(--accent-gradient); color: #fff; border-color: transparent; }
.tab .badge { background: rgba(255,255,255,0.25); padding: 0.1rem 0.4rem; border-radius: 4px; font-size: 0.7rem; margin-left: 0.25rem; }

.settings-section { background: var(--bg-card); backdrop-filter: blur(12px); padding: 1.25rem; border-radius: var(--radius); border: 1px solid var(--border); }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.35rem; }
.form-group input { width: 100%; padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-primary); color: var(--text-primary); font-size: 0.9rem; outline: none; }
.form-group input:focus { border-color: var(--accent); }
.hint { font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem; }
.btn-primary { background: var(--accent-gradient); color: #fff; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 500; transition: all 0.2s; }
.btn-primary:hover { transform: translateY(-1px); }
.msg { margin-top: 0.75rem; color: var(--success); font-size: 0.85rem; }

.w-row { display: flex; align-items: center; justify-content: space-between; gap: 1rem; padding: 0.75rem 1rem; background: var(--bg-card); backdrop-filter: blur(12px); border-radius: var(--radius); border: 1px solid var(--border); margin-bottom: 0.5rem; }
.w-info { display: flex; align-items: center; gap: 1rem; font-size: 0.85rem; }
.w-actions { display: flex; gap: 0.5rem; }
.btn-approve { background: rgba(34,197,94,0.15); color: var(--success); border: 1px solid transparent; padding: 0.3rem 0.75rem; border-radius: 6px; cursor: pointer; font-size: 0.8rem; }
.btn-approve:hover { background: rgba(34,197,94,0.25); }
.btn-reject { background: rgba(239,68,68,0.15); color: var(--danger); border: 1px solid transparent; padding: 0.3rem 0.75rem; border-radius: 6px; cursor: pointer; font-size: 0.8rem; }
.btn-reject:hover { background: rgba(239,68,68,0.25); }
.status-badge { font-size: 0.75rem; padding: 0.15rem 0.5rem; border-radius: 4px; }
.status-badge.pending { background: rgba(245,158,11,0.15); color: var(--warning); }
.status-badge.approved { background: rgba(34,197,94,0.15); color: var(--success); }
.status-badge.rejected { background: rgba(239,68,68,0.15); color: var(--danger); }
.date { color: var(--text-muted); font-size: 0.8rem; }
.empty { text-align: center; color: var(--text-muted); padding: 2rem; }
</style>
