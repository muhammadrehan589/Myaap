<template>
  <div class="splash-screen" @click="skipToUpload" @mousemove="handleMouseMove">
    <!-- Background -->
    <div class="absolute inset-0" style="background: #d2d3db;"></div>

    <!-- Parallax gradient layers -->
    <div class="absolute inset-0 splash-gradient-base" :style="{ transform: layerFar }"></div>
    <div class="absolute inset-0 splash-gradient-glow" :style="{ transform: layerGlow }"></div>

    <!-- Atmospheric radial glows -->
    <div class="absolute inset-0">
      <div class="atmosphere-glow glow-1" :class="{ 'active': showTitle }" :style="{ transform: layerMid }"></div>
      <div class="atmosphere-glow glow-2" :class="{ 'active': showTitle }" :style="{ transform: layerNear }"></div>
    </div>

    <!-- Floating particles -->
    <div class="absolute inset-0 overflow-hidden" :style="{ transform: layerFar }">
      <div class="particle" v-for="n in 20" :key="n"
        :style="{
          left: (n * 5) + '%',
          animationDelay: (n * 0.3) + 's',
          animationDuration: (4 + (n % 3)) + 's',
          opacity: 0.1 + (n % 5) * 0.05
        }"></div>
    </div>

    <!-- 3D Tilt Hero Container -->
    <div class="hero-perspective">
      <div class="hero-tilt" :style="{ transform: tiltTransform }">
        <!-- Glowing edge highlight that follows mouse -->
        <div class="hero-glow-edge" :style="{ background: glowGradient }"></div>

        <!-- Hero card surface -->
        <div class="hero-surface">
          <!-- Logo icon with golden glow -->
          <div class="logo-container" :class="{ 'active': showIcon }">
            <div class="logo-ring">
              <div class="logo-inner">
                <svg class="w-12 h-12 text-black-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
            </div>
          </div>

          <!-- Main title — cinematic reveal -->
          <div class="title-container" :class="{ 'active': showTitle }">
            <h1 class="main-title">
              <span class="title-word" :class="{ 'active': wordIndex >= 0 }">Bid</span>
              <span class="title-word gold" :class="{ 'active': wordIndex >= 1 }">Engine</span>
            </h1>

            <!-- Ornamental divider -->
            <div class="divider-container" :class="{ 'active': showDivider }">
              <div class="divider-line left"></div>
              <div class="divider-diamond"></div>
              <div class="divider-line right"></div>
            </div>

            <h2 class="sub-title">
              <span class="title-word" :class="{ 'active': wordIndex >= 2 }">Proposal</span>
              <span class="title-word accent" :class="{ 'active': wordIndex >= 3 }">AI</span>
            </h2>
          </div>

          <!-- Tagline -->
          <div class="tagline-container" :class="{ 'active': showTagline }">
            <p class="tagline">Intelligent RFP Analysis & Proposal Generation</p>
          </div>

          <!-- Loading indicator -->
          <div class="loading-container" :class="{ 'active': showLoading }">
            <div class="loading-bar">
              <div class="loading-fill" :style="{ width: loadingProgress + '%' }"></div>
            </div>
            <p class="loading-text">Initializing AI Engine...</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Skip hint -->
    <div class="skip-hint" :class="{ 'active': showLoading }">
      <p>Click anywhere to enter</p>
    </div>

    <!-- Corner ornaments -->
    <div class="corner-ornament top-left" :class="{ 'active': showTitle }"></div>
    <div class="corner-ornament top-right" :class="{ 'active': showTitle }"></div>
    <div class="corner-ornament bottom-left" :class="{ 'active': showTitle }"></div>
    <div class="corner-ornament bottom-right" :class="{ 'active': showTitle }"></div>

    <!-- Bottom edge glow -->
    <div class="bottom-edge-glow" :class="{ 'active': showTitle }"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const showIcon = ref(false)
const showTitle = ref(false)
const wordIndex = ref(-1)
const showDivider = ref(false)
const showTagline = ref(false)
const showLoading = ref(false)
const loadingProgress = ref(0)

// Mouse state for 3D tilt
let mouseTargetX = 0
let mouseTargetY = 0
let mouseCurrentX = 0
let mouseCurrentY = 0
let rafId = null

// Parallax layers
const layerFar = ref('')
const layerMid = ref('')
const layerNear = ref('')
const layerGlow = ref('')

// 3D tilt transform
const tiltTransform = computed(() => {
  const rotateX = mouseCurrentY * -8  // tilt up/down
  const rotateY = mouseCurrentX * 8   // tilt left/right
  return `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`
})

// Glow gradient that follows mouse
const glowGradient = computed(() => {
  const x = (mouseCurrentX + 1) * 50  // 0-100%
  const y = (mouseCurrentY + 1) * 50  // 0-100%
  return `radial-gradient(circle at ${x}% ${y}%, rgba(226, 165, 54, 0.15) 0%, transparent 50%)`
})

function handleMouseMove(e) {
  mouseTargetX = (e.clientX / window.innerWidth - 0.5) * 2
  mouseTargetY = (e.clientY / window.innerHeight - 0.5) * 2
}

function animateParallax() {
  // Smooth interpolation for fluid motion
  mouseCurrentX += (mouseTargetX - mouseCurrentX) * 0.06
  mouseCurrentY += (mouseTargetY - mouseCurrentY) * 0.06

  // Update parallax layers
  layerFar.value = `translate(${mouseCurrentX * 5}px, ${mouseCurrentY * 5}px)`
  layerMid.value = `translate(${mouseCurrentX * 12}px, ${mouseCurrentY * 12}px)`
  layerNear.value = `translate(${mouseCurrentX * 20}px, ${mouseCurrentY * 20}px)`
  layerGlow.value = `translate(${mouseCurrentX * 25}px, ${mouseCurrentY * 25}px)`

  rafId = requestAnimationFrame(animateParallax)
}

let timers = []

function scheduleTimer(fn, delay) {
  const t = setTimeout(fn, delay)
  timers.push(t)
  return t
}

function startAnimation() {
  // Phase 1: Logo appears with golden glow
  scheduleTimer(() => { showIcon.value = true }, 300)

  // Phase 2: Title words appear one by one with blur reveal
  scheduleTimer(() => { showTitle.value = true }, 800)
  scheduleTimer(() => { wordIndex.value = 0 }, 900)   // Bid
  scheduleTimer(() => { wordIndex.value = 1 }, 1200)   // Engine
  scheduleTimer(() => { showDivider.value = true }, 1500)
  scheduleTimer(() => { wordIndex.value = 2 }, 1800)   // Proposal
  scheduleTimer(() => { wordIndex.value = 3 }, 2100)   // AI

  // Phase 3: Tagline
  scheduleTimer(() => { showTagline.value = true }, 2500)

  // Phase 4: Loading bar
  scheduleTimer(() => { showLoading.value = true }, 2900)
  scheduleTimer(() => { loadingProgress.value = 25 }, 3100)
  scheduleTimer(() => { loadingProgress.value = 50 }, 3500)
  scheduleTimer(() => { loadingProgress.value = 75 }, 3900)
  scheduleTimer(() => { loadingProgress.value = 100 }, 4300)

  // Navigate to upload
  scheduleTimer(() => { navigateToUpload() }, 4800)
}

function navigateToUpload() {
  router.push('/upload')
}

function skipToUpload() {
  navigateToUpload()
}

onMounted(() => {
  startAnimation()
  animateParallax()
})

onUnmounted(() => {
  timers.forEach(clearTimeout)
  if (rafId) cancelAnimationFrame(rafId)
})
</script>

<style scoped>
.splash-screen {
  position: fixed;
  inset: 0;
  z-index: 100;
  cursor: pointer;
  overflow: hidden;
  background: #ffffff;
}

/* Parallax gradient layers */
.splash-gradient-base {
  background:
    radial-gradient(ellipse at 25% 45%, rgba(200, 169, 110, 0.08) 0%, transparent 55%),
    radial-gradient(ellipse at 75% 25%, rgba(200, 169, 110, 0.05) 0%, transparent 45%),
    linear-gradient(180deg, #ffffff 0%, #fafafa 40%, #ffffff 100%);
  transition: transform 0.15s linear;
}

.splash-gradient-glow {
  background:
    radial-gradient(circle at 35% 45%, rgba(200, 169, 110, 0.06) 0%, transparent 45%),
    radial-gradient(circle at 65% 55%, rgba(200, 169, 110, 0.04) 0%, transparent 35%);
  transition: transform 0.1s linear;
}

/* Atmospheric glows */
.atmosphere-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0;
  transition: opacity 2s ease;
}

.atmosphere-glow.active {
  opacity: 1;
}

.glow-1 {
  width: 600px;
  height: 600px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, rgba(200, 169, 110, 0.15) 0%, rgba(200, 169, 110, 0.06) 40%, transparent 70%);
  animation: orbPulse 6s ease-in-out infinite;
}

.glow-2 {
  width: 300px;
  height: 300px;
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, rgba(200, 169, 110, 0.1) 0%, transparent 60%);
  animation: orbPulse 4s ease-in-out infinite 1s;
}

@keyframes orbPulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.6; }
  50% { transform: translate(-50%, -50%) scale(1.15); opacity: 1; }
}

/* Floating particles */
.particle {
  position: absolute;
  width: 2px;
  height: 2px;
  background: rgba(200, 169, 110, 0.4);
  border-radius: 50%;
  top: -10px;
  animation: particleFall linear infinite;
}

@keyframes particleFall {
  0% { transform: translateY(-10px); opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { transform: translateY(100vh); opacity: 0; }
}

/* 3D Tilt Hero Container */
.hero-perspective {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  perspective: 1200px;
  z-index: 10;
}

.hero-tilt {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.08s linear;
  transform-style: preserve-3d;
  will-change: transform;
}

/* Glowing edge that follows mouse */
.hero-glow-edge {
  position: absolute;
  inset: 0;
  z-index: 0;
  opacity: 0.6;
  transition: background 0.1s linear;
}

/* Hero card surface — full screen with centered content */
.hero-surface {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  background: transparent;
}

/* Logo */
.logo-container {
  opacity: 0;
  transform: translateY(20px) scale(0.8);
  transition: all 1s cubic-bezier(0.16, 1, 0.3, 1);
  margin-bottom: 2.5rem;
}

.logo-container.active {
  opacity: 1;
  transform: translateY(0) scale(1);
}

.logo-ring {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  border: 1px solid rgba(200, 169, 110, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  position: relative;
  animation: ringGlow 3s ease-in-out infinite;
}

.logo-ring::before {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 1px solid rgba(200, 169, 110, 0.1);
}

.logo-inner {
  width: 72px;
  height: 72px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(200, 169, 110, 0.2), rgba(200, 169, 110, 0.1));
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(200, 169, 110, 0.25);
  box-shadow: 0 0 30px rgba(200, 169, 110, 0.2);
}

@keyframes ringGlow {
  0%, 100% { box-shadow: 0 0 20px rgba(200, 169, 110, 0.1); }
  50% { box-shadow: 0 0 40px rgba(200, 169, 110, 0.25); }
}

/* Title */
.title-container {
  margin-bottom: 1.5rem;
}

.main-title {
  font-size: 5rem;
  font-weight: 900;
  letter-spacing: -0.03em;
  line-height: 1;
  margin-bottom: 0.75rem;
}

.sub-title {
  font-size: 2.5rem;
  font-weight: 300;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  line-height: 1;
}

.title-word {
  display: inline-block;
  opacity: 0;
  transform: translateY(30px);
  filter: blur(8px);
  transition: all 0.8s cubic-bezier(0.16, 1, 0.3, 1);
  color: #000000;
  font-weight: 900;
}

.title-word.active {
  opacity: 1;
  transform: translateY(0);
  filter: blur(0);
}

.title-word.gold {
  color: #c8a96e;
  font-weight: 900;
  text-shadow: 0 0 40px rgba(200, 169, 110, 0.5);
}

.title-word.accent {
  background: linear-gradient(135deg, #c8a96e, #e5d1a3);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 700;
  filter: blur(0);
  text-shadow: none;
}

/* Ornamental divider */
.divider-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin: 0.75rem 0;
  opacity: 0;
  transition: opacity 0.6s ease;
}

.divider-container.active {
  opacity: 1;
}

.divider-line {
  width: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #c8a96e);
  transition: width 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}

.divider-line.left {
  background: linear-gradient(90deg, transparent, #c8a96e);
}

.divider-line.right {
  background: linear-gradient(90deg, #c8a96e, transparent);
}

.divider-container.active .divider-line {
  width: 80px;
}

.divider-diamond {
  width: 10px;
  height: 10px;
  background: #c8a96e;
  transform: rotate(45deg);
  box-shadow: 0 0 15px rgba(200, 169, 110, 0.6);
}

/* Tagline */
.tagline-container {
  opacity: 0;
  transform: translateY(15px);
  transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
  margin-bottom: 2.5rem;
}

.tagline-container.active {
  opacity: 1;
  transform: translateY(0);
}

.tagline {
  font-size: 1.125rem;
  color: #b8944d;
  letter-spacing: 0.08em;
  font-weight: 600;
}

/* Loading */
.loading-container {
  opacity: 0;
  transform: translateY(10px);
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  width: 240px;
  margin: 0 auto;
}

.loading-container.active {
  opacity: 1;
  transform: translateY(0);
}

.loading-bar {
  width: 100%;
  height: 2px;
  background: rgba(200, 169, 110, 0.1);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.75rem;
}

.loading-fill {
  height: 100%;
  background: linear-gradient(90deg, #c8a96e, #d4b87a);
  border-radius: 4px;
  transition: width 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 0 15px rgba(200, 169, 110, 0.5);
}

.loading-text {
  font-size: 0.75rem;
  color: #b8944d;
  text-align: center;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-weight: 600;
}

/* Skip hint */
.skip-hint {
  position: absolute;
  bottom: 2.5rem;
  left: 50%;
  transform: translateX(-50%);
  opacity: 0;
  transition: opacity 0.4s ease;
  z-index: 20;
}

.skip-hint.active {
  opacity: 1;
  animation: hintPulse 2.5s ease-in-out infinite;
}

.skip-hint p {
  font-size: 0.75rem;
  color: #b8944d;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-weight: 600;
}

@keyframes hintPulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.7; }
}

/* Corner ornaments */
.corner-ornament {
  position: absolute;
  width: 50px;
  height: 50px;
  opacity: 0;
  transition: opacity 0.8s ease;
  z-index: 20;
}

.corner-ornament.active {
  opacity: 1;
}

.corner-ornament::before,
.corner-ornament::after {
  content: '';
  position: absolute;
  background: rgba(200, 169, 110, 0.15);
}

.corner-ornament.top-left {
  top: 2rem;
  left: 2rem;
}
.corner-ornament.top-left::before {
  top: 0;
  left: 0;
  width: 24px;
  height: 1px;
}
.corner-ornament.top-left::after {
  top: 0;
  left: 0;
  width: 1px;
  height: 24px;
}

.corner-ornament.top-right {
  top: 2rem;
  right: 2rem;
}
.corner-ornament.top-right::before {
  top: 0;
  right: 0;
  width: 24px;
  height: 1px;
}
.corner-ornament.top-right::after {
  top: 0;
  right: 0;
  width: 1px;
  height: 24px;
}

.corner-ornament.bottom-left {
  bottom: 2rem;
  left: 2rem;
}
.corner-ornament.bottom-left::before {
  bottom: 0;
  left: 0;
  width: 24px;
  height: 1px;
}
.corner-ornament.bottom-left::after {
  bottom: 0;
  left: 0;
  width: 1px;
  height: 24px;
}

.corner-ornament.bottom-right {
  bottom: 2rem;
  right: 2rem;
}
.corner-ornament.bottom-right::before {
  bottom: 0;
  right: 0;
  width: 24px;
  height: 1px;
}
.corner-ornament.bottom-right::after {
  bottom: 0;
  right: 0;
  width: 1px;
  height: 24px;
}

/* Bottom edge glow */
.bottom-edge-glow {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(200, 169, 110, 0.3), transparent);
  opacity: 0;
  transition: opacity 0.8s ease;
  z-index: 20;
}

.bottom-edge-glow.active {
  opacity: 1;
}
</style>
