<template>
  <div class="layout-root" @mousemove="handleMouseMove">
    <!-- Background base -->
    <div class="bg-layer bg-base"></div>

    <!-- Mouse glow that follows cursor -->
    <div class="bg-layer bg-mouse-glow" :style="{ background: mouseGlowGradient }"></div>

    <!-- Parallax gradient layers -->
    <div class="bg-layer bg-gradient-glow" :style="{ transform: layerGlow }"></div>
    <div class="bg-layer bg-noise" :style="{ transform: layerFar }"></div>

    <!-- 3D Tilt Container -->
    <div class="tilt-perspective">
      <div class="tilt-surface" :style="{ transform: tiltTransform }">
        <!-- Shine highlight overlay -->
        <div class="shine-overlay" :style="{ background: shineGradient }"></div>

        <!-- Content -->
        <div class="layout-content">
          <AppSidebar />
          <main class="ml-64 min-h-screen">
            <!-- Top bar -->
            <header class="h-16 backdrop-blur-xl flex items-center justify-between px-8 sticky top-0 z-20" style="background: rgba(210, 211, 219, 0.9); border-bottom: 1px solid rgba(200, 169, 110, 0.15);">
              <div>
                <h2 class="text-lg font-bold tracking-tight" style="color: #000000;">{{ pageTitle }}</h2>
              </div>
              <div></div>
            </header>

            <!-- Page content -->
            <div class="p-8 animate-fade-in">
              <slot />
            </div>
          </main>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from './AppSidebar.vue'

const route = useRoute()
const pageTitle = computed(() => route.meta?.title || 'BidEngine')

// Mouse state
let mouseTargetX = 0
let mouseTargetY = 0
let mouseCurrentX = 0
let mouseCurrentY = 0
let rafId = null

const layerFar = ref('')
const layerMid = ref('')
const layerGlow = ref('')

// 3D tilt transform
const tiltTransform = computed(() => {
  const rotateX = mouseCurrentY * -4
  const rotateY = mouseCurrentX * 4
  return `perspective(1200px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`
})

// Mouse glow gradient
const mouseGlowGradient = computed(() => {
  const x = (mouseCurrentX + 1) * 50
  const y = (mouseCurrentY + 1) * 50
  return `radial-gradient(circle at ${x}% ${y}%, rgba(200, 169, 110, 0.12) 0%, transparent 50%)`
})

// Shine highlight gradient
const shineGradient = computed(() => {
  const x = (mouseCurrentX + 1) * 50
  const y = (mouseCurrentY + 1) * 50
  return `radial-gradient(circle at ${x}% ${y}%, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0.05) 30%, transparent 60%)`
})

function handleMouseMove(e) {
  mouseTargetX = (e.clientX / window.innerWidth - 0.5) * 2
  mouseTargetY = (e.clientY / window.innerHeight - 0.5) * 2
}

function animate() {
  mouseCurrentX += (mouseTargetX - mouseCurrentX) * 0.06
  mouseCurrentY += (mouseTargetY - mouseCurrentY) * 0.06

  layerFar.value = `translate(${mouseCurrentX * 5}px, ${mouseCurrentY * 5}px)`
  layerMid.value = `translate(${mouseCurrentX * 2}px, ${mouseCurrentY * 2}px)`
  layerGlow.value = `translate(${mouseCurrentX * 20}px, ${mouseCurrentY * 20}px)`

  rafId = requestAnimationFrame(animate)
}

onMounted(() => {
  animate()
})

onUnmounted(() => {
  if (rafId) cancelAnimationFrame(rafId)
})
</script>

<style scoped>
/* Root layout */
.layout-root {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: #d2d3db;
}

/* Background layers */
.bg-layer {
  position: fixed;
  inset: 0;
  pointer-events: none;
}

/* Base background */
.bg-base {
  background:
    radial-gradient(ellipse at 30% 40%, rgba(200, 169, 110, 0.1) 0%, transparent 60%),
    radial-gradient(ellipse at 70% 60%, rgba(200, 169, 110, 0.07) 0%, transparent 50%),
    linear-gradient(180deg, #d2d3db 0%, #c8c9d2 50%, #d2d3db 100%);
}

/* Mouse glow — follows cursor */
.bg-mouse-glow {
  z-index: 1;
  transition: background 0.1s linear;
}

/* Glow layer — moves with parallax */
.bg-gradient-glow {
  background:
    radial-gradient(circle at 30% 40%, rgba(200, 169, 110, 0.06) 0%, transparent 50%),
    radial-gradient(circle at 70% 60%, rgba(200, 169, 110, 0.04) 0%, transparent 40%);
  transition: transform 0.1s linear;
  z-index: 2;
}

/* Noise texture */
.bg-noise {
  opacity: 0.3;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");
  transition: transform 0.15s linear;
  z-index: 3;
}

/* 3D Tilt Container */
.tilt-perspective {
  position: relative;
  z-index: 10;
  perspective: 1200px;
  min-height: 100vh;
}

.tilt-surface {
  min-height: 100vh;
  transition: transform 0.08s linear;
  transform-style: preserve-3d;
  will-change: transform;
  position: relative;
}

/* Shine highlight overlay */
.shine-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 100;
  opacity: 0.8;
  transition: background 0.1s linear;
  mix-blend-mode: overlay;
}

/* Content layer */
.layout-content {
  min-height: 100vh;
  background: rgba(210, 211, 219, 0.4);
  backdrop-filter: blur(1px);
  -webkit-backdrop-filter: blur(1px);
  position: relative;
  z-index: 1;
}
</style>
