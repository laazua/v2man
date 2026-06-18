<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'

const stats = ref({ users: 0, nodes: 0, plans: 0, pendingRecharges: 0 })
const pendingList = ref<any[]>([])

onMounted(async () => {
  try {
    const [users, nodes, plans, recharges] = await Promise.all([
      api.get('/admin/users/').catch(() => ({ data: [] })),
      api.get('/admin/nodes/').catch(() => ({ data: [] })),
      api.get('/admin/plans/').catch(() => ({ data: [] })),
      api.get('/admin/recharges/').catch(() => ({ data: [] })),
    ])
    const all = recharges.data.results || recharges.data || []
    pendingList.value = all.filter((r: any) => r.status === 'pending')
    stats.value = {
      users: users.data.length || users.data.count || 0,
      nodes: nodes.data.length || 0,
      plans: plans.data.length || 0,
      pendingRecharges: pendingList.value.length,
    }
  } catch {}
})

async function confirmRecharge(r: any) {
  try {
    await api.post(`/admin/recharges/${r.id}/confirm/`)
    r.status = 'completed'
    stats.value.pendingRecharges--
    pendingList.value = pendingList.value.filter(p => p.id !== r.id)
  } catch {}
}
</script>

<template>
  <div class="admin-home">
    <h2>管理概览</h2>
    <div class="stats-grid">
      <router-link to="/admin/users" class="stat-card card-users">
        <div class="card-bg-icon">
          <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
        </div>
        <div class="card-content">
          <div class="card-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          </div>
          <h3>{{ stats.users }}</h3>
          <p>用户总数</p>
        </div>
      </router-link>

      <router-link to="/admin/nodes" class="stat-card card-nodes">
        <div class="card-bg-icon">
          <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><circle cx="6" cy="6" r="1" fill="currentColor"/><circle cx="6" cy="18" r="1" fill="currentColor"/></svg>
        </div>
        <div class="card-content">
          <div class="card-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><circle cx="6" cy="6" r="1" fill="currentColor"/><circle cx="6" cy="18" r="1" fill="currentColor"/></svg>
          </div>
          <h3>{{ stats.nodes }}</h3>
          <p>节点总数</p>
        </div>
      </router-link>

      <router-link to="/admin/plans" class="stat-card card-plans">
        <div class="card-bg-icon">
          <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>
        </div>
        <div class="card-content">
          <div class="card-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg>
          </div>
          <h3>{{ stats.plans }}</h3>
          <p>套餐数量</p>
        </div>
      </router-link>

      <router-link to="/admin/recharges" class="stat-card card-recharges">
        <div class="card-bg-icon">
          <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="6" width="22" height="12" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M1 10h22"/></svg>
        </div>
        <div class="card-content">
          <div class="card-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="6" width="22" height="12" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M1 10h22"/></svg>
          </div>
          <h3>{{ stats.pendingRecharges }}</h3>
          <p>待审核充值</p>
        </div>
      </router-link>
    </div>

    <div v-if="pendingList.length" class="pending-section">
      <h3>待确认充值</h3>
      <div class="pending-list">
        <div v-for="r in pendingList" :key="r.id" class="pending-item">
          <span class="user-name">{{ r.username || r.user }}</span>
          <span class="amount">¥{{ (r.amount / 100).toFixed(2) }}</span>
          <span class="time">{{ new Date(r.created_at).toLocaleString('zh-CN') }}</span>
          <button @click="confirmRecharge(r)" class="btn-confirm">确认到账</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
h2 { margin-bottom: 1.5rem; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }

.stat-card {
  position: relative;
  display: block;
  text-decoration: none;
  border-radius: var(--radius);
  padding: 1.5rem;
  overflow: hidden;
  transition: all 0.25s;
}
.stat-card:hover { transform: translateY(-3px); }

.card-users { background: linear-gradient(135deg, #1e3a5f 0%, #2a4a7a 100%); border: 1px solid rgba(59,130,246,0.25); }
.card-users:hover { box-shadow: 0 8px 24px rgba(59,130,246,0.2); }
.card-users h3 { color: #60a5fa; }
.card-users .card-icon { color: #60a5fa; }

.card-nodes { background: linear-gradient(135deg, #1a3d3a 0%, #1f5a4a 100%); border: 1px solid rgba(52,211,153,0.25); }
.card-nodes:hover { box-shadow: 0 8px 24px rgba(52,211,153,0.2); }
.card-nodes h3 { color: #34d399; }
.card-nodes .card-icon { color: #34d399; }

.card-plans { background: linear-gradient(135deg, #2d1b4e 0%, #4a1d6b 100%); border: 1px solid rgba(168,85,247,0.25); }
.card-plans:hover { box-shadow: 0 8px 24px rgba(168,85,247,0.2); }
.card-plans h3 { color: #a78bfa; }
.card-plans .card-icon { color: #a78bfa; }

.card-recharges { background: linear-gradient(135deg, #3d2d0e 0%, #5c3d10 100%); border: 1px solid rgba(251,191,36,0.25); }
.card-recharges:hover { box-shadow: 0 8px 24px rgba(251,191,36,0.2); }
.card-recharges h3 { color: #fbbf24; }
.card-recharges .card-icon { color: #fbbf24; }

.card-bg-icon {
  position: absolute;
  right: -10px;
  bottom: -10px;
  opacity: 0.08;
  pointer-events: none;
}
.card-bg-icon svg { display: block; }

.card-content { position: relative; z-index: 1; }

.card-icon { margin-bottom: 0.5rem; }
.card-icon svg { display: block; }

.stat-card h3 { font-size: 2rem; margin: 0 0 0.2rem; font-weight: 700; }
.stat-card p { color: rgba(255,255,255,0.55); font-size: 0.85rem; margin: 0; font-weight: 500; }

.pending-section h3 { margin-bottom: 1rem; color: var(--text-primary); }
.pending-list { background: var(--bg-card); backdrop-filter: blur(12px); border-radius: var(--radius); border: 1px solid var(--border); overflow: hidden; }
.pending-item { display: flex; align-items: center; gap: 1rem; padding: 0.75rem 1rem; border-bottom: 1px solid var(--border); font-size: 0.875rem; }
.pending-item:last-child { border-bottom: none; }
.pending-item:hover { background: var(--bg-hover); }
.user-name { flex: 0 0 120px; font-weight: 500; color: var(--text-primary); }
.amount { flex: 0 0 80px; color: var(--accent); font-weight: 600; }
.time { flex: 1; color: var(--text-muted); font-size: 0.8rem; }
.btn-confirm { padding: 0.375rem 0.75rem; background: var(--success); color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 0.8rem; transition: all 0.2s; }
.btn-confirm:hover { transform: translateY(-1px); box-shadow: 0 2px 8px rgba(34,197,94,0.3); }
</style>
