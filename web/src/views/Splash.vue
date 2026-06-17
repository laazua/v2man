<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSiteName } from '../api/site'

const router = useRouter()
const siteName = useSiteName()

const phase = ref<'idle' | 'start' | 'climb' | 'cruise' | 'approach' | 'break' | 'glide' | 'done'>('idle')

function goLogin() {
  router.replace('/login')
}

onMounted(() => {
  const t = (ms: number) => new Promise(r => setTimeout(r, ms))

  ;(async () => {
    await t(400)
    phase.value = 'start'
    await t(2000)
    phase.value = 'climb'
    await t(2200)
    phase.value = 'cruise'
    await t(2800)
    phase.value = 'approach'
    await t(2000)
    phase.value = 'break'
    await t(900)
    phase.value = 'glide'
    await t(1800)
    phase.value = 'done'
    await t(3800)
    goLogin()
  })()
})
</script>

<template>
  <div class="splash" @click="goLogin">
    <div class="sky-bg">
      <div class="cloud layer-1 c1"></div>
      <div class="cloud layer-1 c2"></div>
      <div class="cloud layer-2 c3"></div>
      <div class="cloud layer-2 c4"></div>
      <div class="cloud layer-3 c5"></div>
    </div>

    <div class="scene">
      <div class="wall-section" :class="phase">
        <div class="wall">
          <div class="brick" v-for="i in 21" :key="i"
            :class="{
              cracked: phase === 'approach',
              broken: phase === 'break' || phase === 'glide' || phase === 'done'
            }"
            :style="{ '--i': i }"
          ></div>
        </div>
        <div class="wall-glow" :class="{ active: phase === 'approach' || phase === 'break' }"></div>
        <div class="wall-label" :class="{ hidden: phase === 'approach' || phase === 'break' || phase === 'glide' || phase === 'done' }">·</div>
      </div>

      <div class="flight-area">
        <div class="plane-wrap" :class="phase">
          <div class="plane-body">
            <svg viewBox="0 0 90 90" fill="none">
              <defs>
                <linearGradient id="pg" x1="5" y1="20" x2="70" y2="70">
                  <stop offset="0%" stop-color="#60a5fa"/>
                  <stop offset="50%" stop-color="#3b82f6"/>
                  <stop offset="100%" stop-color="#2563eb"/>
                </linearGradient>
                <linearGradient id="wg" x1="50" y1="20" x2="68" y2="65">
                  <stop offset="0%" stop-color="#818cf8"/>
                  <stop offset="100%" stop-color="#6366f1"/>
                </linearGradient>
                <linearGradient id="ps" x1="5" y1="20" x2="70" y2="70">
                  <stop offset="0%" stop-color="#93c5fd"/>
                  <stop offset="100%" stop-color="#6366f1"/>
                </linearGradient>
              </defs>
              <polygon points="4,44 55,26 48,45 55,64 4,46 24,45" fill="url(#pg)" stroke="url(#ps)" stroke-width="1.5" stroke-linejoin="round"/>
              <polygon points="48,45 55,64 65,59 57,45 65,31 55,26" fill="url(#wg)" stroke="url(#ps)" stroke-width="1" stroke-linejoin="round" opacity="0.9"/>
              <polygon points="24,45 4,46 4,44" fill="rgba(59,130,246,0.12)"/>
            </svg>
          </div>
          <div class="propeller" :class="phase">
            <svg viewBox="0 0 20 20" fill="none">
              <ellipse cx="10" cy="10" rx="2" ry="9" fill="rgba(147,197,253,0.3)" transform="rotate(45 10 10)"/>
              <ellipse cx="10" cy="10" rx="9" ry="2" fill="rgba(147,197,253,0.15)" transform="rotate(45 10 10)"/>
            </svg>
          </div>
          <div class="exhaust" v-for="i in 3" :key="i" :class="['ex-' + i, phase]"></div>
        </div>

        <div class="contrail-wrap">
          <div class="contrail-seg seg-1" :class="phase"></div>
          <div class="contrail-seg seg-2" :class="phase"></div>
          <div class="contrail-seg seg-3" :class="phase"></div>
          <div class="contrail-seg seg-4" :class="phase"></div>
        </div>

        <div class="debris" v-for="i in 12" :key="i" :class="['debris-' + i, { active: phase === 'break' || phase === 'glide' || phase === 'done' }]"></div>
        <div class="sparkle" v-for="i in 10" :key="i" :class="['sparkle-' + i, { active: phase === 'glide' || phase === 'done' }]"></div>
      </div>

      <div class="logo-section" :class="{ visible: phase === 'done' }">
        <div class="logo-badge">
          <svg viewBox="0 0 40 40" fill="none">
            <path d="M8 10 L20 30 L32 10" stroke="white" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
            <path d="M14 16 L20 25 L26 16" stroke="rgba(255,255,255,0.5)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
          </svg>
        </div>
        <h1>{{ siteName }}</h1>
        <p class="tagline">冲破壁垒 · 自由互联</p>
      </div>

      <div class="enter-hint" :class="{ visible: phase !== 'idle' }">
        <span class="pulse-dot"></span>
        <span class="hint-text">点击任意处进入</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.splash {
  position: fixed;
  inset: 0;
  background: linear-gradient(180deg, #b7d9f8 0%, #dbeafe 15%, #eff6ff 35%, #f0fdf4 65%, #fef9e7 92%, #fef3c7 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  overflow: hidden;
  user-select: none;
}

.sky-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(ellipse at 15% 20%, rgba(147, 197, 253, 0.3) 0%, transparent 55%),
    radial-gradient(ellipse at 85% 25%, rgba(167, 139, 250, 0.1) 0%, transparent 45%),
    radial-gradient(ellipse at 40% 70%, rgba(252, 211, 77, 0.08) 0%, transparent 40%);
}

/* ===== Clouds ===== */
.cloud {
  position: absolute;
  background: rgba(255, 255, 255, 0.55);
  border-radius: 100px;
  filter: blur(2.5px);
}
.cloud::before, .cloud::after {
  content: '';
  position: absolute;
  background: inherit;
  border-radius: 50%;
}

.layer-1 { opacity: 0.7; }
.layer-2 { opacity: 0.5; transform: scale(0.8); }
.layer-3 { opacity: 0.35; transform: scale(0.6); }

.c1 { width: 240px; height: 34px; top: 12%; animation: drift 55s linear infinite; }
.c1::before { width: 70px; height: 70px; top: -35px; left: 30px; }
.c1::after { width: 90px; height: 58px; top: -24px; left: 90px; }

.c2 { width: 180px; height: 26px; top: 25%; animation: drift 65s linear infinite 10s; }
.c2::before { width: 50px; height: 50px; top: -26px; left: 20px; }
.c2::after { width: 68px; height: 42px; top: -18px; left: 65px; }

.c3 { width: 200px; height: 30px; top: 8%; animation: drift 70s linear infinite 20s; }
.c3::before { width: 60px; height: 60px; top: -30px; left: 25px; }
.c3::after { width: 75px; height: 48px; top: -20px; left: 75px; }

.c4 { width: 160px; height: 24px; top: 20%; animation: drift 60s linear infinite 5s; }
.c4::before { width: 42px; height: 42px; top: -24px; left: 15px; }
.c4::after { width: 55px; height: 35px; top: -16px; left: 55px; }

.c5 { width: 130px; height: 20px; top: 16%; animation: drift 75s linear infinite -8s; }
.c5::before { width: 35px; height: 35px; top: -20px; left: 12px; }
.c5::after { width: 48px; height: 30px; top: -14px; left: 45px; }

@keyframes drift {
  0% { transform: translateX(-300px); }
  100% { transform: translateX(calc(100vw + 300px)); }
}

/* ===== Scene Container ===== */
.scene {
  position: relative;
  width: 720px;
  height: 460px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ===== Wall ===== */
.wall-section {
  position: absolute;
  right: 30px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 2;
  transition: all 0.3s;
}

.wall-section.approach { animation: screenShake 0.08s infinite; }
.wall-section.break { animation: screenShake 0.04s infinite; }

@keyframes screenShake {
  0%, 100% { transform: translateY(-50%) translate(0, 0); }
  25% { transform: translateY(-50%) translate(-2px, 1px); }
  50% { transform: translateY(-50%) translate(2px, -1px); }
  75% { transform: translateY(-50%) translate(-1px, -2px); }
}

.wall {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2px;
  width: 110px;
}

.wall .brick:nth-child(odd) {
  margin-left: 0;
}

.wall .brick:nth-child(even) {
  margin-left: 0;
}

.brick {
  height: 22px;
  background: rgba(148, 163, 184, 0.12);
  border: 1px solid rgba(148, 163, 184, 0.15);
  border-radius: 2px;
  transition: all 0.4s ease;
  position: relative;
}

/* brick positions for odd-even row stagger */
.brick:nth-child(3n+1) { width: 100%; }
.brick:nth-child(3n+2) { width: 100%; margin-top: 0; }
.brick:nth-child(3n) { width: 100%; }

/* approach phase - cracks form */
.brick.cracked {
  animation: crackForm 0.3s ease forwards;
}

.brick.cracked::before {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(239, 68, 68, 0.08);
  animation: crackLine 0.3s ease forwards;
}

@keyframes crackLine {
  0% { clip-path: inset(50% 50% 50% 50%); }
  100% { clip-path: inset(0); }
}

@keyframes crackForm {
  0% { transform: scale(1); }
  50% { transform: scale(1.03); }
  100% { transform: scale(1); background: rgba(239, 68, 68, 0.08); }
}

.brick.cracked:nth-child(7) { animation-delay: 0s; }
.brick.cracked:nth-child(8) { animation-delay: 0.1s; }
.brick.cracked:nth-child(9) { animation-delay: 0.05s; }
.brick.cracked:nth-child(10) { animation-delay: 0.15s; }
.brick.cracked:nth-child(11) { animation-delay: 0.2s; }
.brick.cracked:nth-child(4) { animation-delay: 0.08s; }
.brick.cracked:nth-child(5) { animation-delay: 0.18s; }
.brick.cracked:nth-child(6) { animation-delay: 0.12s; }
.brick.cracked:nth-child(1) { animation-delay: 0.25s; }
.brick.cracked:nth-child(2) { animation-delay: 0.3s; }
.brick.cracked:nth-child(3) { animation-delay: 0.22s; }
.brick.cracked:nth-child(12) { animation-delay: 0.28s; }
.brick.cracked:nth-child(13) { animation-delay: 0.35s; }
.brick.cracked:nth-child(14) { animation-delay: 0.32s; }
.brick.cracked:nth-child(15) { animation-delay: 0.38s; }
.brick.cracked:nth-child(16) { animation-delay: 0.4s; }
.brick.cracked:nth-child(17) { animation-delay: 0.42s; }
.brick.cracked:nth-child(18) { animation-delay: 0.45s; }
.brick.cracked:nth-child(19) { animation-delay: 0.48s; }
.brick.cracked:nth-child(20) { animation-delay: 0.5s; }
.brick.cracked:nth-child(21) { animation-delay: 0.52s; }

/* break phase - bricks explode */
.brick.broken {
  animation: explode 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
  opacity: 0;
}

.brick:nth-child(7).broken { animation-delay: 0s; --dx: -30px; --dy: 25px; --rot: -20deg; }
.brick:nth-child(8).broken { animation-delay: 0.05s; --dx: 35px; --dy: -20px; --rot: 25deg; }
.brick:nth-child(9).broken { animation-delay: 0.1s; --dx: -20px; --dy: 30px; --rot: 15deg; }
.brick:nth-child(10).broken { animation-delay: 0.08s; --dx: 40px; --dy: 10px; --rot: -30deg; }
.brick:nth-child(11).broken { animation-delay: 0.12s; --dx: -25px; --dy: -15px; --rot: 18deg; }
.brick:nth-child(4).broken { animation-delay: 0.15s; --dx: 25px; --dy: 35px; --rot: -12deg; }
.brick:nth-child(5).broken { animation-delay: 0.18s; --dx: -35px; --dy: 5px; --rot: 22deg; }
.brick:nth-child(6).broken { animation-delay: 0.2s; --dx: 30px; --dy: -30px; --rot: -25deg; }
.brick:nth-child(1).broken { animation-delay: 0.22s; --dx: -40px; --dy: -10px; --rot: 30deg; }
.brick:nth-child(2).broken { animation-delay: 0.25s; --dx: 20px; --dy: 40px; --rot: -15deg; }
.brick:nth-child(3).broken { animation-delay: 0.28s; --dx: -15px; --dy: -35px; --rot: 20deg; }
.brick:nth-child(12).broken { animation-delay: 0.3s; --dx: 45px; --dy: 15px; --rot: -35deg; }
.brick:nth-child(13).broken { animation-delay: 0.32s; --dx: -28px; --dy: -25px; --rot: 28deg; }
.brick:nth-child(14).broken { animation-delay: 0.35s; --dx: 38px; --dy: 30px; --rot: -18deg; }
.brick:nth-child(15).broken { animation-delay: 0.38s; --dx: -32px; --dy: 20px; --rot: 15deg; }
.brick:nth-child(16).broken { animation-delay: 0.4s; --dx: 22px; --dy: -40px; --rot: -22deg; }
.brick:nth-child(17).broken { animation-delay: 0.42s; --dx: -18px; --dy: 45px; --rot: 12deg; }
.brick:nth-child(18).broken { animation-delay: 0.45s; --dx: 48px; --dy: -5px; --rot: -40deg; }
.brick:nth-child(19).broken { animation-delay: 0.48s; --dx: -42px; --dy: 12px; --rot: 35deg; }
.brick:nth-child(20).broken { animation-delay: 0.5s; --dx: 28px; --dy: -28px; --rot: -28deg; }
.brick:nth-child(21).broken { animation-delay: 0.52s; --dx: -12px; --dy: 50px; --rot: 10deg; }

@keyframes explode {
  0% { transform: translate(0, 0) rotate(0deg) scale(1); opacity: 1; background: rgba(239, 68, 68, 0.3); }
  100% { transform: translate(var(--dx), var(--dy)) rotate(var(--rot)) scale(0.3); opacity: 0; background: rgba(239, 68, 68, 0.1); }
}

.wall-glow {
  position: absolute;
  inset: -20px;
  border-radius: 8px;
  opacity: 0;
  transition: opacity 0.3s;
  pointer-events: none;
}

.wall-glow.active {
  opacity: 1;
  box-shadow: 0 0 60px rgba(239, 68, 68, 0.15), 0 0 120px rgba(239, 68, 68, 0.08);
}

.wall-label {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 1.3rem;
  color: rgba(148, 163, 184, 0.15);
  letter-spacing: 0.3em;
  font-weight: 300;
  transition: opacity 0.3s;
}

.wall-label.hidden { opacity: 0; }

/* ===== Flight Area ===== */
.flight-area {
  position: absolute;
  inset: 0;
  z-index: 3;
  pointer-events: none;
}

/* ===== Plane ===== */
.plane-wrap {
  position: absolute;
  z-index: 4;
  will-change: transform;
}

/* Phase: idle - plane waits */
.plane-wrap.idle {
  bottom: 22%;
  left: 3%;
  transform: translate(0, 0) scale(0.45) rotate(25deg);
  opacity: 0.6;
}

/* Phase: start - engine running, slight movement */
.plane-wrap.start {
  bottom: 22%;
  left: 3%;
  transform: translate(10px, -15px) scale(0.5) rotate(20deg);
  transition: all 1.2s cubic-bezier(0.4, 0, 0.2, 1);
  opacity: 1;
  animation: planeVibrate 0.08s infinite;
}

@keyframes planeVibrate {
  0%, 100% { transform: translate(10px, -15px) scale(0.5) rotate(20deg); }
  25% { transform: translate(11px, -14px) scale(0.5) rotate(20.5deg); }
  50% { transform: translate(9px, -16px) scale(0.5) rotate(19.5deg); }
  75% { transform: translate(11px, -15px) scale(0.5) rotate(20deg); }
}

/* Phase: climb - take off! */
.plane-wrap.climb {
  transform: translate(120px, -120px) scale(0.65) rotate(35deg);
  transition: all 2.2s cubic-bezier(0.22, 1, 0.36, 1);
  animation: none;
}

/* Phase: cruise - level out with bobbing */
.plane-wrap.cruise {
  transform: translate(200px, -160px) scale(0.75) rotate(5deg);
  transition: all 2.8s cubic-bezier(0.45, 0, 0.55, 1);
  animation: planeBob 1.6s ease-in-out infinite;
}

@keyframes planeBob {
  0%, 100% { transform: translate(200px, -160px) scale(0.75) rotate(5deg); }
  25% { transform: translate(205px, -168px) scale(0.75) rotate(7deg); }
  50% { transform: translate(210px, -155px) scale(0.75) rotate(3deg); }
  75% { transform: translate(195px, -165px) scale(0.75) rotate(6deg); }
}

/* Phase: approach - dive toward wall */
.plane-wrap.approach {
  transform: translate(320px, -130px) scale(0.85) rotate(-10deg);
  transition: all 2s cubic-bezier(0.36, 0, 0.66, 1);
  animation: none;
}

/* Phase: break - impact! */
.plane-wrap.break {
  transform: translate(360px, -120px) scale(0.9) rotate(15deg);
  transition: all 0.4s cubic-bezier(0.36, 0, 0.66, 1.5);
  animation: none;
}

/* Phase: glide - emerge on the other side */
.plane-wrap.glide {
  transform: translate(440px, -150px) scale(1) rotate(-8deg);
  transition: all 1.8s cubic-bezier(0.22, 1, 0.36, 1);
  animation: planeGlide 2s ease-in-out infinite;
}

@keyframes planeGlide {
  0%, 100% { transform: translate(440px, -150px) scale(1) rotate(-8deg); }
  50% { transform: translate(445px, -156px) scale(1) rotate(-5deg); }
}

/* Phase: done - victory hover */
.plane-wrap.done {
  transform: translate(460px, -160px) scale(1.05) rotate(-10deg);
  transition: all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
  animation: planeDone 2.5s ease-in-out infinite;
}

@keyframes planeDone {
  0%, 100% { transform: translate(460px, -160px) scale(1.05) rotate(-10deg); }
  50% { transform: translate(468px, -168px) scale(1.08) rotate(-7deg); }
}

.plane-body {
  width: 80px;
  height: 80px;
  filter: drop-shadow(0 2px 12px rgba(59, 130, 246, 0.25));
}

.plane-body svg { width: 100%; height: 100%; }

/* ===== Propeller ===== */
.propeller {
  position: absolute;
  top: 12px;
  left: -6px;
  width: 18px;
  height: 18px;
  opacity: 0;
  transition: opacity 0.3s;
}

.propeller.start, .propeller.climb, .propeller.cruise {
  opacity: 1;
  animation: spinProp 0.06s linear infinite;
}

.propeller.approach {
  opacity: 1;
  animation: spinProp 0.04s linear infinite;
}

.propeller.break, .propeller.glide, .propeller.done {
  opacity: 1;
  animation: spinProp 0.08s linear infinite;
}

@keyframes spinProp {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.propeller svg { width: 100%; height: 100%; }

/* ===== Exhaust ===== */
.exhaust {
  position: absolute;
  bottom: -8px;
  left: 30%;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(147, 197, 253, 0.4), transparent);
  opacity: 0;
  transition: all 0.5s;
}

.ex-1.start, .ex-1.climb, .ex-1.cruise, .ex-1.approach {
  opacity: 1;
  animation: exhaustPuff 0.6s ease-out infinite;
}

.ex-2.start, .ex-2.climb, .ex-2.cruise, .ex-2.approach {
  opacity: 1;
  animation: exhaustPuff 0.6s ease-out infinite 0.2s;
}

.ex-3.start, .ex-3.climb, .ex-3.cruise, .ex-3.approach {
  opacity: 1;
  animation: exhaustPuff 0.6s ease-out infinite 0.4s;
}

@keyframes exhaustPuff {
  0% { transform: translate(0, 0) scale(1); opacity: 0.6; }
  100% { transform: translate(-20px, 6px) scale(2.5); opacity: 0; }
}

/* ===== Contrail ===== */
.contrail-wrap {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 2;
}

.contrail-seg {
  position: absolute;
  height: 3px;
  border-radius: 2px;
  opacity: 0;
  transform-origin: left center;
}

.contrail-seg.start, .contrail-seg.climb, .contrail-seg.cruise,
.contrail-seg.approach, .contrail-seg.break,
.contrail-seg.glide, .contrail-seg.done {
  opacity: 1;
}

.seg-1 {
  bottom: 22%;
  left: 4%;
  background: linear-gradient(90deg, rgba(59, 130, 246, 0.35), rgba(59, 130, 246, 0.08));
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.seg-1.start { width: 60px; }
.seg-1.climb { width: 160px; transition-duration: 0.8s; }
.seg-1.cruise { width: 240px; }
.seg-1.approach { width: 340px; }
.seg-1.break { width: 380px; }
.seg-1.glide { width: 480px; }
.seg-1.done { width: 520px; }

.seg-2 {
  bottom: calc(22% + 6px);
  left: 15%;
  width: 0;
  background: linear-gradient(90deg, rgba(99, 102, 241, 0.25), rgba(99, 102, 241, 0.05));
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.seg-2.climb { width: 80px; }
.seg-2.cruise { width: 160px; }
.seg-2.approach { width: 240px; transition-duration: 0.8s; }
.seg-2.break { width: 280px; }
.seg-2.glide { width: 360px; }
.seg-2.done { width: 400px; }

.seg-3 {
  bottom: calc(22% - 5px);
  left: 25%;
  width: 0;
  background: linear-gradient(90deg, rgba(59, 130, 246, 0.2), rgba(59, 130, 246, 0.03));
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.seg-3.cruise { width: 80px; }
.seg-3.approach { width: 160px; transition-duration: 0.8s; }
.seg-3.break { width: 200px; }
.seg-3.glide { width: 280px; }
.seg-3.done { width: 320px; }

.seg-4 {
  bottom: calc(22% + 10px);
  left: 35%;
  width: 0;
  background: linear-gradient(90deg, rgba(139, 92, 246, 0.15), rgba(139, 92, 246, 0.03));
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.seg-4.approach { width: 60px; }
.seg-4.break { width: 100px; }
.seg-4.glide { width: 160px; }
.seg-4.done { width: 200px; }

/* ===== Debris ===== */
.debris {
  position: absolute;
  width: 6px;
  height: 6px;
  border-radius: 2px;
  opacity: 0;
  z-index: 3;
}

.debris.active {
  animation: debrisFly 1.2s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
}

.debris-1 { top: 45%; left: 52%; background: #fbbf24; --dx: 30px; --dy: -40px; --rot: 45deg; animation-delay: 0s; }
.debris-2 { top: 50%; left: 50%; background: #f87171; --dx: -35px; --dy: -25px; --rot: -30deg; animation-delay: 0.05s; }
.debris-3 { top: 48%; left: 51%; background: #60a5fa; --dx: 40px; --dy: 30px; --rot: 60deg; animation-delay: 0.1s; }
.debris-4 { top: 52%; left: 49%; background: #34d399; --dx: -25px; --dy: 35px; --rot: -45deg; animation-delay: 0.08s; }
.debris-5 { top: 46%; left: 53%; background: #a78bfa; --dx: 50px; --dy: -20px; --rot: 90deg; animation-delay: 0.12s; }
.debris-6 { top: 53%; left: 48%; background: #f472b6; --dx: -45px; --dy: 20px; --rot: -60deg; animation-delay: 0.15s; }
.debris-7 { top: 44%; left: 50%; background: #fb923c; --dx: 25px; --dy: -50px; --rot: 35deg; animation-delay: 0.18s; }
.debris-8 { top: 55%; left: 52%; background: #22d3ee; --dx: -30px; --dy: 45px; --rot: -75deg; animation-delay: 0.2s; }
.debris-9 { top: 47%; left: 47%; background: #facc15; --dx: 55px; --dy: 15px; --rot: 120deg; animation-delay: 0.22s; }
.debris-10 { top: 54%; left: 54%; background: #e879f9; --dx: -40px; --dy: -35px; --rot: -90deg; animation-delay: 0.25s; }
.debris-11 { top: 43%; left: 55%; background: #a3e635; --dx: 35px; --dy: 40px; --rot: 55deg; animation-delay: 0.28s; }
.debris-12 { top: 56%; left: 46%; background: #67e8f9; --dx: -50px; --dy: -15px; --rot: -40deg; animation-delay: 0.3s; }

@keyframes debrisFly {
  0% { transform: translate(0, 0) rotate(0deg) scale(1); opacity: 1; }
  50% { opacity: 1; }
  100% { transform: translate(var(--dx), var(--dy)) rotate(var(--rot)) scale(0.2); opacity: 0; }
}

/* ===== Sparkles ===== */
.sparkle {
  position: absolute;
  width: 5px;
  height: 5px;
  background: radial-gradient(circle, rgba(147, 197, 253, 0.8), transparent);
  border-radius: 50%;
  opacity: 0;
  z-index: 3;
}

.sparkle.active {
  animation: sparkleGlow 2s ease-in-out infinite;
}

.sparkle-1 { top: 42%; right: 18%; animation-delay: 0s; }
.sparkle-2 { top: 38%; right: 22%; animation-delay: 0.3s; }
.sparkle-3 { top: 48%; right: 15%; animation-delay: 0.6s; }
.sparkle-4 { top: 35%; right: 25%; animation-delay: 0.9s; }
.sparkle-5 { top: 53%; right: 12%; animation-delay: 0.15s; }
.sparkle-6 { top: 45%; right: 28%; animation-delay: 0.45s; }
.sparkle-7 { top: 40%; right: 10%; animation-delay: 0.75s; }
.sparkle-8 { top: 55%; right: 20%; animation-delay: 0.2s; }
.sparkle-9 { top: 32%; right: 16%; animation-delay: 0.5s; }
.sparkle-10 { top: 50%; right: 30%; animation-delay: 0.8s; }

@keyframes sparkleGlow {
  0%, 100% { transform: scale(0.5); opacity: 0; }
  50% { transform: scale(1.5); opacity: 1; }
}

/* ===== Logo Section ===== */
.logo-section {
  position: absolute;
  bottom: 8%;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  opacity: 0;
  transition: all 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 5;
  pointer-events: none;
}

.logo-section.visible {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}

.logo-badge {
  width: 48px;
  height: 48px;
  margin: 0 auto 0.75rem;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.25);
}

.logo-badge svg {
  width: 26px;
  height: 26px;
}

h1 {
  color: #1e293b;
  font-size: 1.7rem;
  font-weight: 700;
  margin: 0 0 0.3rem;
  letter-spacing: -0.02em;
}

.tagline {
  color: #64748b;
  font-size: 0.85rem;
  margin: 0 0 1rem;
  letter-spacing: 0.12em;
}

.enter-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  opacity: 0;
  transition: opacity 0.6s ease;
}

.enter-hint.visible {
  opacity: 1;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: #3b82f6;
  border-radius: 50%;
  animation: pulseDot 1.5s ease-in-out infinite;
}

@keyframes pulseDot {
  0%, 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4); transform: scale(1); }
  50% { box-shadow: 0 0 0 10px rgba(59, 130, 246, 0); transform: scale(1.2); }
}

.hint-text {
  color: #94a3b8;
  font-size: 0.8rem;
}
</style>
