<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'
import type { Node } from '../types'
import { profile } from '../api/profile'
const nodes = ref<Node[]>([])
const loading = ref(true)

const protocolColors: Record<string, string> = {
  vless: 'var(--accent)',
  vmess: '#a855f7',
  shadowsocks: '#22c55e',
  trojan: '#f97316',
  hysteria2: '#ec4899',
}

onMounted(async () => {
  try {
    const { data } = await api.get('/nodes/')
    nodes.value = data
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="nodes-page">
    <div class="page-header">
      <h2>节点列表</h2>
      <span class="node-count">{{ nodes.length }} 个节点</span>
    </div>

    <div v-if="profile.plan_name && profile.subscription_token" class="quick-sub">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
      <router-link to="/subscription">查看订阅链接 →</router-link>
    </div>

    <div class="node-list">
      <template v-if="loading">
        <div v-for="n in 4" :key="n" class="node-card">
          <div class="skeleton-dot"></div>
          <div class="node-body">
            <div class="node-top">
              <div class="skeleton-line w-20 h-5"></div>
              <div class="skeleton-line w-32 h-5"></div>
            </div>
            <div class="skeleton-line w-44 h-4 mt-1"></div>
          </div>
        </div>
      </template>
      <template v-else>
        <div v-for="node in nodes" :key="node.id" class="node-card">
          <div class="status-dot" :class="node.is_active ? 'online' : 'offline'"></div>
          <div class="node-body">
            <div class="node-top">
              <span class="protocol-badge" :style="{ background: protocolColors[node.protocol] + '20', color: protocolColors[node.protocol], borderColor: protocolColors[node.protocol] + '40' }">{{ node.protocol }}</span>
              <strong class="node-name">{{ node.name }}</strong>
            </div>
            <div class="node-addr">{{ node.address }}:{{ node.port }}</div>
          </div>
        </div>
        <p v-if="!nodes.length" class="empty">暂无可用节点</p>
      </template>
    </div>
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
.skeleton-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; background: var(--bg-hover); animation: shimmer 1.5s infinite; background-size: 200px 100%; }
.h-4 { height: 14px; }
.h-5 { height: 18px; }
.w-20 { width: 60px; }
.w-32 { width: 100px; }
.w-44 { width: 140px; }
.mt-1 { margin-top: 4px; }

.page-header { display: flex; align-items: baseline; gap: 0.75rem; margin-bottom: 1.5rem; }
.page-header h2 { margin: 0; }
.node-count { font-size: 0.8rem; color: var(--text-muted); }

.quick-sub { display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem 1rem; background: var(--accent-soft); border-radius: var(--radius-sm); border: 1px solid var(--border); margin-bottom: 1.25rem; color: var(--accent); font-size: 0.85rem; }
.quick-sub a { color: var(--accent); font-weight: 500; }
.quick-sub a:hover { text-decoration: underline; }

.node-list { display: flex; flex-direction: column; gap: 0.75rem; }

.node-card { display: flex; align-items: center; gap: 1rem; background: var(--bg-card); backdrop-filter: blur(12px); padding: 1rem 1.25rem; border-radius: var(--radius); border: 1px solid var(--border); transition: all 0.25s; }
.node-card:hover { transform: translateX(3px); box-shadow: var(--shadow); }

.status-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.status-dot.online { background: #22c55e; box-shadow: 0 0 6px rgba(34,197,94,0.5); }
.status-dot.offline { background: var(--text-muted); }

.node-body { flex: 1; min-width: 0; }
.node-top { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.25rem; }
.protocol-badge { padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.7rem; font-weight: 600; border: 1px solid; letter-spacing: 0.02em; }
.node-name { font-size: 0.95rem; }
.node-addr { color: var(--text-muted); font-size: 0.8rem; font-family: 'SF Mono', 'Fira Code', monospace; }

.empty { text-align: center; color: var(--text-muted); padding: 3rem; }
</style>
