<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '../api'

const hasQr = ref(false)
const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const message = ref('')
const refreshKey = ref(0)

async function loadQr() {
  try {
    const { data } = await api.get('/admin/payment/qr/')
    hasQr.value = !!data.qr_url
  } catch {
    hasQr.value = false
  }
}

onMounted(loadQr)

function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files?.length) {
    selectedFile.value = target.files[0]
  }
}

async function upload() {
  if (!selectedFile.value) return
  uploading.value = true
  message.value = ''
  const formData = new FormData()
  formData.append('qr_code', selectedFile.value)
  try {
    await api.post('/admin/payment/qr/', formData)
    message.value = '收款码已更新'
    hasQr.value = true
    refreshKey.value++
    selectedFile.value = null
  } catch {
    message.value = '上传失败，请重试'
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="payment-qr-page">
    <h2>收款码管理</h2>
    <div class="content">
      <div class="card">
        <h3>当前收款码</h3>
        <div v-if="hasQr" class="preview">
          <img :src="`/api/auth/payment/qr-image/?t=${refreshKey}`" alt="当前收款码" />
        </div>
        <div v-else class="no-image">暂未设置收款码</div>
      </div>
      <div class="card">
        <h3>上传新收款码</h3>
        <input type="file" accept="image/*" @change="onFileChange" />
        <button @click="upload" :disabled="!selectedFile || uploading">
          {{ uploading ? '上传中...' : '上传' }}
        </button>
        <p v-if="message" class="message">{{ message }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
h2 { margin-bottom: 1.5rem; }
.content { display: flex; flex-direction: column; gap: 1.5rem; max-width: 500px; }
.card { background: var(--bg-card); backdrop-filter: blur(12px); padding: 1.5rem; border-radius: var(--radius); border: 1px solid var(--border); }
.preview { width: 200px; margin: 1rem auto; }
.preview img { width: 100%; height: auto; border-radius: var(--radius-sm); }
.no-image { width: 200px; height: 200px; margin: 1rem auto; background: var(--bg-hover); display: flex; align-items: center; justify-content: center; border-radius: var(--radius-sm); color: var(--text-muted); }
input[type="file"] { display: block; margin: 1rem 0; }
button { padding: 0.75rem 1.5rem; background: var(--accent-gradient); color: #fff; border: none; border-radius: var(--radius-sm); cursor: pointer; font-size: 0.9rem; font-weight: 500; transition: all 0.2s; }
button:hover:not(:disabled) { transform: translateY(-1px); }
button:disabled { opacity: 0.5; cursor: not-allowed; }
.message { margin-top: 0.75rem; color: var(--success); }
</style>
