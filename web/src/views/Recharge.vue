<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '../api'

const amount = ref(0)
const loading = ref(false)
const message = ref('')
const hasQr = ref(false)
const qrImageUrl = computed(() => '/api/auth/payment/qr-image/')

onMounted(async () => {
  try {
    const { data } = await api.get('/auth/payment/qr/')
    hasQr.value = data.has_qr
  } catch {
    hasQr.value = false
  }
})

async function submitRecharge() {
  if (!amount.value || amount.value < 1) return
  loading.value = true
  message.value = ''
  try {
    await api.post('/auth/recharge/', { amount: amount.value * 100 })
    message.value = `充值 ¥${amount.value} 已提交，等待管理员确认`
    amount.value = 0
  } catch {
    message.value = '提交失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="recharge-page">
    <h2>充值</h2>
    <div class="content">
      <div class="qr-section">
        <h3>请使用支付宝扫码付款</h3>
        <div v-if="hasQr" class="qr-image">
          <img :src="qrImageUrl" alt="支付宝收款码" />
        </div>
        <div v-else class="qr-placeholder">
          <p>收款码暂未设置</p>
          <p class="hint">请联系管理员上传收款码</p>
        </div>
      </div>

      <div class="form-section">
        <h3>填写充值金额</h3>
        <p class="form-desc">扫码付款后，请在此填写您支付的金额并提交</p>
        <div class="amount-input">
          <span class="prefix">¥</span>
          <input v-model.number="amount" type="number" min="1" placeholder="输入金额" />
        </div>
        <button @click="submitRecharge" :disabled="loading || amount < 1">
          {{ loading ? '提交中...' : '提交充值' }}
        </button>
        <p v-if="message" class="message">{{ message }}</p>
      </div>

      <div class="info-section">
        <p>管理员确认到账后，余额将自动更新</p>
        <p>如长时间未到账，请<router-link to="/contact">联系管理员</router-link></p>
      </div>
    </div>
  </div>
</template>

<style scoped>
h2 { margin-bottom: 1.5rem; }
.content { display: flex; flex-direction: column; gap: 1.5rem; max-width: 500px; }
.qr-section, .form-section, .info-section { background: var(--bg-card); backdrop-filter: blur(12px); padding: 1.5rem; border-radius: var(--radius); border: 1px solid var(--border); }
.qr-image { width: 200px; margin: 1rem auto; }
.qr-image img { width: 100%; height: auto; border-radius: var(--radius-sm); }
.qr-placeholder { width: 200px; height: 200px; margin: 1rem auto; background: var(--bg-hover); display: flex; flex-direction: column; align-items: center; justify-content: center; border-radius: var(--radius-sm); text-align: center; color: var(--text-muted); font-size: 0.875rem; }
.hint { font-size: 0.75rem; margin-top: 0.5rem; color: var(--text-muted); opacity: 0.6; }
.form-desc { color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.5rem; }
.amount-input { display: flex; align-items: center; margin: 1rem 0; }
.prefix { font-size: 1.5rem; margin-right: 0.5rem; color: var(--text-secondary); }
.amount-input input { flex: 1; padding: 0.75rem; font-size: 1.25rem; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--bg-primary); color: var(--text-primary); outline: none; transition: border-color 0.2s; }
.amount-input input:focus { border-color: var(--accent); }
button { width: 100%; padding: 0.75rem; background: var(--accent-gradient); color: #fff; border: none; border-radius: var(--radius-sm); cursor: pointer; font-size: 0.9rem; font-weight: 500; transition: all 0.2s; }
button:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(59,130,246,0.3); }
button:disabled { opacity: 0.5; cursor: not-allowed; }
.message { margin-top: 0.75rem; color: var(--success); text-align: center; }
.info-section { text-align: center; color: var(--text-muted); font-size: 0.875rem; line-height: 1.8; }
.info-section a { color: var(--accent); text-decoration: none; font-weight: 500; }
.info-section a:hover { text-decoration: underline; }
</style>
