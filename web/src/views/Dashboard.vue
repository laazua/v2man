<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'
import type { User } from '../types'

const origin = window.location.origin
const user = ref<(User & { subscription_token?: string; balance?: number }) | null>(null)

onMounted(async () => {
  const { data } = await api.get('/auth/profile/')
  user.value = data
})

function formatMB(mb: number): string {
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`
  return `${mb} MB`
}

function trafficPercent(): number {
  if (!user.value || !user.value.traffic_total) return 0
  return Math.min(100, Math.round((user.value.traffic_used / user.value.traffic_total) * 100))
}

function copy(text: string) {
  navigator.clipboard.writeText(text)
}
</script>

<template>
  <div class="dashboard">
    <div v-if="user" class="grid">
      <div class="card">
        <h3>当前套餐</h3>
        <p>{{ user.plan_name || '无套餐' }}</p>
        <router-link to="/plans">购买套餐 →</router-link>
      </div>
      <div class="card">
        <h3>使用量</h3>
        <p>{{ formatMB(user.traffic_used) }} / {{ formatMB(user.traffic_total) }}</p>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: trafficPercent() + '%' }"></div>
        </div>
      </div>
      <div class="card">
        <h3>到期时间</h3>
        <p>{{ user.expire_date ? new Date(user.expire_date).toLocaleDateString('zh-CN') : '无' }}</p>
      </div>
      <div class="card">
        <h3>充值</h3>
        <router-link to="/recharge">去充值 →</router-link>
      </div>
    </div>

    <div v-if="user?.subscription_token" class="subscribe-section">
      <h3>订阅链接</h3>
      <div class="sub-links">
        <div class="sub-item">
          <label>V2Ray (Base64)</label>
          <code>{{ origin }}/api/subscription/{{ user.subscription_token }}/</code>
          <button @click="copy(`${origin}/api/subscription/${user.subscription_token}/`)">复制</button>
        </div>
        <div class="sub-item">
          <label>Clash</label>
          <code>{{ origin }}/api/subscription/{{ user.subscription_token }}/clashmeta/</code>
          <button @click="copy(`${origin}/api/subscription/${user.subscription_token}/clashmeta/`)">复制</button>
        </div>
        <div class="sub-item">
          <label>Sing-box</label>
          <code>{{ origin }}/api/subscription/{{ user.subscription_token }}/singbox/</code>
          <button @click="copy(`${origin}/api/subscription/${user.subscription_token}/singbox/`)">复制</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
.card { background: var(--bg-card); backdrop-filter: blur(12px); padding: 1.25rem; border-radius: var(--radius); border: 1px solid var(--border); transition: all 0.2s; }
.card:hover { transform: translateY(-1px); box-shadow: var(--shadow); }
.card h3 { margin: 0 0 0.5rem; font-size: 0.875rem; color: var(--text-secondary); }
.card p { margin: 0 0 0.75rem; font-size: 1.125rem; }
.card a { color: var(--accent); font-size: 0.875rem; }
.progress-bar { height: 6px; background: var(--bg-hover); border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: var(--accent-gradient); border-radius: 3px; transition: width 0.3s; }
.subscribe-section { background: var(--bg-card); backdrop-filter: blur(12px); padding: 1.25rem; border-radius: var(--radius); border: 1px solid var(--border); }
.subscribe-section h3 { margin-bottom: 0.75rem; }
.sub-item { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.75rem; flex-wrap: wrap; }
.sub-item label { font-size: 0.8rem; color: var(--text-secondary); min-width: 100px; }
.sub-item code { flex: 1; font-size: 0.75rem; word-break: break-all; color: var(--text-primary); background: var(--bg-primary); padding: 0.375rem 0.5rem; border-radius: 6px; border: 1px solid var(--border); }
.sub-item button { background: var(--accent); color: #fff; border: none; padding: 0.25rem 0.75rem; border-radius: 6px; cursor: pointer; font-size: 0.75rem; transition: all 0.2s; }
.sub-item button:hover { opacity: 0.85; transform: translateY(-1px); }
</style>
