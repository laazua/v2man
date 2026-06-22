<script setup lang="ts">
import { profile } from '../api/profile'
import { getSubscribeBaseUrl } from '../api/subscribe'
import { copiedKey, copyText } from '../api/copy'

const origin = getSubscribeBaseUrl()
</script>

<template>
  <div class="sub-page">
    <h2>订阅链接</h2>

    <div v-if="!profile.loaded" class="sub-skeleton">
      <div class="skeleton-card">
        <div class="skeleton-accent"></div>
        <div class="skeleton-body">
          <div class="skeleton-line w-32 h-3"></div>
          <div class="skeleton-line w-full h-9 mt-2"></div>
          <div class="skeleton-line w-40 h-3 mt-2"></div>
        </div>
      </div>
      <div class="skeleton-grid">
        <div v-for="n in 3" :key="n" class="skeleton-sub">
          <div class="skeleton-line w-20 h-3"></div>
          <div class="skeleton-line w-16 h-7 mt-3"></div>
        </div>
      </div>
    </div>

    <div v-else-if="!profile.plan_name" class="status-box no-plan">
      <svg class="status-icon" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2L11 13"/><path d="M22 2L15 22L11 13L2 9L22 2Z"/></svg>
      <p class="status-text">您还没有购买套餐，购买后可获取订阅链接</p>
      <router-link to="/plans" class="btn-buy">去购买套餐 →</router-link>
    </div>

    <div v-else-if="!profile.subscription_token" class="status-box no-plan">
      <svg class="status-icon" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      <p class="status-text">订阅链接生成异常，请联系管理员</p>
    </div>

    <div v-else class="sub-content">
      <div class="token-card">
        <div class="token-header">
          <svg class="token-header-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>
          <span>订阅 Token</span>
        </div>
        <div class="token-row">
          <code class="token-value">{{ profile.subscription_token }}</code>
          <button @click="copyText(profile.subscription_token!, 'sub-token')" :class="['token-copy', { copied: copiedKey === 'sub-token' }]">
            <svg v-if="copiedKey !== 'sub-token'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
            <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            {{ copiedKey === 'sub-token' ? '已复制' : '复制' }}
          </button>
        </div>
        <p class="token-hint">将此 Token 填入支持手动配置的客户端以连接服务器</p>
      </div>

      <p class="section-title">选择客户端格式</p>

      <div class="sub-grid">
        <div class="sub-card sub-v2ray">
          <div class="sub-card-bg">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
          </div>
          <div class="sub-card-body">
            <div class="sub-card-top">
              <div class="sub-card-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
              </div>
              <div class="sub-card-info">
                <span class="sub-card-name">V2Ray (Base64)</span>
                <span class="sub-card-desc">标准 V2Ray 订阅格式，适用于 V2Ray 内核客户端</span>
              </div>
            </div>
            <button @click="copyText(`${origin}/api/subscription/${profile.subscription_token}/`, 'sub-v2ray')" :class="['sub-card-copy', { copied: copiedKey === 'sub-v2ray' }]">
              <svg v-if="copiedKey !== 'sub-v2ray'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              {{ copiedKey === 'sub-v2ray' ? '已复制' : '复制链接' }}
            </button>
          </div>
        </div>

        <div class="sub-card sub-clash">
          <div class="sub-card-bg">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"/><line x1="12" y1="22" x2="12" y2="15.5"/><polyline points="22 8.5 12 15.5 2 8.5"/></svg>
          </div>
          <div class="sub-card-body">
            <div class="sub-card-top">
              <div class="sub-card-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"/><line x1="12" y1="22" x2="12" y2="15.5"/><polyline points="22 8.5 12 15.5 2 8.5"/></svg>
              </div>
              <div class="sub-card-info">
                <span class="sub-card-name">Clash Meta</span>
                <span class="sub-card-desc">适用于 Clash Meta / mihomo 内核的代理客户端</span>
              </div>
            </div>
            <button @click="copyText(`${origin}/api/subscription/${profile.subscription_token}/clashmeta/`, 'sub-clash')" :class="['sub-card-copy', { copied: copiedKey === 'sub-clash' }]">
              <svg v-if="copiedKey !== 'sub-clash'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              {{ copiedKey === 'sub-clash' ? '已复制' : '复制链接' }}
            </button>
          </div>
        </div>

        <div class="sub-card sub-singbox">
          <div class="sub-card-bg">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
          </div>
          <div class="sub-card-body">
            <div class="sub-card-top">
              <div class="sub-card-icon">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
              </div>
              <div class="sub-card-info">
                <span class="sub-card-name">Sing-box</span>
                <span class="sub-card-desc">通用代理格式，支持 Sing-box 通用代理工具</span>
              </div>
            </div>
            <button @click="copyText(`${origin}/api/subscription/${profile.subscription_token}/singbox/`, 'sub-singbox')" :class="['sub-card-copy', { copied: copiedKey === 'sub-singbox' }]">
              <svg v-if="copiedKey !== 'sub-singbox'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
              <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              {{ copiedKey === 'sub-singbox' ? '已复制' : '复制链接' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sub-page { max-width: 820px; }
h2 { margin-bottom: 1.5rem; }

/* ── Skeleton ── */
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
.skeleton-card { background: var(--bg-card); border-radius: var(--radius); border: 1px solid var(--border); display: flex; overflow: hidden; margin-bottom: 1.25rem; }
.skeleton-accent { width: 4px; flex-shrink: 0; background: var(--bg-hover); }
.skeleton-body { padding: 1.25rem; flex: 1; }
.skeleton-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; }
.skeleton-sub { background: var(--bg-card); padding: 1rem; border-radius: var(--radius); border: 1px solid var(--border); }
.w-16 { width: 64px; }
.w-20 { width: 64px; }
.w-32 { width: 80px; }
.w-40 { width: 100px; }
.w-full { width: 100%; }
.h-3 { height: 12px; }
.h-6 { height: 24px; }
.h-7 { height: 28px; }
.h-9 { height: 36px; }
.mt-2 { margin-top: 8px; }
.mt-3 { margin-top: 12px; }

/* ── Status ── */
.status-box { display: flex; flex-direction: column; align-items: center; gap: 1rem; background: var(--bg-card); backdrop-filter: blur(12px); padding: 3rem 2.5rem; border-radius: var(--radius); border: 1px solid var(--border); text-align: center; color: var(--text-muted); }
.status-icon { opacity: 0.4; }
.status-text { margin: 0; font-size: 0.9rem; line-height: 1.6; }
.btn-buy { display: inline-block; background: var(--accent-gradient); color: #fff; padding: 0.55rem 1.5rem; border-radius: 8px; text-decoration: none; font-size: 0.9rem; font-weight: 500; transition: all 0.2s; }
.btn-buy:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(56,189,248,0.3); }

/* ── Token ── */
.token-card { background: var(--bg-card); backdrop-filter: blur(12px); padding: 1.25rem; border-radius: var(--radius); border: 1px solid var(--border); margin-bottom: 1.5rem; }
.token-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; }
.token-header-icon { color: var(--accent); }
.token-header span { font-size: 0.85rem; font-weight: 600; color: var(--text-secondary); }
.token-row { display: flex; align-items: center; gap: 0.75rem; }
.token-value { flex: 1; font-size: 0.8rem; word-break: break-all; color: var(--text-primary); background: var(--bg-primary); padding: 0.55rem 0.75rem; border-radius: 6px; border: 1px solid var(--border); font-family: 'SF Mono', 'Fira Code', monospace; user-select: all; }
.token-copy { display: flex; align-items: center; gap: 0.35rem; background: var(--accent); color: #fff; border: none; padding: 0.4rem 1rem; border-radius: 6px; cursor: pointer; font-size: 0.78rem; font-weight: 500; transition: all 0.2s; flex-shrink: 0; white-space: nowrap; }
.token-copy:hover { opacity: 0.9; transform: translateY(-1px); box-shadow: 0 2px 8px rgba(56,189,248,0.3); }
.token-copy.copied { background: var(--success); }
.token-hint { margin: 0.65rem 0 0; font-size: 0.75rem; color: var(--text-muted); }

/* ── Section Title ── */
.section-title { font-size: 0.8rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; margin: 0 0 0.75rem; }

/* ── Sub Grid ── */
.sub-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; }

/* ── Sub Card ── */
.sub-card {
  position: relative;
  border-radius: var(--radius);
  overflow: hidden;
  transition: all 0.25s;
}
.sub-card:hover { transform: translateY(-2px); }

.sub-card-bg {
  position: absolute;
  right: -10px;
  bottom: -10px;
  opacity: 0.06;
  pointer-events: none;
}
.sub-card-bg svg { display: block; }

.sub-card-body {
  position: relative;
  z-index: 1;
  padding: 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.sub-card-top { display: flex; align-items: flex-start; gap: 0.65rem; }
.sub-card-icon {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
}
.sub-card-info { flex: 1; min-width: 0; }
.sub-card-name { display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.15rem; }
.sub-card-desc { display: block; font-size: 0.68rem; line-height: 1.4; opacity: 0.7; }

.sub-card-copy {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  background: transparent;
  border: 1px solid;
  border-radius: 6px;
  padding: 0.4rem 0.75rem;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.2s;
  white-space: nowrap;
}
.sub-card-copy:hover { opacity: 0.9; }

/* ── V2Ray ── */
.sub-v2ray { background: linear-gradient(135deg, #1e2a5a 0%, #2a3d7a 100%); border: 1px solid rgba(99,102,241,0.25); }
.sub-v2ray:hover { box-shadow: 0 6px 20px rgba(99,102,241,0.2); }
.sub-v2ray .sub-card-icon { background: rgba(99,102,241,0.2); color: #818cf8; }
.sub-v2ray .sub-card-name { color: #a5b4fc; }
.sub-v2ray .sub-card-desc { color: #a5b4fc; }
.sub-v2ray .sub-card-url code { color: #c7d2fe; }
.sub-v2ray .sub-card-copy { border-color: rgba(99,102,241,0.3); color: #818cf8; }
.sub-v2ray .sub-card-copy:hover { background: rgba(99,102,241,0.15); border-color: #818cf8; }
.sub-v2ray .sub-card-copy.copied { border-color: #34d399; color: #34d399; background: rgba(52,211,153,0.1); }

/* ── Clash ── */
.sub-clash { background: linear-gradient(135deg, #4a1a1a 0%, #6b2020 100%); border: 1px solid rgba(239,68,68,0.25); }
.sub-clash:hover { box-shadow: 0 6px 20px rgba(239,68,68,0.2); }
.sub-clash .sub-card-icon { background: rgba(239,68,68,0.2); color: #f87171; }
.sub-clash .sub-card-name { color: #fca5a5; }
.sub-clash .sub-card-desc { color: #fca5a5; }
.sub-clash .sub-card-url code { color: #fecaca; }
.sub-clash .sub-card-copy { border-color: rgba(239,68,68,0.3); color: #f87171; }
.sub-clash .sub-card-copy:hover { background: rgba(239,68,68,0.15); border-color: #f87171; }
.sub-clash .sub-card-copy.copied { border-color: #34d399; color: #34d399; background: rgba(52,211,153,0.1); }

/* ── Sing-box ── */
.sub-singbox { background: linear-gradient(135deg, #0a3d2a 0%, #105a3a 100%); border: 1px solid rgba(52,211,153,0.25); }
.sub-singbox:hover { box-shadow: 0 6px 20px rgba(52,211,153,0.2); }
.sub-singbox .sub-card-icon { background: rgba(52,211,153,0.2); color: #34d399; }
.sub-singbox .sub-card-name { color: #6ee7b7; }
.sub-singbox .sub-card-desc { color: #6ee7b7; }
.sub-singbox .sub-card-url code { color: #a7f3d0; }
.sub-singbox .sub-card-copy { border-color: rgba(52,211,153,0.3); color: #34d399; }
.sub-singbox .sub-card-copy:hover { background: rgba(52,211,153,0.15); border-color: #34d399; }
.sub-singbox .sub-card-copy.copied { border-color: #34d399; color: #34d399; background: rgba(52,211,153,0.1); }

/* ── Responsive ── */
@media (max-width: 720px) {
  .sub-grid { grid-template-columns: 1fr; }
  .skeleton-grid { grid-template-columns: 1fr; }
}
</style>
