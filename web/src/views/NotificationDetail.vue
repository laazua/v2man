<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'

const route = useRoute()
const router = useRouter()
const notification = ref<any>(null)
const loading = ref(true)
const notFound = ref(false)

onMounted(async () => {
  try {
    const { data } = await api.get(`/notifications/`)
    const n = data.find((n: any) => n.id === Number(route.params.id))
    if (n) {
      notification.value = n
      await api.post('/notifications/mark-read/', { notification_id: n.id })
    } else {
      notFound.value = true
    }
  } catch {
    notFound.value = true
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="detail-page">
    <button @click="router.push('/notifications')" class="btn-back">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
      返回通知列表
    </button>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="notFound" class="empty">通知不存在</div>

    <div v-else class="notify-card" :class="{ pinned: notification.is_pinned }">
      <div class="notify-head">
        <span v-if="notification.is_pinned" class="pin-badge">置顶</span>
        <h1>{{ notification.title }}</h1>
        <span class="notify-date">{{ new Date(notification.created_at).toLocaleDateString('zh-CN') }}</span>
      </div>
      <div class="notify-body">{{ notification.content }}</div>
    </div>
  </div>
</template>

<style scoped>
.detail-page { max-width: 700px; }
.btn-back { display: inline-flex; align-items: center; gap: 0.35rem; background: none; border: none; color: var(--text-secondary); cursor: pointer; font-size: 0.85rem; padding: 0.35rem 0; margin-bottom: 1.25rem; transition: color 0.2s; }
.btn-back:hover { color: var(--accent); }

.loading { text-align: center; color: var(--text-muted); padding: 3rem; }
.empty { text-align: center; color: var(--text-muted); padding: 3rem; background: var(--bg-card); backdrop-filter: blur(12px); border-radius: var(--radius); border: 1px solid var(--border); }

.notify-card { background: var(--bg-card); backdrop-filter: blur(12px); padding: 1.5rem; border-radius: var(--radius); border: 1px solid var(--border); }
.notify-card.pinned { border-color: rgba(56,189,248,0.3); background: linear-gradient(135deg, var(--bg-card), rgba(56,189,248,0.06)); }
.notify-head { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; flex-wrap: wrap; }
.notify-head h1 { margin: 0; font-size: 1.15rem; flex: 1; min-width: 200px; }
.pin-badge { font-size: 0.7rem; padding: 0.15rem 0.5rem; border-radius: 4px; background: var(--accent); color: #fff; font-weight: 600; }
.notify-date { font-size: 0.8rem; color: var(--text-muted); white-space: nowrap; }
.notify-body { font-size: 0.9rem; line-height: 1.7; color: var(--text-secondary); white-space: pre-wrap; }
</style>
