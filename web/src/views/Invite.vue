<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api from '../api'
import { copiedKey, copyText } from '../api/copy'

const codes = ref<any[]>([])
const referrals = ref<any[]>([])
const earnings = ref({ total_earned: 0, total_referees: 0, percentage: 20 })
const withdrawals = ref<any[]>([])
const withdrawAmount = ref(0)
const withdrawMsg = ref('')
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    const [c, r, e, w] = await Promise.all([
      api.get('/invite/codes/').catch(() => ({ data: [] })),
      api.get('/invite/referrals/').catch(() => ({ data: [] })),
      api.get('/invite/earnings/').catch(() => ({ data: { total_earned: 0, total_referees: 0, percentage: 20 } })),
      api.get('/invite/withdrawals/').catch(() => ({ data: [] })),
    ])
    codes.value = c.data
    referrals.value = r.data
    earnings.value = e.data
    withdrawals.value = w.data
  } finally {
    loading.value = false
  }
}

async function generateCode() {
  try {
    const { data } = await api.post('/invite/codes/generate/')
    codes.value.unshift(data)
  } catch {
    // fail silently
  }
}

function shareLink(code: string) {
  const url = `${window.location.origin}/register?invite=${code}`
  copyText(url, `share-${code}`)
}

async function submitWithdraw() {
  withdrawMsg.value = ''
  if (!withdrawAmount.value || withdrawAmount.value < 1) return
  const amount = Math.round(withdrawAmount.value * 100)
  try {
    await api.post('/invite/withdrawals/create/', { amount })
    withdrawMsg.value = '提现申请已提交，等待管理员审核'
    withdrawAmount.value = 0
    await load()
  } catch (e: any) {
    withdrawMsg.value = e.response?.data?.error || '提交失败'
  }
}

const totalEarnedYuan = computed(() => (earnings.value.total_earned / 100).toFixed(2))

onMounted(load)
</script>

<template>
  <div class="invite-page">
    <h2>邀请返现</h2>

    <div v-if="loading" class="loading">加载中...</div>

    <template v-else>
      <div class="stats-row">
        <div class="stat-card">
          <span class="stat-value">¥{{ totalEarnedYuan }}</span>
          <span class="stat-label">累计返现</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{{ earnings.total_referees }}</span>
          <span class="stat-label">邀请人数</span>
        </div>
        <div class="stat-card">
          <span class="stat-value">{{ earnings.percentage }}%</span>
          <span class="stat-label">返现比例</span>
        </div>
      </div>

      <div class="section">
        <div class="section-header">
          <h3>邀请码</h3>
          <button @click="generateCode" class="btn-primary btn-sm">生成新码</button>
        </div>
        <div v-if="codes.length === 0" class="empty">暂无邀请码</div>
        <div v-for="code in codes" :key="code.code" class="code-row">
          <code class="code-value">{{ code.code }}</code>
          <span class="code-status" :class="{ active: code.is_active }">{{ code.is_active ? '有效' : '已失效' }}</span>
          <button @click="shareLink(code.code)" class="btn-copy">{{ copiedKey === `share-${code.code}` ? '已复制' : '复制链接' }}</button>
        </div>
      </div>

      <div class="section">
        <h3>邀请记录</h3>
        <div v-if="referrals.length === 0" class="empty">暂无邀请记录</div>
        <div v-for="ref in referrals" :key="ref.invited_username" class="ref-row">
          <div class="ref-user">{{ ref.invited_username }}</div>
          <div class="ref-date">{{ new Date(ref.created_at).toLocaleDateString('zh-CN') }}</div>
          <div class="ref-earned">+¥{{ (ref.earned / 100).toFixed(2) }}</div>
        </div>
      </div>

      <div class="section">
        <h3>提现</h3>
        <div class="withdraw-form">
          <div class="amount-input">
            <span class="prefix">¥</span>
            <input v-model.number="withdrawAmount" type="number" min="1" step="0.01" placeholder="输入提现金额" />
          </div>
          <button @click="submitWithdraw" :disabled="!withdrawAmount || withdrawAmount < 1" class="btn-primary">提交提现</button>
          <p v-if="withdrawMsg" class="msg">{{ withdrawMsg }}</p>
        </div>
        <div v-if="withdrawals.length > 0" class="withdraw-list">
          <div v-for="w in withdrawals" :key="w.id" class="withdraw-row">
            <span>¥{{ (w.amount / 100).toFixed(2) }}</span>
            <span :class="['status-badge', w.status]">{{ { pending: '待审核', approved: '已通过', rejected: '已拒绝' }[w.status] || w.status }}</span>
            <span class="date">{{ new Date(w.created_at).toLocaleDateString('zh-CN') }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.invite-page { max-width: 700px; }
h2 { margin-bottom: 1.5rem; }
h3 { margin: 0 0 1rem; font-size: 1rem; }
.loading { text-align: center; color: var(--text-muted); padding: 3rem; }

.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; margin-bottom: 1.5rem; }
.stat-card { background: var(--bg-card); backdrop-filter: blur(12px); padding: 1.25rem; border-radius: var(--radius); border: 1px solid var(--border); text-align: center; }
.stat-value { display: block; font-size: 1.5rem; font-weight: 700; color: var(--accent); }
.stat-label { display: block; font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem; }

.section { background: var(--bg-card); backdrop-filter: blur(12px); padding: 1.25rem; border-radius: var(--radius); border: 1px solid var(--border); margin-bottom: 1rem; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
.section-header h3 { margin: 0; }

.code-row { display: flex; align-items: center; gap: 0.75rem; padding: 0.625rem 0; border-bottom: 1px solid var(--border); }
.code-row:last-child { border-bottom: none; }
.code-value { font-size: 0.9rem; font-weight: 600; color: var(--text-primary); letter-spacing: 0.05em; flex: 1; }
.code-status { font-size: 0.75rem; padding: 0.15rem 0.5rem; border-radius: 4px; background: var(--bg-hover); color: var(--text-muted); }
.code-status.active { background: rgba(34,197,94,0.15); color: var(--success); }
.btn-copy { background: var(--accent); color: #fff; border: none; padding: 0.3rem 0.75rem; border-radius: 6px; cursor: pointer; font-size: 0.75rem; white-space: nowrap; transition: all 0.2s; }
.btn-copy:hover { opacity: 0.9; }

.ref-row { display: flex; align-items: center; gap: 1rem; padding: 0.5rem 0; border-bottom: 1px solid var(--border); font-size: 0.85rem; }
.ref-row:last-child { border-bottom: none; }
.ref-user { flex: 1; font-weight: 500; }
.ref-date { color: var(--text-muted); font-size: 0.8rem; }
.ref-earned { color: var(--success); font-weight: 600; }

.withdraw-form { display: flex; gap: 0.75rem; align-items: center; flex-wrap: wrap; margin-bottom: 1rem; }
.amount-input { display: flex; align-items: center; flex: 1; min-width: 200px; }
.prefix { font-size: 1.2rem; margin-right: 0.35rem; color: var(--text-secondary); }
.amount-input input { flex: 1; padding: 0.5rem; font-size: 1rem; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-primary); color: var(--text-primary); outline: none; }
.amount-input input:focus { border-color: var(--accent); }
.btn-primary { background: var(--accent-gradient); color: #fff; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 500; transition: all 0.2s; white-space: nowrap; }
.btn-primary:hover:not(:disabled) { transform: translateY(-1px); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-sm { padding: 0.35rem 0.75rem; font-size: 0.8rem; }
.msg { width: 100%; color: var(--success); font-size: 0.85rem; }

.withdraw-row { display: flex; align-items: center; gap: 1rem; padding: 0.5rem 0; border-bottom: 1px solid var(--border); font-size: 0.85rem; }
.withdraw-row:last-child { border-bottom: none; }
.status-badge { font-size: 0.75rem; padding: 0.15rem 0.5rem; border-radius: 4px; }
.status-badge.pending { background: rgba(245,158,11,0.15); color: var(--warning); }
.status-badge.approved { background: rgba(34,197,94,0.15); color: var(--success); }
.status-badge.rejected { background: rgba(239,68,68,0.15); color: var(--danger); }
.date { color: var(--text-muted); font-size: 0.8rem; }
.empty { color: var(--text-muted); text-align: center; padding: 1.5rem; font-size: 0.85rem; }
</style>
