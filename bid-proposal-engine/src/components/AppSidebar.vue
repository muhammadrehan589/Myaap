<template>
  <aside class="sidebar-root">
    <!-- Logo -->
    <div class="sidebar-header">
      <div class="flex items-center gap-3">
        <div class="sidebar-logo">
          <svg class="w-5 h-5 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <div>
          <h1 class="text-sm font-bold leading-tight tracking-tight" style="color: #000000;">BidEngine</h1>
          <p class="text-[10px] leading-tight font-medium" style="color: #b8944d;">Proposal AI</p>
        </div>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="sidebar-nav">
      <router-link
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="sidebar-link"
        :class="isActive(item.to) ? 'sidebar-link-active' : 'sidebar-link-inactive'"
      >
        <component :is="item.icon" class="w-5 h-5 flex-shrink-0 transition-colors duration-200" />
        {{ item.label }}
      </router-link>
    </nav>

  </aside>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { h } from 'vue'

const route = useRoute()

const isActive = (path) => route.path === path

const UploadIcon = {
  render() {
    return h('svg', { class: 'w-5 h-5', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor', 'stroke-width': '2' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12' })
    ])
  }
}

const DashboardIcon = {
  render() {
    return h('svg', { class: 'w-5 h-5', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor', 'stroke-width': '2' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z' })
    ])
  }
}

const ProposalIcon = {
  render() {
    return h('svg', { class: 'w-5 h-5', fill: 'none', viewBox: '0 0 24 24', stroke: 'currentColor', 'stroke-width': '2' }, [
      h('path', { 'stroke-linecap': 'round', 'stroke-linejoin': 'round', d: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z' })
    ])
  }
}

const navItems = [
  { to: '/upload', label: 'Upload RFP', icon: UploadIcon },
  { to: '/dashboard', label: 'Dashboard', icon: DashboardIcon },
  { to: '/proposal', label: 'Proposal', icon: ProposalIcon },
]
</script>

<style scoped>
.sidebar-root {
  position: fixed;
  top: 0;
  bottom: 0;
  left: 0;
  width: 16rem;
  display: flex;
  flex-direction: column;
  z-index: 30;
  background: rgba(210, 211, 219, 0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid rgba(200, 169, 110, 0.15);
}

.sidebar-header {
  height: 4rem;
  display: flex;
  align-items: center;
  padding: 0 1.5rem;
  border-bottom: 1px solid rgba(200, 169, 110, 0.08);
}

.sidebar-logo {
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #c8a96e, #d4b87a);
  box-shadow: 0 0 15px rgba(200, 169, 110, 0.3);
}

.sidebar-nav {
  flex: 1;
  padding: 1rem 0.75rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  border-radius: 0.75rem;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s ease-out;
  border: 1px solid transparent;
  text-decoration: none;
}

.sidebar-link-active {
  background: rgba(200, 169, 110, 0.2);
  border-color: rgba(200, 169, 110, 0.3);
  color: #b8944d;
  box-shadow: 0 0 10px rgba(200, 169, 110, 0.15);
}

.sidebar-link-inactive {
  color: #000000;
}

.sidebar-link-inactive:hover {
  background: rgba(200, 169, 110, 0.1);
  color: #000000;
}
</style>
