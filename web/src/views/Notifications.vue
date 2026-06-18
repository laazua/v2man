<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const notifications = ref<any[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await api.get('/notifications/')
    notifications.value = data
    await api.post('/notifications/mark-read/')
  } catch {
    // fail silently
  } finally {
    loading.value = false
  }
})

function goDetail(n: any) {
  router.push(`/notifications/${n.id}`)
}
</script>

<template>
  <div class="notify-page">
    <h2>系统通知</h2>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else-if="!notifications.length" class="empty">暂无通知</div>

    <div v-else class="notify-list">
      <div v-for="n in notifications" :key="n.id" class="notify-card" :class="{ pinned: n.is_pinned }" @click="goDetail(n)">
        <div class="notify-head">
          <span v-if="n.is_pinned" class="pin-badge">置顶</span>
          <span v-if="!n.is_read" class="unread-dot"></span>
          <h3>{{ n.title }}</h3>
          <span class="notify-date">{{ new Date(n.created_at).toLocaleDateString('zh-CN') }}</span>
          <svg class="arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
        </div>
        <div class="notify-summary">{{ n.content }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.notify-page { max-width: 700px; }
h2 { margin-bottom: 1.5rem; }
.loading { text-align: center; color: var(--text-muted); padding: 3rem; }
.empty { text-align: center; color: var(--text-muted); padding: 3rem; background: var(--bg-card); backdrop-filter: blur(12px); border-radius: var(--radius); border: 1px solid var(--border); }

.notify-list { display: flex; flex-direction: column; gap: 0.75rem; }
.notify-card { background: var(--bg-card); backdrop-filter: blur(12px); padding: 1.1rem 1.25rem; border-radius: var(--radius); border: 1px solid var(--border); cursor: pointer; transition: all 0.2s; }
.notify-card:hover { transform: translateX(3px); box-shadow: var(--shadow); border-color: var(--accent); }
.notify-card.pinned { border-color: rgba(56,189,248,0.3); background: linear-gradient(135deg, var(--bg-card), rgba(56,189,248,0.06)); }
.notify-head { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.35rem; }
.notify-head h3 { margin: 0; font-size: 0.95rem; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.arrow { flex-shrink: 0; color: var(--text-muted); opacity: 0; transition: opacity 0.2s; }
.notify-card:hover .arrow { opacity: 1; }
.unread-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); flex-shrink: 0; box-shadow: 0 0 6px rgba(56,189,248,0.5); }
.pin-badge { font-size: 0.65rem; padding: 0.12rem 0.45rem; border-radius: 4px; background: var(--accent); color: #fff; font-weight: 600; flex-shrink: 0; }
.notify-date { font-size: 0.7rem; color: var(--text-muted); white-space: nowrap; }
.notify-summary { font-size: 0.8rem; line-height: 1.4; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; padding-left: 1.25rem; }
</style>
