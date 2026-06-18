<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue'
import api from '../api'

interface Reply {
  id: number
  message: string
  is_admin: boolean
  visible_to_user: boolean
  created_at: string
}

interface Conversation {
  id: number
  username: string
  subject: string
  message: string
  status: 'pending' | 'replied'
  replies: Reply[]
  replied_at: string | null
  created_at: string
}

const conversations = ref<Conversation[]>([])
const loading = ref(true)
const filter = ref<'all' | 'pending' | 'replied'>('all')
const selected = ref<Conversation | null>(null)
const replyText = ref('')
const replySending = ref(false)
const replyInput = ref<HTMLTextAreaElement | null>(null)

const filtered = computed(() => {
  if (filter.value === 'all') return conversations.value
  return conversations.value.filter(m => m.status === filter.value)
})

async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/admin/contact/')
    conversations.value = data
    if (selected.value) {
      const updated = conversations.value.find(c => c.id === selected.value!.id)
      if (updated) selected.value = updated
    }
  } finally {
    loading.value = false
  }
}

function select(conv: Conversation) {
  selected.value = conv
  replyText.value = ''
}

async function sendReply() {
  if (!selected.value || !replyText.value.trim()) return
  replySending.value = true
  try {
    await api.post(`/admin/contact/${selected.value.id}/reply/`, { message: replyText.value.trim() })
    replyText.value = ''
    await load()
  } finally {
    replySending.value = false
  }
}

async function toggleVisibility(convId: number, replyId: number) {
  try {
    const { data } = await api.post(`/admin/contact/${convId}/toggle_visibility/`, { reply_id: replyId })
    if (selected.value) {
      const reply = selected.value.replies.find(r => r.id === replyId)
      if (reply) reply.visible_to_user = data.visible_to_user
    }
  } catch {}
}

onMounted(load)
</script>

<template>
  <div class="page">
    <h2 class="page-title">联系管理</h2>

    <div class="toolbar">
      <div class="filter-group">
        <button :class="['filter-btn', { active: filter === 'all' }]" @click="filter = 'all'">全部 ({{ conversations.length }})</button>
        <button :class="['filter-btn', { active: filter === 'pending' }]" @click="filter = 'pending'">待回复 ({{ conversations.filter(m => m.status === 'pending').length }})</button>
        <button :class="['filter-btn', { active: filter === 'replied' }]" @click="filter = 'replied'">已回复 ({{ conversations.filter(m => m.status === 'replied').length }})</button>
      </div>
    </div>

    <div class="content-split">
      <div class="list-panel">
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="!filtered.length" class="empty">暂无消息</div>
        <div v-else class="msg-list">
          <div
            v-for="conv in filtered"
            :key="conv.id"
            :class="['msg-card', { active: selected?.id === conv.id, pending: conv.status === 'pending' }]"
            @click="select(conv)"
          >
            <div class="msg-card-header">
              <span class="msg-username">{{ conv.username }}</span>
              <span :class="['status-dot', conv.status]" />
            </div>
            <div class="msg-card-subject">{{ conv.subject }}</div>
            <div class="msg-card-meta">{{ new Date(conv.created_at).toLocaleDateString('zh-CN') }}</div>
          </div>
        </div>
      </div>

      <div class="detail-panel">
        <div v-if="!selected" class="empty-detail">选择左侧消息进行回复</div>
        <template v-else>
          <div class="detail-header">
            <h3>{{ selected.subject }}</h3>
            <span :class="['status-badge', selected.status]">{{ selected.status === 'pending' ? '待回复' : '已回复' }}</span>
          </div>
          <div class="detail-meta">
            <span>来自：{{ selected.username }}</span>
            <span>{{ new Date(selected.created_at).toLocaleString('zh-CN') }}</span>
          </div>

          <div class="chat-body">
            <div class="chat-bubble user-bubble">
              <div class="bubble-label">用户</div>
              <div class="bubble-text">{{ selected.message }}</div>
              <div class="bubble-time">{{ new Date(selected.created_at).toLocaleString('zh-CN') }}</div>
            </div>
            <div v-for="reply in selected.replies" :key="reply.id" :class="['chat-bubble', reply.is_admin ? 'admin-bubble' : 'user-bubble', { 'hidden-reply': !reply.visible_to_user }]">
              <div class="bubble-label">{{ reply.is_admin ? '管理员' : '用户' }}</div>
              <div class="bubble-text">{{ reply.message }}</div>
              <div class="bubble-actions">
                <span class="bubble-time">{{ new Date(reply.created_at).toLocaleString('zh-CN') }}</span>
                <button v-if="reply.is_admin" class="visibility-toggle" :title="reply.visible_to_user ? '对用户隐藏' : '对用户可见'" @click="toggleVisibility(selected.id, reply.id)">
                  {{ reply.visible_to_user ? '👁' : '🚫' }}
                </button>
              </div>
            </div>
          </div>

          <div class="reply-form">
            <textarea
              ref="replyInput"
              v-model="replyText"
              rows="3"
              placeholder="输入回复内容..."
            ></textarea>
            <button class="btn-primary" :disabled="replySending || !replyText.trim()" @click="sendReply">
              {{ replySending ? '发送中...' : '发送回复' }}
            </button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-title { font-size: 1.25rem; font-weight: 700; margin-bottom: 1rem; }

.toolbar { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; }
.filter-group { display: flex; gap: 0.35rem; }
.filter-btn { padding: 0.35rem 0.75rem; border-radius: var(--radius-sm); border: 1px solid var(--border); background: transparent; color: var(--text-secondary); font-size: 0.8rem; cursor: pointer; transition: all 0.15s; }
.filter-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.filter-btn:hover:not(.active) { background: var(--bg-hover); }

.content-split { display: flex; gap: 1rem; min-height: 500px; }
.list-panel { width: 320px; flex-shrink: 0; overflow-y: auto; border: 1px solid var(--border); border-radius: var(--radius); background: var(--bg-card); max-height: calc(100vh - 220px); }
.detail-panel { flex: 1; border: 1px solid var(--border); border-radius: var(--radius); background: var(--bg-card); padding: 1.25rem; overflow-y: auto; max-height: calc(100vh - 220px); display: flex; flex-direction: column; }

.loading, .empty, .empty-detail { padding: 2rem; text-align: center; color: var(--text-muted); font-size: 0.875rem; }

.msg-list { display: flex; flex-direction: column; }
.msg-card { padding: 0.75rem 1rem; cursor: pointer; border-bottom: 1px solid var(--border); transition: background 0.1s; }
.msg-card:last-child { border-bottom: none; }
.msg-card:hover { background: var(--bg-hover); }
.msg-card.active { background: rgba(56,189,248,0.06); border-left: 3px solid var(--accent); }
.msg-card.pending .msg-card-subject { font-weight: 600; }
.msg-card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.25rem; }
.msg-username { font-size: 0.8rem; color: var(--text-muted); }
.status-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.status-dot.pending { background: #eab308; }
.status-dot.replied { background: #22c55e; }
.msg-card-subject { font-size: 0.85rem; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.msg-card-meta { font-size: 0.75rem; color: var(--text-muted); margin-top: 0.2rem; }

.detail-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem; }
.detail-header h3 { font-size: 1.05rem; font-weight: 600; margin: 0; }
.status-badge { font-size: 0.75rem; padding: 0.15rem 0.5rem; border-radius: 10px; font-weight: 600; }
.status-badge.pending { background: rgba(234,179,8,0.12); color: #eab308; border: 1px solid rgba(234,179,8,0.25); }
.status-badge.replied { background: rgba(34,197,94,0.12); color: #22c55e; border: 1px solid rgba(34,197,94,0.25); }
.detail-meta { display: flex; gap: 1rem; font-size: 0.8rem; color: var(--text-muted); margin-bottom: 1rem; }

.chat-body { flex: 1; display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1rem; overflow-y: auto; }
.chat-bubble { max-width: 85%; padding: 0.55rem 0.75rem; border-radius: var(--radius-sm); }
.user-bubble { align-self: flex-end; background: var(--accent-soft); border-bottom-right-radius: 2px; }
.admin-bubble { align-self: flex-start; background: var(--bg-primary); border: 1px solid var(--border); border-bottom-left-radius: 2px; }
.hidden-reply { opacity: 0.4; }
.hidden-reply .bubble-text { text-decoration: line-through; }
.bubble-label { font-size: 0.7rem; color: var(--accent); font-weight: 600; margin-bottom: 0.2rem; }
.bubble-text { font-size: 0.875rem; color: var(--text-primary); line-height: 1.6; white-space: pre-wrap; }
.bubble-actions { display: flex; align-items: center; justify-content: space-between; margin-top: 0.25rem; }
.bubble-time { font-size: 0.7rem; color: var(--text-muted); }
.visibility-toggle { background: none; border: none; cursor: pointer; font-size: 0.85rem; padding: 0 0.25rem; line-height: 1; opacity: 0.5; transition: opacity 0.15s; }
.visibility-toggle:hover { opacity: 1; }

.reply-form { display: flex; flex-direction: column; gap: 0.5rem; border-top: 1px solid var(--border); padding-top: 0.75rem; }
.reply-form textarea { width: 100%; padding: 0.55rem 0.75rem; border-radius: var(--radius); border: 1px solid var(--border); background: var(--bg-primary); color: var(--text-primary); font-size: 0.875rem; resize: vertical; min-height: 60px; box-sizing: border-box; font-family: inherit; }
.reply-form textarea:focus { outline: none; border-color: var(--accent); }
.btn-primary { align-self: flex-start; padding: 0.5rem 1.25rem; border-radius: var(--radius); border: none; background: linear-gradient(135deg, var(--accent), #7c3aed); color: #fff; font-size: 0.875rem; font-weight: 600; cursor: pointer; transition: all 0.2s; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary:not(:disabled):hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(56,189,248,0.3); }
</style>
