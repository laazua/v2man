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
        <div class="skeleton-line w-24 h-3"></div>
        <div class="skeleton-line w-full h-8 mt-2"></div>
      </div>
      <div v-for="n in 3" :key="n" class="skeleton-row">
        <div class="skeleton-icon"></div>
        <div class="skeleton-body">
          <div class="skeleton-line w-20 h-3"></div>
          <div class="skeleton-line w-full h-3 mt-1"></div>
        </div>
        <div class="skeleton-line w-14 h-7"></div>
      </div>
    </div>

    <div v-else-if="!profile.plan_name" class="status-box no-plan">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2L11 13"/><path d="M22 2L15 22L11 13L2 9L22 2Z"/></svg>
      <p>您还没有购买套餐，购买后可获取订阅链接</p>
      <router-link to="/plans" class="btn-buy">去购买套餐 →</router-link>
    </div>

    <div v-else-if="!profile.subscription_token" class="status-box no-plan">
      <p>订阅链接生成异常，请联系管理员</p>
    </div>

    <div v-else class="sub-content">
      <div class="token-card">
        <span class="token-label">订阅 Token</span>
        <div class="token-row">
          <code class="token-value">{{ profile.subscription_token }}</code>
          <button @click="copyText(profile.subscription_token!, 'sub-token')" class="btn-copy">{{ copiedKey === 'sub-token' ? '已复制' : '复制' }}</button>
        </div>
      </div>

      <div class="sub-item">
        <div class="sub-icon-wrap">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
        </div>
        <div class="sub-body">
          <label>V2Ray (Base64)</label>
          <code>{{ origin }}/api/subscription/{{ profile.subscription_token }}/</code>
        </div>
        <button @click="copyText(`${origin}/api/subscription/${profile.subscription_token}/`, 'sub-v2ray')" class="btn-copy">{{ copiedKey === 'sub-v2ray' ? '已复制' : '复制' }}</button>
      </div>
      <div class="sub-item">
        <div class="sub-icon-wrap">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"/><line x1="12" y1="22" x2="12" y2="15.5"/><polyline points="22 8.5 12 15.5 2 8.5"/></svg>
        </div>
        <div class="sub-body">
          <label>Clash</label>
          <code>{{ origin }}/api/subscription/{{ profile.subscription_token }}/clashmeta/</code>
        </div>
        <button @click="copyText(`${origin}/api/subscription/${profile.subscription_token}/clashmeta/`, 'sub-clash')" class="btn-copy">{{ copiedKey === 'sub-clash' ? '已复制' : '复制' }}</button>
      </div>
      <div class="sub-item">
        <div class="sub-icon-wrap">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
        </div>
        <div class="sub-body">
          <label>Sing-box</label>
          <code>{{ origin }}/api/subscription/{{ profile.subscription_token }}/singbox/</code>
        </div>
        <button @click="copyText(`${origin}/api/subscription/${profile.subscription_token}/singbox/`, 'sub-singbox')" class="btn-copy">{{ copiedKey === 'sub-singbox' ? '已复制' : '复制' }}</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sub-page { max-width: 700px; }
h2 { margin-bottom: 1.5rem; }

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
.skeleton-card { background: var(--bg-card); padding: 1rem 1.25rem; border-radius: var(--radius); border: 1px solid var(--border); margin-bottom: 1rem; }
.skeleton-row { display: flex; align-items: center; gap: 0.75rem; padding: 0.85rem 1rem; background: var(--bg-card); border-radius: var(--radius); border: 1px solid var(--border); margin-bottom: 0.75rem; }
.skeleton-icon { width: 36px; height: 36px; border-radius: 8px; flex-shrink: 0; background: var(--bg-hover); animation: shimmer 1.5s infinite; background-size: 200px 100%; }
.skeleton-body { flex: 1; }
.h-3 { height: 12px; }
.h-7 { height: 28px; }
.h-8 { height: 32px; }
.w-14 { width: 56px; }
.w-20 { width: 64px; }
.w-24 { width: 80px; }
.w-full { width: 100%; }
.mt-1 { margin-top: 4px; }
.mt-2 { margin-top: 8px; }

.status-box { display: flex; flex-direction: column; align-items: center; gap: 1rem; background: var(--bg-card); backdrop-filter: blur(12px); padding: 2.5rem; border-radius: var(--radius); border: 1px solid var(--border); text-align: center; color: var(--text-muted); }
.status-box p { margin: 0; }
.btn-buy { display: inline-block; background: var(--accent-gradient); color: #fff; padding: 0.5rem 1.25rem; border-radius: 6px; text-decoration: none; font-size: 0.9rem; font-weight: 500; transition: all 0.2s; }
.btn-buy:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(56,189,248,0.3); }

.token-card { background: var(--bg-card); backdrop-filter: blur(12px); padding: 1rem 1.25rem; border-radius: var(--radius); border: 1px solid var(--border); margin-bottom: 1rem; }
.token-label { display: block; font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.5rem; font-weight: 500; }
.token-row { display: flex; align-items: center; gap: 0.75rem; }
.token-value { flex: 1; font-size: 0.85rem; word-break: break-all; color: var(--text-primary); background: var(--bg-primary); padding: 0.5rem 0.75rem; border-radius: 6px; border: 1px solid var(--border); font-family: 'SF Mono', 'Fira Code', monospace; }

.sub-item { display: flex; align-items: center; gap: 0.75rem; padding: 0.85rem 1rem; background: var(--bg-card); backdrop-filter: blur(12px); border-radius: var(--radius); border: 1px solid var(--border); margin-bottom: 0.75rem; transition: all 0.2s; }
.sub-item:hover { border-color: var(--accent); }
.sub-icon-wrap { width: 36px; height: 36px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; background: var(--accent-soft); border-radius: 8px; color: var(--accent); }
.sub-body { flex: 1; min-width: 0; }
.sub-body label { display: block; font-size: 0.8rem; font-weight: 500; margin-bottom: 0.15rem; }
.sub-body code { display: block; font-size: 0.7rem; word-break: break-all; color: var(--text-muted); }
.btn-copy { background: var(--accent); color: #fff; border: none; padding: 0.35rem 0.85rem; border-radius: 6px; cursor: pointer; font-size: 0.75rem; font-weight: 500; transition: all 0.2s; flex-shrink: 0; }
.btn-copy:hover { opacity: 0.9; transform: translateY(-1px); box-shadow: 0 2px 8px rgba(56,189,248,0.3); }
</style>
