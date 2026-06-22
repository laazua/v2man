<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import api from '../api'

const rechargeMode = ref('manual')
const paymentDriver = ref('simulate')
const alipayAppId = ref('')
const alipayPrivateKey = ref('')
const alipayPublicKey = ref('')
const notifyUrl = ref('')
const msg = ref('')
const loading = ref(false)

onMounted(async () => {
  const { data } = await api.get('/admin/payment/settings/')
  rechargeMode.value = data.recharge_mode
  paymentDriver.value = data.payment_driver
  alipayAppId.value = data.alipay_app_id || ''
  alipayPrivateKey.value = data.alipay_private_key || ''
  alipayPublicKey.value = data.alipay_public_key || ''
  notifyUrl.value = data.notify_url || ''
})

const driverLabel = computed(() =>
  paymentDriver.value === 'simulate' ? '模拟驱动（开发用）' : '支付宝当面付（生产用）'
)

async function save() {
  if (rechargeMode.value === 'auto' && paymentDriver.value === 'alipay') {
    if (!alipayAppId.value.trim() || !alipayPrivateKey.value.trim() || !alipayPublicKey.value.trim()) {
      msg.value = '错误：启用支付宝驱动需要填写 APPID、应用私钥和支付宝公钥'
      return
    }
  }
  loading.value = true
  msg.value = ''
  try {
    await api.post('/admin/payment/settings/', {
      recharge_mode: rechargeMode.value,
      payment_driver: paymentDriver.value,
      alipay_app_id: alipayAppId.value,
      alipay_private_key: alipayPrivateKey.value,
      alipay_public_key: alipayPublicKey.value,
    })
    msg.value = '保存成功'
  } catch (e: any) {
    msg.value = e.response?.data?.error || '保存失败'
  } finally {
    loading.value = false
  }
}

function copyNotifyUrl() {
  navigator.clipboard.writeText(notifyUrl.value)
  msg.value = '回调地址已复制'
  setTimeout(() => { msg.value = '' }, 2000)
}
</script>

<template>
  <div class="admin-page">
    <h2>充值设置</h2>

    <div class="card">
      <div class="form-group">
        <label>充值模式</label>
        <select v-model="rechargeMode" class="select">
          <option value="manual">手动审核模式</option>
          <option value="auto">自动到账模式</option>
        </select>
        <p class="hint">
          {{ rechargeMode === 'manual' ? '用户提交 → 管理员在充值审核页面确认到账' : '用户支付 → 系统自动确认到账' }}
        </p>
      </div>
    </div>

    <div v-if="rechargeMode === 'auto'" class="card">
      <h3 class="section-title">支付驱动</h3>

      <div class="form-group">
        <label>支付驱动</label>
        <select v-model="paymentDriver" class="select">
          <option value="simulate">模拟驱动（开发测试用）</option>
          <option value="alipay">支付宝当面付（生产用）</option>
        </select>
        <p class="hint">{{ driverLabel }}</p>
      </div>

      <template v-if="paymentDriver === 'alipay'">
        <div class="alipay-config">
          <h4 class="sub-title">支付宝配置</h4>

          <div class="form-group">
            <label>应用 APPID</label>
            <input v-model="alipayAppId" type="text" placeholder="支付宝开放平台获取的 APPID" class="input" />
          </div>

          <div class="form-group">
            <label>应用私钥</label>
            <textarea v-model="alipayPrivateKey" rows="6" placeholder="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----" class="input code" />
          </div>

          <div class="form-group">
            <label>支付宝公钥</label>
            <textarea v-model="alipayPublicKey" rows="4" placeholder="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----" class="input code" />
          </div>

          <div class="form-group">
            <label>异步通知地址 (Notify URL)</label>
            <div class="copy-row">
              <code class="notify-url">{{ notifyUrl }}</code>
              <button @click="copyNotifyUrl" class="btn-copy">复制</button>
            </div>
            <p class="hint">请将此地址配置到支付宝开放平台的应用中</p>
          </div>
        </div>
      </template>

    </div>

    <button @click="save" :disabled="loading" class="btn-primary">
      {{ loading ? '保存中...' : '保存设置' }}
    </button>
    <p v-if="msg" :class="['msg', { error: msg.includes('失败') || msg.includes('错误') }]">{{ msg }}</p>
  </div>
</template>

<style scoped>
.admin-page { max-width: 640px; }
h2 { margin-bottom: 1.5rem; }
.card { background: var(--bg-card); backdrop-filter: blur(12px); padding: 1.5rem; border-radius: var(--radius); border: 1px solid var(--border); margin-bottom: 1rem; }
.section-title { margin: 0 0 1rem; font-size: 1rem; }
.sub-title { margin: 0 0 1rem; font-size: 0.9rem; color: var(--text-secondary); }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.35rem; }
.input, .select { width: 100%; padding: 0.5rem; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-primary); color: var(--text-primary); font-size: 0.9rem; outline: none; box-sizing: border-box; }
.select { cursor: pointer; }
.input:focus, .select:focus { border-color: var(--accent); }
.input.code { font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace; font-size: 0.8rem; line-height: 1.5; resize: vertical; }
.hint { font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem; }
.alipay-config { background: var(--bg-primary); padding: 1rem; border-radius: 6px; margin-bottom: 1rem; }
.copy-row { display: flex; gap: 0.5rem; align-items: center; }
.notify-url { flex: 1; padding: 0.5rem; background: var(--bg-card); border: 1px solid var(--border); border-radius: 6px; font-size: 0.8rem; word-break: break-all; color: var(--accent); }
.btn-copy { padding: 0.4rem 0.75rem; background: var(--accent-gradient); color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 0.8rem; white-space: nowrap; }
.btn-copy:hover { opacity: 0.9; }
.btn-primary { width: 100%; padding: 0.6rem; background: var(--accent-gradient); color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 500; transition: all 0.2s; }
.btn-primary:hover:not(:disabled) { transform: translateY(-1px); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.msg { margin-top: 0.75rem; color: var(--success); text-align: center; font-size: 0.85rem; }
.msg.error { color: var(--danger); }
</style>
