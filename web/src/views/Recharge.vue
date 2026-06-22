<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '../api'

interface RechargeRecord {
  id: number; amount: number; status: string; admin_remark: string; created_at: string; confirmed_at: string | null
}

const mode = ref<'manual' | 'auto'>('manual')
const amount = ref(0)
const loading = ref(false)
const message = ref('')
const hasQr = ref(false)
const qrImageUrl = computed(() => `/api/auth/payment/qr-image/?t=${Date.now()}`)

// Auto mode state
const currentOrder = ref<any>(null)
const step = ref<'form' | 'paying' | 'done'>('form')
const alipayQrCode = ref('')

// Recharge history
const history = ref<RechargeRecord[]>([])

function isSimulateDriver() {
  return currentOrder.value && !currentOrder.value.qr_code
}

onMounted(async () => {
  try {
    const { data } = await api.get('/payment/mode/')
    mode.value = data.recharge_mode
  } catch {
    // fallback to manual
  }
  if (mode.value === 'manual') {
    try {
      const { data } = await api.get('/auth/payment/qr/')
      hasQr.value = data.has_qr
    } catch {
      hasQr.value = false
    }
  }
  loadHistory()
})

async function loadHistory() {
  try {
    const { data } = await api.get('/auth/recharge/')
    history.value = Array.isArray(data) ? data : []
  } catch {
    history.value = []
  }
}

function statusLabel(s: string) {
  return { pending: '待确认', completed: '已完成', failed: '已拒绝' }[s] || s
}

function formatAmount(cents: number) {
  return `¥${(cents / 100).toFixed(2)}`
}

// --- Manual mode ---
async function submitRecharge() {
  if (!amount.value || amount.value < 1) return
  loading.value = true
  message.value = ''
  try {
    await api.post('/auth/recharge/', { amount: amount.value * 100 })
    message.value = `充值 ¥${amount.value} 已提交，等待管理员确认`
    amount.value = 0
  } catch (e: any) {
    message.value = e.response?.data?.error || '提交失败，请重试'
  } finally {
    loading.value = false
  }
}

// --- Auto mode ---
async function createPayment() {
  if (!amount.value || amount.value < 1) return
  loading.value = true
  message.value = ''
  currentOrder.value = null
  try {
    const { data } = await api.post('/payment/create/', { amount: amount.value * 100 })
    currentOrder.value = data
    alipayQrCode.value = data.qr_code || ''
    step.value = 'paying'
  } catch (e: any) {
    message.value = e.response?.data?.error || '创建订单失败'
  } finally {
    loading.value = false
  }
}

async function simulatePay() {
  if (!currentOrder.value) return
  loading.value = true
  try {
    const { data } = await api.post('/payment/notify/', {
      out_trade_no: currentOrder.value.out_trade_no,
    })
    message.value = data.message
    step.value = 'done'
    amount.value = 0
  } catch (e: any) {
    message.value = e.response?.data?.error || '支付失败'
  } finally {
    loading.value = false
  }
}

function resetAuto() {
  step.value = 'form'
  currentOrder.value = null
  message.value = ''
}
</script>

<template>
  <div class="recharge-page">
    <h2>充值</h2>
    <div class="content">

      <!-- ============ 手动模式 ============ -->
      <template v-if="mode === 'manual'">
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
      </template>

      <!-- ============ 自动模式 ============ -->
      <template v-else>
        <!-- 步骤1：填金额 -->
        <div v-if="step === 'form'" class="form-section">
          <h3>充值金额</h3>
          <p class="form-desc">输入充值金额，提交后将生成支付二维码</p>
          <div class="amount-input">
            <span class="prefix">¥</span>
            <input v-model.number="amount" type="number" min="1" placeholder="输入金额" />
          </div>
          <button @click="createPayment" :disabled="loading || amount < 1">
            {{ loading ? '创建中...' : '去支付' }}
          </button>
          <p v-if="message" class="message error">{{ message }}</p>
        </div>

        <!-- 步骤2：支付 -->
        <div v-if="step === 'paying' && currentOrder" class="paying-section">
          <div class="pay-header">
            <div class="pay-amount">¥{{ (currentOrder.amount / 100).toFixed(2) }}</div>
            <div class="pay-order-no">订单号: {{ currentOrder.out_trade_no }}</div>
          </div>

          <!-- 支付宝当面付：显示动态二维码 -->
          <div v-if="alipayQrCode" class="alipay-qr-box">
            <p class="qr-desc">请使用支付宝扫码支付</p>
            <div class="qr-code-image" v-html="alipayQrCode"></div>
            <p class="qr-hint">扫描上方二维码完成支付，系统将自动到账</p>
          </div>

          <!-- 模拟驱动：显示模拟支付按钮 -->
          <div v-else class="simulate-box">
            <div class="simulate-icon">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" color="#2563eb"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5" fill="currentColor"/><path d="M21 15l-5-5L5 21"/></svg>
            </div>
            <p class="simulate-desc">开发环境 - 模拟支付宝支付</p>
            <p class="simulate-hint">点击下方按钮模拟支付成功回调</p>
            <button @click="simulatePay" :disabled="loading" class="btn-simulate">
              {{ loading ? '处理中...' : '模拟支付成功' }}
            </button>
          </div>
        </div>

        <!-- 步骤3：完成 -->
        <div v-if="step === 'done'" class="done-section">
          <div class="done-icon">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="var(--success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          </div>
          <p class="done-text">{{ message || '充值成功' }}</p>
          <button @click="resetAuto" class="btn-again">继续充值</button>
        </div>
      </template>

      <!-- ============ 充值记录 ============ -->
      <div class="history-section" v-if="history.length">
        <h3>充值记录</h3>
        <div class="history-list">
          <div v-for="r in history" :key="r.id" class="history-item">
            <div class="history-left">
              <span class="history-amount">{{ formatAmount(r.amount) }}</span>
              <span :class="['history-status', r.status]">{{ statusLabel(r.status) }}</span>
            </div>
            <div class="history-right">
              <span class="history-time">{{ new Date(r.created_at).toLocaleDateString('zh-CN') }}</span>
              <span v-if="r.status === 'failed' && r.admin_remark" class="history-remark">{{ r.admin_remark }}</span>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
h2 { margin-bottom: 1.5rem; }
.content { display: flex; flex-direction: column; gap: 1.5rem; max-width: 500px; }
.qr-section, .form-section, .paying-section, .done-section, .info-section { background: var(--bg-card); backdrop-filter: blur(12px); padding: 1.5rem; border-radius: var(--radius); border: 1px solid var(--border); }
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
.message.error { color: var(--danger); }
.info-section { text-align: center; color: var(--text-muted); font-size: 0.875rem; line-height: 1.8; }
.info-section a { color: var(--accent); text-decoration: none; font-weight: 500; }
.info-section a:hover { text-decoration: underline; }

/* Auto mode styles */
.pay-header { text-align: center; margin-bottom: 1rem; }
.pay-amount { font-size: 2rem; font-weight: 700; color: var(--text-primary); }
.pay-order-no { font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem; }

.simulate-box { text-align: center; padding: 1.5rem 0; }
.simulate-icon { margin-bottom: 1rem; }
.simulate-desc { font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 0.25rem; }
.simulate-hint { font-size: 0.8rem; color: var(--text-muted); margin-bottom: 1.25rem; }
.btn-simulate { max-width: 240px; margin: 0 auto; background: var(--success); }
.btn-simulate:hover:not(:disabled) { box-shadow: 0 4px 12px rgba(34,197,94,0.3); }

.alipay-qr-box { text-align: center; padding: 1.5rem 0; }
.qr-desc { font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 1rem; }
.qr-code-image { display: inline-block; padding: 1rem; background: #fff; border-radius: 8px; margin-bottom: 1rem; }
.qr-hint { font-size: 0.8rem; color: var(--text-muted); }

.done-section { text-align: center; }
.done-icon { margin-bottom: 1rem; }
.done-text { font-size: 1.1rem; font-weight: 500; color: var(--success); margin-bottom: 1.25rem; }
.btn-again { max-width: 200px; margin: 0 auto; }

/* 充值记录 */
.history-section { background: var(--bg-card); backdrop-filter: blur(12px); padding: 1.25rem; border-radius: var(--radius); border: 1px solid var(--border); }
.history-section h3 { margin: 0 0 0.75rem; font-size: 1rem; }
.history-list { display: flex; flex-direction: column; gap: 0.5rem; }
.history-item { display: flex; justify-content: space-between; align-items: center; padding: 0.6rem 0.75rem; background: var(--bg-primary); border-radius: 6px; border: 1px solid var(--border); }
.history-left { display: flex; align-items: center; gap: 0.5rem; }
.history-amount { font-weight: 600; font-size: 0.9rem; color: var(--text-primary); }
.history-status { padding: 0.125rem 0.4rem; border-radius: 4px; font-size: 0.7rem; font-weight: 500; }
.history-status.pending { background: rgba(245,158,11,0.15); color: var(--warning); }
.history-status.completed { background: rgba(34,197,94,0.15); color: var(--success); }
.history-status.failed { background: rgba(239,68,68,0.15); color: var(--danger); }
.history-right { display: flex; flex-direction: column; align-items: flex-end; gap: 0.2rem; }
.history-time { font-size: 0.7rem; color: var(--text-muted); }
.history-remark { font-size: 0.7rem; color: var(--danger); max-width: 180px; text-align: right; line-height: 1.3; }
</style>
