<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { profile } from '../api/profile'
import { getSubscribeBaseUrl } from '../api/subscribe'
import { copiedKey, copyText } from '../api/copy'

const router = useRouter()
const origin = getSubscribeBaseUrl()
const activeTab = ref('v2ray')

const tabs = [
  { id: 'v2ray', label: 'V2Ray' },
  { id: 'clash', label: 'Clash' },
  { id: 'singbox', label: 'Sing-box' },
  { id: 'shadowrocket', label: 'Shadowrocket' },
  { id: 'stash', label: 'Stash' },
]

function subUrl(fmt?: string) {
  const t = profile.subscription_token
  if (!t) return ''
  if (fmt === 'clash') return `${origin}/api/subscription/${t}/clashmeta/`
  if (fmt === 'singbox') return `${origin}/api/subscription/${t}/singbox/`
  return `${origin}/api/subscription/${t}/`
}

function goPlans() {
  router.push('/plans')
}
</script>

<template>
  <div class="tutorial-page">
    <h2>使用教程</h2>

    <div v-if="profile.loaded && !profile.plan_name" class="plan-warning">
      <div class="plan-warning-icon">!</div>
      <div class="plan-warning-text">
        <strong>请先<a href="javascript:;" @click="goPlans">购买套餐</a>后再使用订阅链接</strong>
        <p>订阅链接需要绑定有效套餐才能正常使用，点击上方链接查看套餐方案。</p>
      </div>
    </div>

    <div v-if="!profile.loaded" class="loading-subs">
      <div v-for="n in 3" :key="n" class="skeleton-line w-48 h-3"></div>
    </div>

    <div class="tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="['tab-btn', { active: activeTab === tab.id }]"
        @click="activeTab = tab.id"
      >{{ tab.label }}</button>
    </div>

    <!-- V2Ray -->
    <div v-if="activeTab === 'v2ray'" class="guide">
      <p class="guide-desc">V2Ray 客户端支持 VLESS、VMess、Shadowsocks、Trojan 等多种协议，通用性最强。</p>

      <section>
        <h3>Windows — v2rayN</h3>
        <ol>
          <li>下载 <a href="https://github.com/2dust/v2rayN/releases" target="_blank">v2rayN</a>，解压运行</li>
          <li>点击任务栏图标 → <strong>参数设置</strong> → <strong>订阅设置</strong></li>
          <li>点击 <strong>添加</strong>，粘贴下方订阅链接，备注随意</li>
          <li>点击 <strong>确定</strong>，右键任务栏图标 → <strong>更新订阅</strong>（不通过代理）</li>
          <li>右键服务器列表中的节点 → <strong>设为活动服务器</strong></li>
          <li>右键任务栏图标 → <strong>系统代理</strong> → <strong>自动配置系统代理</strong></li>
        </ol>
        <div class="sub-row" v-if="profile.subscription_token">
          <code>{{ subUrl() }}</code>
          <button @click="copyText(subUrl(), 'tut-v2ray')" class="btn-copy">{{ copiedKey === 'tut-v2ray' ? '已复制' : '复制链接' }}</button>
        </div>
      </section>

      <section>
        <h3>Android — V2RayNG</h3>
        <ol>
          <li>从 Google Play 或 <a href="https://github.com/2dust/v2rayNG/releases" target="_blank">GitHub</a> 下载 V2RayNG</li>
          <li>打开应用，点击右上角 <strong>+</strong> → <strong>导入订阅链接</strong></li>
          <li>粘贴下方订阅链接，点击 <strong>√</strong></li>
          <li>点击左上角菜单 → 勾选节点 → 点击右下角 <strong>V</strong> 图标连接</li>
        </ol>
        <div class="sub-row" v-if="profile.subscription_token">
          <code>{{ subUrl() }}</code>
          <button @click="copyText(subUrl(), 'tut-v2ray-and')" class="btn-copy">{{ copiedKey === 'tut-v2ray-and' ? '已复制' : '复制链接' }}</button>
        </div>
      </section>

      <section>
        <h3>macOS — V2RayX / V2RayU</h3>
        <ol>
          <li>下载 <a href="https://github.com/Cenmrev/V2RayX/releases" target="_blank">V2RayX</a> 或 <a href="https://github.com/yanue/V2RayU/releases" target="_blank">V2RayU</a></li>
          <li>打开应用，进入 <strong>订阅</strong> 或 <strong>Import Subscription</strong></li>
          <li>粘贴下方订阅链接，点击导入</li>
          <li>选择节点，点击 <strong>连接</strong></li>
        </ol>
        <div class="sub-row" v-if="profile.subscription_token">
          <code>{{ subUrl() }}</code>
          <button @click="copyText(subUrl(), 'tut-v2ray-mac')" class="btn-copy">{{ copiedKey === 'tut-v2ray-mac' ? '已复制' : '复制链接' }}</button>
        </div>
      </section>

      <section>
        <h3>iOS — FairVPN / Streisand</h3>
        <ol>
          <li>在 App Store 搜索下载 FairVPN 或 Streisand</li>
          <li>打开应用 → <strong>导入配置</strong> → <strong>从 URL 下载</strong></li>
          <li>粘贴下方订阅链接，导入后选择节点连接</li>
        </ol>
        <div class="sub-row" v-if="profile.subscription_token">
          <code>{{ subUrl() }}</code>
          <button @click="copyText(subUrl(), 'tut-v2ray-ios')" class="btn-copy">{{ copiedKey === 'tut-v2ray-ios' ? '已复制' : '复制链接' }}</button>
        </div>
      </section>
    </div>

    <!-- Clash -->
    <div v-if="activeTab === 'clash'" class="guide">
      <p class="guide-desc">Clash 内核支持 VLESS、Shadowsocks、Trojan、Hysteria2 等协议，一个客户端全协议支持。</p>

      <section>
        <h3>全平台 — Clash Verge</h3>
        <ol>
          <li>下载 <a href="https://github.com/clash-verge-rev/clash-verge-rev/releases" target="_blank">Clash Verge Rev</a>（Windows / macOS / Linux）</li>
          <li>安装后打开，进入 <strong>订阅</strong> 页面</li>
          <li>点击 <strong>添加</strong>，粘贴下方 Clash 订阅链接</li>
          <li>点击 <strong>导入</strong>，然后点击 <strong>启用</strong></li>
          <li>切换到 <strong>代理</strong> 页面，选择节点 → <strong>规则</strong> 或 <strong>全局</strong> 模式</li>
        </ol>
        <div class="sub-row" v-if="profile.subscription_token">
          <code>{{ subUrl('clash') }}</code>
          <button @click="copyText(subUrl('clash'), 'tut-clash')" class="btn-copy">{{ copiedKey === 'tut-clash' ? '已复制' : '复制链接' }}</button>
        </div>
      </section>

      <section>
        <h3>Android — Clash Meta for Android</h3>
        <ol>
          <li>下载 <a href="https://github.com/MetaCubeX/ClashMetaForAndroid/releases" target="_blank">Clash Meta for Android</a></li>
          <li>打开应用 → <strong>配置</strong> → 右上角 <strong>+</strong> → <strong>从 URL 导入</strong></li>
          <li>粘贴 Clash 订阅链接，下载后启用</li>
          <li>返回主页，点击 <strong>启动</strong></li>
        </ol>
        <div class="sub-row" v-if="profile.subscription_token">
          <code>{{ subUrl('clash') }}</code>
          <button @click="copyText(subUrl('clash'), 'tut-clash-and')" class="btn-copy">{{ copiedKey === 'tut-clash-and' ? '已复制' : '复制链接' }}</button>
        </div>
      </section>

      <section>
        <h3>iOS — Stash</h3>
        <p>Clash 在 iOS 上的最佳选择是 <router-link to="/tutorials" @click="activeTab='stash'">Stash</router-link>，见下方 Stash 教程。</p>
        <div class="sub-row" v-if="profile.subscription_token">
          <code>{{ subUrl('clash') }}</code>
          <button @click="copyText(subUrl('clash'), 'tut-clash-ios')" class="btn-copy">{{ copiedKey === 'tut-clash-ios' ? '已复制' : '复制链接' }}</button>
        </div>
      </section>
    </div>

    <!-- Sing-box -->
    <div v-if="activeTab === 'singbox'" class="guide">
      <p class="guide-desc">Sing-box 是新一代通用代理平台，轻量高性能。</p>

      <section>
        <h3>全平台</h3>
        <ol>
          <li>下载 <a href="https://github.com/SagerNet/sing-box/releases" target="_blank">Sing-box</a> 对应系统的版本</li>
          <li>GUI 客户端推荐：<a href="https://github.com/Firewallv2/Firewallv2/releases" target="_blank">Firewall</a>（Windows）、Sing-box（macOS）</li>
          <li>在客户端中导入下方 Sing-box 格式订阅链接</li>
          <li>选择节点，启用代理</li>
        </ol>
        <div class="sub-row" v-if="profile.subscription_token">
          <code>{{ subUrl('singbox') }}</code>
          <button @click="copyText(subUrl('singbox'), 'tut-sing')" class="btn-copy">{{ copiedKey === 'tut-sing' ? '已复制' : '复制链接' }}</button>
        </div>
      </section>

      <section>
        <h3>Android — Firewall / Sing-box</h3>
        <ol>
          <li>下载 <a href="https://play.google.com/store/apps/details?id=io.nekohasekai.sfa" target="_blank">Sing-box</a> 或 <a href="https://github.com/Firewallv2/Firewallv2/releases" target="_blank">Firewall</a></li>
          <li>打开应用 → <strong>配置</strong> → <strong>远程配置</strong></li>
          <li>粘贴下方 Sing-box 订阅链接，保存</li>
          <li>启用配置，连接</li>
        </ol>
        <div class="sub-row" v-if="profile.subscription_token">
          <code>{{ subUrl('singbox') }}</code>
          <button @click="copyText(subUrl('singbox'), 'tut-sing-and')" class="btn-copy">{{ copiedKey === 'tut-sing-and' ? '已复制' : '复制链接' }}</button>
        </div>
      </section>
    </div>

    <!-- Shadowrocket -->
    <div v-if="activeTab === 'shadowrocket'" class="guide">
      <p class="guide-desc">Shadowrocket 是 iOS 上最流行的代理客户端，支持多种协议和订阅。</p>

      <section>
        <h3>iOS — Shadowrocket（小火箭）</h3>
        <ol>
          <li>在 App Store 搜索 <strong>Shadowrocket</strong>（需美区/港区 Apple ID）</li>
          <li>打开应用，点击右上角 <strong>+</strong> → <strong>类型</strong> 选择 <strong>Subscribe</strong></li>
          <li>在 <strong>URL</strong> 栏粘贴下方订阅链接，点击 <strong>完成</strong></li>
          <li>回到主页，所有节点会出现在列表中</li>
          <li>点击右上角开关按钮连接，选择节点</li>
        </ol>
        <div class="sub-row" v-if="profile.subscription_token">
          <code>{{ subUrl() }}</code>
          <button @click="copyText(subUrl(), 'tut-rocket')" class="btn-copy">{{ copiedKey === 'tut-rocket' ? '已复制' : '复制链接' }}</button>
        </div>
      </section>

      <section>
        <h3>快捷操作</h3>
        <ul>
          <li>长按节点可测试延迟</li>
          <li>右上角 <strong>设置</strong> → <strong>配置</strong> 可切换规则模式</li>
          <li>支持手动切换 <strong>全局路由</strong> / <strong>配置</strong> / <strong>直连</strong></li>
        </ul>
      </section>
    </div>

    <!-- Stash -->
    <div v-if="activeTab === 'stash'" class="guide">
      <p class="guide-desc">Stash 是 iOS 上功能最强大的 Clash 客户端，支持完整的 Clash 协议和规则。</p>

      <section>
        <h3>iOS — Stash</h3>
        <ol>
          <li>在 App Store 搜索 <strong>Stash</strong>（需美区/港区 Apple ID）</li>
          <li>打开应用 → <strong>设置</strong> → <strong>订阅</strong></li>
          <li>点击 <strong>添加订阅</strong>，粘贴下方 Clash 订阅链接</li>
          <li>返回主页，点击 <strong>启动</strong></li>
          <li>在 <strong>策略</strong> 页面选择节点或使用自动策略组</li>
        </ol>
        <div class="sub-row" v-if="profile.subscription_token">
          <code>{{ subUrl('clash') }}</code>
          <button @click="copyText(subUrl('clash'), 'tut-stash')" class="btn-copy">{{ copiedKey === 'tut-stash' ? '已复制' : '复制链接' }}</button>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.tutorial-page { max-width: 800px; }
h2 { margin-bottom: 1.5rem; }

.loading-subs { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1.5rem; }
.skeleton-line { height: 0.75rem; background: var(--border); border-radius: 4px; animation: pulse 1.5s infinite; }
@keyframes pulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 0.8; } }
.w-48 { width: 12rem; }

.plan-warning {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem;
  margin-bottom: 1.5rem;
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: var(--radius);
}
.plan-warning-icon {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(251, 191, 36, 0.2);
  color: #f59e0b;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1rem;
  flex-shrink: 0;
}
.plan-warning-text strong { font-size: 0.9rem; color: var(--text-primary); }
.plan-warning-text p { margin: 0.25rem 0 0; font-size: 0.8rem; color: var(--text-secondary); }
.plan-warning-text a { color: var(--accent); cursor: pointer; }
.plan-warning-text a:hover { text-decoration: underline; }

.tab-bar { display: flex; gap: 0.25rem; margin-bottom: 1.5rem; background: var(--bg-card); padding: 0.25rem; border-radius: var(--radius); border: 1px solid var(--border); overflow-x: auto; }
.tab-btn { padding: 0.5rem 1rem; border: none; background: transparent; color: var(--text-secondary); border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 500; white-space: nowrap; transition: all 0.2s; }
.tab-btn:hover { color: var(--text-primary); }
.tab-btn.active { background: var(--accent-gradient); color: #fff; }

.guide { animation: fadeIn 0.2s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }

.guide-desc { color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1.5rem; padding: 0.75rem 1rem; background: var(--accent-soft); border-radius: var(--radius-sm); border: 1px solid var(--border); }

section { margin-bottom: 1.5rem; background: var(--bg-card); backdrop-filter: blur(12px); padding: 1.25rem; border-radius: var(--radius); border: 1px solid var(--border); }
section h3 { margin: 0 0 0.75rem; font-size: 1rem; }
section ol, section ul { margin: 0; padding-left: 1.25rem; }
section li { font-size: 0.875rem; line-height: 1.8; color: var(--text-secondary); }
section a { color: var(--accent); }
section a:hover { text-decoration: underline; }

.sub-row { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.75rem; padding: 0.5rem 0.75rem; background: var(--bg-primary); border-radius: 6px; border: 1px solid var(--border); }
.sub-row code { flex: 1; font-size: 0.7rem; word-break: break-all; color: var(--text-muted); user-select: all; }
.btn-copy { background: var(--accent); color: #fff; border: none; padding: 0.35rem 0.75rem; border-radius: 6px; cursor: pointer; font-size: 0.75rem; font-weight: 500; transition: all 0.2s; flex-shrink: 0; }
.btn-copy:hover { opacity: 0.9; transform: translateY(-1px); box-shadow: 0 2px 8px rgba(56,189,248,0.3); }
.btn-copy:active { transform: translateY(0); }
</style>
