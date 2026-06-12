<template>
  <div class="layout-root" @mousemove="handleMouseMove">
    <!-- Dynamic background based on current page -->
    <div class="bg-layer" :style="{ background: pageBackground }"></div>

    <!-- Mouse glow that follows cursor -->
    <div class="bg-layer bg-mouse-glow" :style="{ background: mouseGlowGradient }"></div>

    <!-- Parallax gradient layers -->
    <div class="bg-layer bg-gradient-glow" :style="{ transform: layerGlow, background: pageGlow }"></div>

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
            <header class="h-16 backdrop-blur-xl flex items-center justify-between px-8 sticky top-0 z-20" :style="headerStyle">
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

// Page-specific background colors
const pageBackgrounds = {
  '/upload': 'linear-gradient(135deg, #f5f0e8 0%, #e8e0d0 30%, #d2d3db 60%, #c8c0b0 100%)',
  '/dashboard': 'linear-gradient(135deg, #e8e4dc 0%, #d8d4cc 30%, #d2d3db 60%, #c8c4bc 100%)',
  '/proposal': 'linear-gradient(135deg, #f0ece4 0%, #e0dcd4 30%, #d2d3db 60%, #ccc8c0 100%)',
}

const pageGlows = {
  '/upload': 'radial-gradient(circle at 30% 50%, rgba(200, 169, 110, 0.08) 0%, transparent 50%)',
  '/dashboard': 'radial-gradient(circle at 50% 30%, rgba(200, 169, 110, 0.06) 0%, transparent 50%)',
  '/proposal': 'radial-gradient(circle at 70% 50%, rgba(200, 169, 110, 0.07) 0%, transparent 50%)',
}

const headerStyles = {
  '/upload': 'background: rgba(245, 240, 232, 0.9); border-bottom: 1px solid rgba(200, 169, 110, 0.15);',
  '/dashboard': 'background: rgba(232, 228, 220, 0.9); border-bottom: 1px solid rgba(200, 169, 110, 0.15);',
  '/proposal': 'background: rgba(240, 236, 228, 0.9); border-bottom: 1px solid rgba(200, 169, 110, 0.15);',
}

const pageBackground = computed(() => pageBackgrounds[route.path] || pageBackgrounds['/upload'])
const pageGlow = computed(() => pageGlows[route.path] || pageGlows['/upload'])
const headerStyle = computed(() => headerStyles[route.path] || headerStyles['/upload'])

// Mouse state
let mouseTargetX = 0
let mouseTargetY = 0
let mouseCurrentX = 0
let mouseCurrentY = 0
let rafId = null

const layerFar = ref('')
const layerMid = ref('')
const layerGlow = ref('')

// 3D tilt transform — more pronounced for visible effect
const tiltTransform = computed(() => {
  const rotateX = mouseCurrentY * -8
  const rotateY = mouseCurrentX * 8
  return `perspective(800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.01, 1.01, 1.01)`
})

// Mouse glow gradient
const mouseGlowGradient = computed(() => {
  const x = (mouseCurrentX + 1) * 50
  const y = (mouseCurrentY + 1) * 50
  return `radial-gradient(circle at ${x}% ${y}%, rgba(200, 169, 110, 0.1) 0%, transparent 50%)`
})

// Shine highlight gradient
const shineGradient = computed(() => {
  const x = (mouseCurrentX + 1) * 50
  const y = (mouseCurrentY + 1) * 50
  return `radial-gradient(circle at ${x}% ${y}%, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.03) 30%, transparent 60%)`
})

function handleMouseMove(e) {
  mouseTargetX = (e.clientX / window.innerWidth - 0.5) * 2
  mouseTargetY = (e.clientY / window.innerHeight - 0.5) * 2
}

function animate() {
  // Faster interpolation for more responsive tilt
  mouseCurrentX += (mouseTargetX - mouseCurrentX) * 0.12
  mouseCurrentY += (mouseTargetY - mouseCurrentY) * 0.12

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
.layout-root {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
}

.bg-layer {
  position: fixed;
  inset: 0;
  pointer-events: none;
  transition: background 0.5s ease;
}

.bg-mouse-glow {
  z-index: 1;
  transition: background 0.1s linear;
}

.bg-gradient-glow {
  z-index: 2;
  transition: background 0.3s ease, transform 0.1s linear;
}

.shine-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 100;
  opacity: 0.8;
  transition: background 0.1s linear;
  mix-blend-mode: overlay;
}

.tilt-perspective {
  position: relative;
  z-index: 10;
  perspective: 1200px;
  min-height: 100vh;
}

.tilt-surface {
  min-height: 100vh;
  transition: transform 0.05s linear;
  transform-style: preserve-3d;
  will-change: transform;
  position: relative;
}

.layout-content {
  min-height: 100vh;
  position: relative;
  z-index: 1;
}
</style>
