<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'
import type { Node } from '../types'

const origin = window.location.origin
const nodes = ref<Node[]>([])
const subToken = ref('')

onMounted(async () => {
  const [nodeRes, profileRes] = await Promise.all([
    api.get('/nodes/'),
    api.get('/auth/profile/'),
  ])
  nodes.value = nodeRes.data
  subToken.value = profileRes.data.subscription_token || ''
})

function copy(text: string) {
  navigator.clipboard.writeText(text)
}
</script>

<template>
  <div class="nodes-page">
    <h2>节点列表</h2>

    <div v-if="subToken" class="subscribe-box">
      <h3>订阅链接</h3>
      <div class="sub-item">
        <label>V2Ray</label>
        <code>{{ origin }}/api/subscription/{{ subToken }}/</code>
        <button @click="copy(`${origin}/api/subscription/${subToken}/`)">复制</button>
      </div>
      <div class="sub-item">
        <label>Clash</label>
        <code>{{ origin }}/api/subscription/{{ subToken }}/clashmeta/</code>
        <button @click="copy(`${origin}/api/subscription/${subToken}/clashmeta/`)">复制</button>
      </div>
      <div class="sub-item">
        <label>Sing-box</label>
        <code>{{ origin }}/api/subscription/{{ subToken }}/singbox/</code>
        <button @click="copy(`${origin}/api/subscription/${subToken}/singbox/`)">复制</button>
      </div>
    </div>

    <div class="node-list">
      <div v-for="node in nodes" :key="node.id" class="node-card">
        <div class="node-header">
          <span class="protocol">{{ node.protocol }}</span>
          <strong>{{ node.name }}</strong>
        </div>
        <div class="node-info">{{ node.address }}:{{ node.port }}</div>
      </div>
      <p v-if="!nodes.length" class="empty">暂无可用节点</p>
    </div>
  </div>
</template>

<style scoped>
h2 { margin-bottom: 1.5rem; }
.subscribe-box { background: var(--bg-card); backdrop-filter: blur(12px); padding: 1.25rem; border-radius: var(--radius); border: 1px solid var(--border); margin-bottom: 1.5rem; }
.subscribe-box h3 { margin-bottom: 0.75rem; }
.sub-item { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.75rem; flex-wrap: wrap; }
.sub-item label { font-size: 0.8rem; color: var(--text-secondary); min-width: 60px; }
.sub-item code { flex: 1; font-size: 0.75rem; word-break: break-all; color: var(--text-primary); background: var(--bg-primary); padding: 0.375rem 0.5rem; border-radius: 6px; border: 1px solid var(--border); }
.sub-item button { background: var(--accent); color: #fff; border: none; padding: 0.25rem 0.75rem; border-radius: 6px; cursor: pointer; font-size: 0.75rem; transition: all 0.2s; }
.sub-item button:hover { opacity: 0.85; }
.node-list { display: grid; gap: 0.75rem; }
.node-card { background: var(--bg-card); backdrop-filter: blur(12px); padding: 1rem 1.25rem; border-radius: var(--radius); border: 1px solid var(--border); transition: all 0.2s; }
.node-card:hover { transform: translateY(-1px); box-shadow: var(--shadow); }
.node-header { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.25rem; }
.protocol { background: var(--bg-hover); padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; color: var(--text-secondary); }
.node-info { color: var(--text-muted); font-size: 0.875rem; }
.empty { text-align: center; color: var(--text-muted); padding: 2rem; }
</style>
