<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'

const stats = ref({ users: 0, nodes: 0, plans: 0, pendingRecharges: 0 })

onMounted(async () => {
  try {
    const [users, nodes, plans, recharges] = await Promise.all([
      api.get('/admin/users/').catch(() => ({ data: [] })),
      api.get('/admin/nodes/').catch(() => ({ data: [] })),
      api.get('/admin/plans/').catch(() => ({ data: [] })),
      api.get('/admin/recharges/').catch(() => ({ data: [] })),
    ])
    stats.value = {
      users: users.data.length || users.data.count || 0,
      nodes: nodes.data.length || 0,
      plans: plans.data.length || 0,
      pendingRecharges: (recharges.data.results || recharges.data || []).filter(
        (r: any) => r.status === 'pending'
      ).length,
    }
  } catch {}
})
</script>

<template>
  <div class="admin-home">
    <h2>管理概览</h2>
    <div class="stats-grid">
      <div class="stat-card">
        <h3>{{ stats.users }}</h3>
        <p>用户总数</p>
      </div>
      <div class="stat-card">
        <h3>{{ stats.nodes }}</h3>
        <p>节点总数</p>
      </div>
      <div class="stat-card">
        <h3>{{ stats.plans }}</h3>
        <p>套餐数量</p>
      </div>
      <div class="stat-card warn">
        <h3>{{ stats.pendingRecharges }}</h3>
        <p>待审核充值</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
h2 { margin-bottom: 1.5rem; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 1rem; }
.stat-card { background: var(--bg-card); backdrop-filter: blur(12px); padding: 1.5rem; border-radius: var(--radius); border: 1px solid var(--border); text-align: center; transition: all 0.2s; }
.stat-card:hover { transform: translateY(-1px); box-shadow: var(--shadow); }
.stat-card h3 { font-size: 2rem; margin: 0 0 0.25rem; color: var(--accent); }
.stat-card p { color: var(--text-muted); font-size: 0.875rem; margin: 0; }
.stat-card.warn h3 { color: var(--warning); }
</style>
