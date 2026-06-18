<script setup lang="ts">
import { profile } from '../api/profile'
import { getSubscribeBaseUrl } from '../api/subscribe'
import { copiedKey, copyText } from '../api/copy'

const origin = getSubscribeBaseUrl()

function formatMB(mb: number): string {
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`
  return `${mb} MB`
}

function trafficPercent(): number {
  if (!profile.traffic_total) return 0
  return Math.min(100, Math.round((profile.traffic_used / profile.traffic_total) * 100))
}

function daysLeft(): number {
  if (!profile.expire_date) return 0
  const now = new Date()
  const expire = new Date(profile.expire_date)
  return Math.max(0, Math.ceil((expire.getTime() - now.getTime()) / 86400000))
}
</script>

<template>
  <div class="dashboard">
    <div v-if="profile.loaded" class="grid">
      <div class="card card-plan">
        <div class="card-bg-icon">
          <svg width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2L11 13"/><path d="M22 2L15 22L11 13L2 9L22 2Z"/></svg>
        </div>
        <div class="card-body">
          <div class="card-header">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2L11 13"/><path d="M22 2L15 22L11 13L2 9L22 2Z"/></svg>
            <span>当前套餐</span>
          </div>
          <p class="card-value">{{ profile.plan_name || '无套餐' }}</p>
          <router-link v-if="!profile.plan_name" to="/plans" class="card-link">购买套餐 →</router-link>
          <span v-else class="card-meta">已激活</span>
        </div>
      </div>
      <div class="card card-traffic">
        <div class="card-bg-icon">
          <svg width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><polyline points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        </div>
        <div class="card-body">
          <div class="card-header">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            <span>流量使用</span>
          </div>
          <p class="card-value">{{ formatMB(profile.traffic_used) }} <span class="card-unit">/ {{ formatMB(profile.traffic_total) }}</span></p>
          <div class="fuel-gauge">
            <div class="fuel-fill" :style="{ width: trafficPercent() + '%' }"></div>
          </div>
          <span class="card-meta">{{ trafficPercent() }}% 已使用</span>
        </div>
      </div>
      <div class="card card-expiry">
        <div class="card-bg-icon">
          <svg width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
        </div>
        <div class="card-body">
          <div class="card-header">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
            <span>到期时间</span>
          </div>
          <p class="card-value">{{ profile.expire_date ? new Date(profile.expire_date).toLocaleDateString('zh-CN') : '无' }}</p>
          <span class="card-meta">{{ profile.expire_date ? `剩余 ${daysLeft()} 天` : '' }}</span>
        </div>
      </div>
      <div class="card card-balance">
        <div class="card-bg-icon">
          <svg width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="6" width="22" height="12" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M1 10h22"/></svg>
        </div>
        <div class="card-body">
          <div class="card-header">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="6" width="22" height="12" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M1 10h22"/></svg>
            <span>账户余额</span>
          </div>
          <p class="card-value">¥{{ (profile.balance / 100).toFixed(2) }}</p>
          <router-link to="/recharge" class="card-link">去充值 →</router-link>
        </div>
      </div>
    </div>

    <div v-if="profile.loaded && profile.plan_name && profile.subscription_token" class="subscribe-section">
      <div class="sub-header">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
        <span>订阅链接</span>
      </div>
      <div class="sub-links">
        <div class="sub-item sub-v2ray" @click="copyText(`${origin}/api/subscription/${profile.subscription_token}/`, 'dash-v2ray')">
          <span class="sub-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
          </span>
          <span class="sub-label">V2Ray</span>
          <span class="copy-badge">{{ copiedKey === 'dash-v2ray' ? '已复制' : '点击复制' }}</span>
        </div>
        <div class="sub-item sub-clash" @click="copyText(`${origin}/api/subscription/${profile.subscription_token}/clashmeta/`, 'dash-clash')">
          <span class="sub-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"/><line x1="12" y1="22" x2="12" y2="15.5"/><polyline points="22 8.5 12 15.5 2 8.5"/></svg>
          </span>
          <span class="sub-label">Clash</span>
          <span class="copy-badge">{{ copiedKey === 'dash-clash' ? '已复制' : '点击复制' }}</span>
        </div>
        <div class="sub-item sub-singbox" @click="copyText(`${origin}/api/subscription/${profile.subscription_token}/singbox/`, 'dash-singbox')">
          <span class="sub-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
          </span>
          <span class="sub-label">Sing-box</span>
          <span class="copy-badge">{{ copiedKey === 'dash-singbox' ? '已复制' : '点击复制' }}</span>
        </div>
      </div>
    </div>

    <div v-if="!profile.loaded" class="grid">
      <div v-for="n in 4" :key="n" class="skeleton-card">
        <div class="skeleton-accent"></div>
        <div class="skeleton-body">
          <div class="skeleton-line h-3 w-40"></div>
          <div class="skeleton-line h-6 w-60 mt-3"></div>
          <div class="skeleton-line h-3 w-32 mt-2"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard { max-width: 900px; }
.grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-bottom: 1.5rem; }

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
.h-3 { height: 12px; }
.h-6 { height: 24px; }
.w-32 { width: 80px; }
.w-40 { width: 100px; }
.w-60 { width: 150px; }
.mt-2 { margin-top: 6px; }
.mt-3 { margin-top: 10px; }
.skeleton-card { background: var(--bg-card); border-radius: var(--radius); border: 1px solid var(--border); display: flex; overflow: hidden; }
.skeleton-accent { width: 4px; flex-shrink: 0; background: var(--bg-hover); border-radius: 4px 0 0 4px; }
.skeleton-body { padding: 1.25rem; flex: 1; }

.card {
  position: relative;
  border-radius: var(--radius);
  padding: 1.25rem;
  overflow: hidden;
  transition: all 0.25s;
}
.card:hover { transform: translateY(-2px); }

.card-plan { background: linear-gradient(135deg, #2d1b4e 0%, #4a1d6b 100%); border: 1px solid rgba(168,85,247,0.25); }
.card-plan:hover { box-shadow: 0 8px 24px rgba(168,85,247,0.2); }
.card-plan .card-header svg { color: #a78bfa; }
.card-plan .card-value { color: #a78bfa; }
.card-plan .card-link { color: #c4b5fd; }

.card-traffic { background: linear-gradient(135deg, #0f3d3a 0%, #1a5a4a 100%); border: 1px solid rgba(52,211,153,0.25); }
.card-traffic:hover { box-shadow: 0 8px 24px rgba(52,211,153,0.2); }
.card-traffic .card-header svg { color: #34d399; }
.card-traffic .card-value { color: #34d399; }

.card-expiry { background: linear-gradient(135deg, #3d2d0e 0%, #5c3d10 100%); border: 1px solid rgba(251,191,36,0.25); }
.card-expiry:hover { box-shadow: 0 8px 24px rgba(251,191,36,0.2); }
.card-expiry .card-header svg { color: #fbbf24; }
.card-expiry .card-value { color: #fbbf24; }

.card-balance { background: linear-gradient(135deg, #1e3a5f 0%, #2a4a7a 100%); border: 1px solid rgba(59,130,246,0.25); }
.card-balance:hover { box-shadow: 0 8px 24px rgba(59,130,246,0.2); }
.card-balance .card-header svg { color: #60a5fa; }
.card-balance .card-value { color: #60a5fa; }
.card-balance .card-link { color: #93c5fd; }

.card-bg-icon {
  position: absolute;
  right: -8px;
  bottom: -8px;
  opacity: 0.08;
  pointer-events: none;
}
.card-bg-icon svg { display: block; }

.card-body { position: relative; z-index: 1; }
.card-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; }
.card-header span { font-size: 0.8rem; color: rgba(255,255,255,0.6); font-weight: 500; }
.card-value { margin: 0 0 0.35rem; font-size: 1.35rem; font-weight: 700; }
.card-unit { font-size: 0.85rem; font-weight: 400; color: rgba(255,255,255,0.4); }
.card-link { font-size: 0.8rem; font-weight: 500; text-decoration: none; }
.card-link:hover { text-decoration: underline; }
.card-meta { font-size: 0.75rem; color: rgba(255,255,255,0.45); }

.fuel-gauge { height: 6px; background: rgba(0,0,0,0.25); border-radius: 3px; overflow: hidden; margin-bottom: 0.35rem; }
.fuel-fill { height: 100%; background: linear-gradient(90deg, #34d399, #38bdf8); border-radius: 3px; transition: width 0.5s ease; }

.subscribe-section { background: var(--bg-card); backdrop-filter: blur(12px); padding: 1.25rem; border-radius: var(--radius); border: 1px solid var(--border); }
.sub-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem; }
.sub-header span { font-weight: 600; font-size: 0.95rem; }
.sub-links { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; }
.sub-item { display: flex; flex-direction: column; align-items: center; gap: 0.5rem; padding: 1rem; border-radius: var(--radius-sm); cursor: pointer; transition: all 0.2s; }
.sub-item:hover { transform: translateY(-2px); }

.sub-v2ray { background: linear-gradient(135deg, #1e2a5a 0%, #2a3d7a 100%); border: 1px solid rgba(99,102,241,0.25); }
.sub-v2ray:hover { box-shadow: 0 4px 16px rgba(99,102,241,0.2); }
.sub-v2ray .sub-icon { background: rgba(99,102,241,0.2); color: #818cf8; }
.sub-v2ray .sub-label { color: #a5b4fc; }
.sub-v2ray .copy-badge { background: rgba(99,102,241,0.15); color: #818cf8; }

.sub-clash { background: linear-gradient(135deg, #4a1a1a 0%, #6b2020 100%); border: 1px solid rgba(239,68,68,0.25); }
.sub-clash:hover { box-shadow: 0 4px 16px rgba(239,68,68,0.2); }
.sub-clash .sub-icon { background: rgba(239,68,68,0.2); color: #f87171; }
.sub-clash .sub-label { color: #fca5a5; }
.sub-clash .copy-badge { background: rgba(239,68,68,0.15); color: #f87171; }

.sub-singbox { background: linear-gradient(135deg, #0a3d2a 0%, #105a3a 100%); border: 1px solid rgba(52,211,153,0.25); }
.sub-singbox:hover { box-shadow: 0 4px 16px rgba(52,211,153,0.2); }
.sub-singbox .sub-icon { background: rgba(52,211,153,0.2); color: #34d399; }
.sub-singbox .sub-label { color: #6ee7b7; }
.sub-singbox .copy-badge { background: rgba(52,211,153,0.15); color: #34d399; }

.sub-icon { width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border-radius: 8px; }
.sub-label { font-size: 0.9rem; font-weight: 600; }
.copy-badge { font-size: 0.7rem; padding: 0.15rem 0.5rem; border-radius: 4px; font-weight: 500; }
</style>
