<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import type { Plan } from '../types'
import { fetchProfile } from '../api/profile'

const router = useRouter()
const plans = ref<Plan[]>([])
const loading = ref(true)
const error = ref('')
const success = ref('')
const buying = ref<number | null>(null)

onMounted(async () => {
  try {
    const { data } = await api.get('/plans/')
    plans.value = data
  } catch {
    error.value = '加载失败，请刷新重试'
  } finally {
    loading.value = false
  }
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
    await api.post(`/plans/purchase/${plan.id}/`)
    await fetchProfile()
    router.push('/subscription')
  } catch (e: any) {
    error.value = e.response?.data?.error || '购买失败'
  } finally {
    buying.value = null
  }
}
</script>

<template>
  <div class="plans-page">
    <h2>选择套餐</h2>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="success" class="success">{{ success }}</p>
    <template v-if="loading">
      <div class="plan-list">
        <div v-for="n in 3" :key="n" class="plan-card">
          <div class="skeleton-line w-32 h-5" style="margin: 0 auto 0.5rem"></div>
          <div class="skeleton-line w-24 h-8" style="margin: 0.5rem auto"></div>
          <div class="skeleton-line w-36 h-4" style="margin: 0.5rem auto 1.25rem"></div>
          <div class="skeleton-line w-full h-10" style="border-radius: 6px"></div>
        </div>
      </div>
    </template>
    <template v-else>
      <div v-if="!plans.length && !error" class="empty">暂无可用套餐</div>
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
    </template>
  </div>
</template>

<style scoped>
@keyframes shimmer {
  0% { background-position: -200px 0; }
  100% { background-position: calc(200px + 100%) 0; }
}
.skeleton-line {
  background: linear-gradient(90deg, var(--bg-hover) 25%, rgba(255,255,255,0.04) 50%, var(--bg-hover) 75%);
  background-size: 200px 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}
.h-4 { height: 14px; }
.h-5 { height: 18px; }
.h-8 { height: 32px; }
.h-10 { height: 40px; }
.w-24 { width: 80px; }
.w-32 { width: 100px; }
.w-36 { width: 130px; }
.w-full { width: 100%; }

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
.empty { text-align: center; color: var(--text-muted); padding: 3rem; font-size: 0.95rem; }
</style>
