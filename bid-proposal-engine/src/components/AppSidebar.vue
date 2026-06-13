<template>
  <aside class="fixed inset-y-0 left-0 w-64 bg-white border-r border-gray-200 flex flex-col z-30">
    <!-- Logo -->
    <div class="h-16 flex items-center px-6 border-b border-gray-200">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
          <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <div>
          <h1 class="text-sm font-bold text-gray-900 leading-tight">BidEngine</h1>
          <p class="text-[10px] text-gray-500 leading-tight">Proposal AI</p>
        </div>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
      <router-link
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150"
        :class="isActive(item.to)
          ? 'bg-primary-50 text-primary-700'
          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'"
      >
        <component :is="item.icon" class="w-5 h-5 flex-shrink-0" />
        {{ item.label }}
      </router-link>
    </nav>

    <!-- Footer -->
    <div class="p-4 border-t border-gray-200">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
          <span class="text-xs font-semibold text-gray-600">JD</span>
        </div>
        <div class="min-w-0">
          <p class="text-sm font-medium text-gray-900 truncate">John Doe</p>
          <p class="text-xs text-gray-500 truncate">Admin</p>
        </div>
      </div>
    </div>
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
