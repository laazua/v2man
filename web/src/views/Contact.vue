<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'

interface Reply {
  id: number
  message: string
  is_admin: boolean
  created_at: string
}

interface ContactMessage {
  id: number
  subject: string
  message: string
  status: 'pending' | 'replied'
  replies: Reply[]
  replied_at: string | null
  created_at: string
}

const conversations = ref<ContactMessage[]>([])
const loading = ref(true)
const submitting = ref(false)
const subject = ref('')
const content = ref('')
const submitMsg = ref({ text: '', type: '' })
const replyTexts = ref<Record<number, string>>({})

async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/contact/')
    conversations.value = data
  } finally {
    loading.value = false
  }
}

async function submit() {
  submitMsg.value = { text: '', type: '' }
  if (!subject.value.trim() || !content.value.trim()) {
    submitMsg.value = { text: '请填写主题和内容', type: 'error' }
    return
  }
  submitting.value = true
  try {
    await api.post('/contact/', { subject: subject.value.trim(), message: content.value.trim() })
    subject.value = ''
    content.value = ''
    submitMsg.value = { text: '消息已提交，请等待管理员回复', type: 'success' }
    await load()
  } catch (e: any) {
    submitMsg.value = { text: e.response?.data?.error || '提交失败', type: 'error' }
  } finally {
    submitting.value = false
  }
}

async function sendFollowUp(convId: number) {
  const text = replyTexts.value[convId]?.trim()
  if (!text) return
  try {
    await api.post(`/contact/${convId}/reply/`, { message: text })
    replyTexts.value[convId] = ''
    await load()
  } catch (e: any) {
    alert(e.response?.data?.error || '发送失败')
  }
}

onMounted(() => {
  localStorage.setItem('contact_last_viewed', new Date().toISOString())
  load()
})
</script>

<template>
  <div class="page">
    <h2 class="page-title">联系管理员</h2>

    <div class="card contact-form">
      <div class="card-body">
        <h3 class="form-title">提交新消息</h3>
        <div class="form-group">
          <label>主题</label>
          <input v-model="subject" type="text" placeholder="简要描述您的问题" maxlength="200" />
        </div>
        <div class="form-group">
          <label>内容</label>
          <textarea v-model="content" rows="5" placeholder="请详细描述您遇到的问题或需求"></textarea>
        </div>
        <p v-if="submitMsg.text" :class="['msg', submitMsg.type]">{{ submitMsg.text }}</p>
        <button @click="submit" class="btn-primary" :disabled="submitting">
          {{ submitting ? '提交中...' : '提交' }}
        </button>
      </div>
    </div>

    <h3 class="section-title">历史消息</h3>
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="!conversations.length" class="empty">暂无历史消息</div>
    <div v-else class="conversation-list">
      <div v-for="conv in conversations" :key="conv.id" class="conversation-card">
        <div class="conv-header">
          <span class="conv-subject">{{ conv.subject }}</span>
          <span :class="['status-badge', conv.status]">{{ conv.status === 'pending' ? '待回复' : '已回复' }}</span>
        </div>

        <div class="chat-body">
          <div class="chat-bubble user-bubble">
            <div class="bubble-text">{{ conv.message }}</div>
            <div class="bubble-time">{{ new Date(conv.created_at).toLocaleString('zh-CN') }}</div>
          </div>
          <div v-for="reply in conv.replies" :key="reply.id" :class="['chat-bubble', reply.is_admin ? 'admin-bubble' : 'user-bubble']">
            <div v-if="reply.is_admin" class="bubble-label">管理员</div>
            <div class="bubble-text">{{ reply.message }}</div>
            <div class="bubble-time">{{ new Date(reply.created_at).toLocaleString('zh-CN') }}</div>
          </div>
        </div>

        <div class="followup-form">
          <textarea
            v-model="replyTexts[conv.id]"
            rows="2"
            :placeholder="conv.status === 'replied' ? '输入您的跟进回复...' : '等待管理员回复...'"
            :disabled="conv.status === 'pending'"
          ></textarea>
          <button
            v-if="conv.status === 'replied'"
            @click="sendFollowUp(conv.id)"
            :disabled="!replyTexts[conv.id]?.trim()"
            class="btn-sm"
          >发送</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { max-width: 720px; margin: 0 auto; }
.page-title { font-size: 1.25rem; font-weight: 700; margin-bottom: 1.25rem; }
.section-title { font-size: 1rem; font-weight: 600; margin: 1.5rem 0 0.75rem; }

.contact-form { margin-bottom: 0.5rem; }
.form-title { font-size: 0.95rem; font-weight: 600; margin-bottom: 1rem; }
.form-group { margin-bottom: 0.75rem; }
.form-group label { display: block; font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.3rem; }
.form-group input,
.form-group textarea { width: 100%; padding: 0.55rem 0.75rem; border-radius: var(--radius); border: 1px solid var(--border); background: var(--bg-primary); color: var(--text-primary); font-size: 0.875rem; transition: border-color 0.15s; box-sizing: border-box; font-family: inherit; }
.form-group input:focus,
.form-group textarea:focus { outline: none; border-color: var(--accent); }
.form-group textarea { resize: vertical; min-height: 100px; }
.msg { font-size: 0.85rem; margin-bottom: 0.75rem; }
.msg.success { color: var(--success); }
.msg.error { color: var(--danger); }
.btn-primary { padding: 0.5rem 1.25rem; border-radius: var(--radius); border: none; background: linear-gradient(135deg, var(--accent), #7c3aed); color: #fff; font-size: 0.875rem; font-weight: 600; cursor: pointer; transition: all 0.2s; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary:not(:disabled):hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(56,189,248,0.3); }

.loading, .empty { color: var(--text-muted); font-size: 0.875rem; padding: 2rem 0; text-align: center; }

.conversation-list { display: flex; flex-direction: column; gap: 1rem; }
.conversation-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.conv-header { display: flex; align-items: center; justify-content: space-between; padding: 0.65rem 1rem; border-bottom: 1px solid var(--border); }
.conv-subject { font-size: 0.9rem; font-weight: 600; color: var(--text-primary); }
.status-badge { font-size: 0.75rem; padding: 0.15rem 0.5rem; border-radius: 10px; font-weight: 600; }
.status-badge.pending { background: rgba(234,179,8,0.12); color: #eab308; border: 1px solid rgba(234,179,8,0.25); }
.status-badge.replied { background: rgba(34,197,94,0.12); color: #22c55e; border: 1px solid rgba(34,197,94,0.25); }

.chat-body { padding: 0.75rem 1rem; display: flex; flex-direction: column; gap: 0.5rem; }
.chat-bubble { max-width: 85%; padding: 0.55rem 0.75rem; border-radius: var(--radius-sm); position: relative; }
.user-bubble { align-self: flex-end; background: var(--accent-soft); border-bottom-right-radius: 2px; }
.admin-bubble { align-self: flex-start; background: var(--bg-primary); border: 1px solid var(--border); border-bottom-left-radius: 2px; }
.bubble-label { font-size: 0.7rem; color: var(--accent); font-weight: 600; margin-bottom: 0.2rem; }
.bubble-text { font-size: 0.875rem; color: var(--text-primary); line-height: 1.6; white-space: pre-wrap; }
.bubble-time { font-size: 0.7rem; color: var(--text-muted); margin-top: 0.25rem; text-align: right; }

.followup-form { display: flex; gap: 0.5rem; padding: 0.65rem 1rem; border-top: 1px solid var(--border); align-items: flex-end; }
.followup-form textarea { flex: 1; padding: 0.5rem 0.65rem; border-radius: var(--radius-sm); border: 1px solid var(--border); background: var(--bg-primary); color: var(--text-primary); font-size: 0.85rem; resize: none; min-height: 36px; font-family: inherit; }
.followup-form textarea:focus { outline: none; border-color: var(--accent); }
.followup-form textarea:disabled { opacity: 0.5; }
.btn-sm { padding: 0.4rem 0.85rem; border-radius: var(--radius-sm); border: none; background: linear-gradient(135deg, var(--accent), #7c3aed); color: #fff; font-size: 0.8rem; font-weight: 600; cursor: pointer; white-space: nowrap; }
.btn-sm:disabled { opacity: 0.4; cursor: not-allowed; }
.btn-sm:not(:disabled):hover { transform: translateY(-1px); }
</style>
