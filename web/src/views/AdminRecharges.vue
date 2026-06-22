<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import api from '../api'
import { useRoute, useRouter } from 'vue-router'

interface Recharge {
  id: number; user: number; username?: string; amount: number; status: string; created_at: string; confirmed_at: string | null
}

const recharges = ref<Recharge[]>([])
const filter = ref('pending')
const search = ref('')
const route = useRoute()
const router = useRouter()

onMounted(() => {
  if (route.query.username) {
    search.value = route.query.username as string
  }
  load()
})

watch(search, () => {
  const query = search.value ? { username: search.value } : {}
  router.replace({ query })
  load()
})

async function load() {
  const params: Record<string, string> = {}
  if (search.value) params.username = search.value
  const { data } = await api.get('/admin/recharges/', { params })
  recharges.value = Array.isArray(data) ? data : data.results || []
}

async function confirm(r: Recharge) {
  try {
    await api.post(`/admin/recharges/${r.id}/confirm/`)
    r.status = 'completed'
  } catch {
    // API failed, don't update status optimistically
  }
}

async function reject(r: Recharge) {
  const remark = prompt('拒绝原因（可选）') || ''
  try {
    await api.post(`/admin/recharges/${r.id}/reject/`, { remark })
    r.status = 'failed'
  } catch {
    // API failed, don't update status
  }
}

function formatAmount(cents: number) {
  return `¥${(cents / 100).toFixed(2)}`
}

const filtered = computed(() => filter.value === 'all' ? recharges.value : recharges.value.filter(r => r.status === filter.value))
</script>

<template>
  <div class="admin-page">
    <header>
      <h2>充值审核</h2>
      <div class="header-right">
        <input v-model="search" placeholder="搜索用户名…" class="search-input" />
        <select v-model="filter" class="filter-select">
          <option value="pending">待审核</option>
          <option value="completed">已完成</option>
          <option value="failed">已拒绝</option>
          <option value="all">全部</option>
        </select>
      </div>
    </header>

    <div class="table-wrapper">
      <table class="data-table">
        <thead><tr><th>用户</th><th>金额</th><th>状态</th><th>提交时间</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="r in filtered" :key="r.id">
            <td>{{ r.username || r.user }}</td>
            <td>{{ formatAmount(r.amount) }}</td>
            <td><span :class="['badge', r.status]">{{ {pending:'待审核',completed:'已完成',failed:'已拒绝'}[r.status] }}</span></td>
            <td>{{ new Date(r.created_at).toLocaleString('zh-CN') }}</td>
            <td class="actions">
              <template v-if="r.status === 'pending'">
                <button @click="confirm(r)" class="btn-sm btn-success">确认到账</button>
                <button @click="reject(r)" class="btn-sm btn-danger">拒绝</button>
              </template>
              <span v-else class="muted">{{ r.status === 'completed' ? '已确认' : '已拒绝' }}</span>
            </td>
          </tr>
          <tr v-if="!filtered.length"><td colspan="5" class="empty">暂无数据</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.admin-page { max-width: 1000px; }
header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 0.75rem; }
.header-right { display: flex; gap: 0.5rem; align-items: center; }
.search-input { background: var(--bg-primary); color: var(--text-primary); border: 1px solid var(--border); padding: 0.5rem 0.75rem; border-radius: 6px; outline: none; font-size: 0.875rem; width: 180px; }
.search-input:focus { border-color: var(--accent); }
.search-input::placeholder { color: var(--text-muted); }
.filter-select { background: var(--bg-primary); color: var(--text-primary); border: 1px solid var(--border); padding: 0.5rem 0.75rem; border-radius: 6px; outline: none; font-size: 0.875rem; }
.filter-select:focus { border-color: var(--accent); }
.table-wrapper { background: var(--bg-card); backdrop-filter: blur(12px); border-radius: var(--radius); border: 1px solid var(--border); overflow: hidden; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { padding: 0.75rem 1rem; text-align: left; font-size: 0.875rem; }
.data-table th { background: var(--bg-primary); color: var(--text-secondary); font-weight: 500; border-bottom: 1px solid var(--border); }
.data-table td { border-bottom: 1px solid var(--border); }
.data-table tbody tr:last-child td { border-bottom: none; }
.data-table tbody tr:hover { background: var(--bg-hover); }
.badge { padding: 0.125rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 500; }
.badge.pending { background: rgba(245,158,11,0.15); color: var(--warning); }
.badge.completed { background: rgba(34,197,94,0.15); color: var(--success); }
.badge.failed { background: rgba(239,68,68,0.15); color: var(--danger); }
.actions { display: flex; gap: 0.5rem; }
.btn-sm { border: none; padding: 0.375rem 0.75rem; border-radius: 6px; cursor: pointer; font-size: 0.8rem; color: #fff; transition: all 0.2s; }
.btn-sm:hover { transform: translateY(-1px); }
.btn-success { background: var(--success); }
.btn-danger { background: var(--danger); }
.muted { color: var(--text-muted); font-size: 0.85rem; }
.empty { text-align: center; color: var(--text-muted); padding: 2rem; }
</style>
