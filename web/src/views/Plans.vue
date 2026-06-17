<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'

interface Plan {
  id: number
  name: string
  price_display: string
  traffic_limit: number
  duration_days: number
}

const plans = ref<Plan[]>([])
const balance = ref(0)
const error = ref('')
const success = ref('')
const buying = ref<number | null>(null)

onMounted(async () => {
  const [planRes, profileRes] = await Promise.all([
    api.get('/plans/'),
    api.get('/auth/profile/'),
  ])
  plans.value = planRes.data
  balance.value = profileRes.data.balance
})

function formatTraffic(mb: number): string {
  if (mb === 0) return '无限'
  if (mb >= 1024) return `${(mb / 1024).toFixed(0)} GB`
  return `${mb} MB`
}

async function buy(plan: Plan) {
  buying.value = plan.id
  error.value = ''
  success.value = ''
  try {
    const { data } = await api.post(`/plans/purchase/${plan.id}/`)
    success.value = data.message
    balance.value = data.balance_remaining
  } catch (e: any) {
    error.value = e.response?.data?.error || '购买失败'
  } finally {
    buying.value = null
  }
}
</script>

<template>
  <div class="plans-page">
    <div class="page-header">
      <h2>选择套餐</h2>
      <span class="balance-label">余额: ¥{{ (balance / 100).toFixed(2) }}</span>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="success" class="success">{{ success }}</p>
    <div class="plan-list">
      <div v-for="plan in plans" :key="plan.id" class="plan-card">
        <h3>{{ plan.name }}</h3>
        <p class="price">{{ plan.price_display }}</p>
        <p class="detail">{{ formatTraffic(plan.traffic_limit) }} / {{ plan.duration_days }} 天</p>
        <button @click="buy(plan)" :disabled="buying === plan.id">
          {{ buying === plan.id ? '购买中...' : '购买' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 2rem; }
.balance-label { color: var(--success); }
.plan-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 1rem; }
.plan-card { background: var(--bg-card); backdrop-filter: blur(12px); padding: 1.5rem; border-radius: var(--radius); border: 1px solid var(--border); text-align: center; transition: all 0.2s; }
.plan-card:hover { transform: translateY(-2px); box-shadow: var(--shadow); }
.plan-card h3 { margin: 0 0 0.5rem; }
.price { font-size: 1.5rem; color: var(--warning); margin: 0.5rem 0; font-weight: 700; }
.detail { color: var(--text-muted); font-size: 0.875rem; margin-bottom: 1.25rem; }
button { width: 100%; padding: 0.75rem; background: var(--accent-gradient); color: #fff; border: none; border-radius: var(--radius-sm); cursor: pointer; font-size: 0.9rem; font-weight: 500; transition: all 0.2s; }
button:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(59,130,246,0.3); }
button:disabled { opacity: 0.5; cursor: not-allowed; }
.error { color: var(--danger); margin-bottom: 0.75rem; }
.success { color: var(--success); margin-bottom: 0.75rem; }
</style>
