import { ref, onMounted, onUnmounted } from 'vue'

/**
 * Mouse parallax composable — creates subtle depth movement on mouse hover.
 * Returns reactive x/y offsets that shift elements based on cursor position.
 */
export function useMouseParallax(sensitivity = 0.02) {
  const mouseX = ref(0)
  const mouseY = ref(0)
  const targetX = ref(0)
  const targetY = ref(0)
  let animationId = null

  function handleMouseMove(e) {
    // Normalize mouse position to -1 to 1 range
    targetX.value = (e.clientX / window.innerWidth - 0.5) * 2
    targetY.value = (e.clientY / window.innerHeight - 0.5) * 2
  }

  function animate() {
    // Smooth interpolation (lerp) for fluid movement
    mouseX.value += (targetX.value - mouseX.value) * 0.08
    mouseY.value += (targetY.value - mouseY.value) * 0.08
    animationId = requestAnimationFrame(animate)
  }

  onMounted(() => {
    window.addEventListener('mousemove', handleMouseMove)
    animate()
  })

  onUnmounted(() => {
    window.removeEventListener('mousemove', handleMouseMove)
    if (animationId) cancelAnimationFrame(animationId)
  })

  return {
    mouseX,
    mouseY,
    // Pre-computed transform strings for different layers
    layerFar: computed(() => `translate(${mouseX.value * 8 * sensitivity}px, ${mouseY.value * 8 * sensitivity}px)`),
    layerMid: computed(() => `translate(${mouseX.value * 15 * sensitivity}px, ${mouseY.value * 15 * sensitivity}px)`),
    layerNear: computed(() => `translate(${mouseX.value * 25 * sensitivity}px, ${mouseY.value * 25 * sensitivity}px)`),
    layerGlow: computed(() => `translate(${mouseX.value * 30 * sensitivity}px, ${mouseY.value * 30 * sensitivity}px)`),
  }
}
