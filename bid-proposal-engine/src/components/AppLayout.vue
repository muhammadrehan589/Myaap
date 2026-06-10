<template>
  <div class="min-h-screen bg-gray-50">
    <AppSidebar />
    <main class="ml-64 min-h-screen">
      <!-- Top bar -->
      <header class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-8 sticky top-0 z-20">
        <div>
          <h2 class="text-lg font-semibold text-gray-900">{{ pageTitle }}</h2>
        </div>
        <div class="flex items-center gap-4">
          <button class="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </button>
          <div class="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
            <span class="text-xs font-semibold text-white">JD</span>
          </div>
        </div>
      </header>

      <!-- Page content -->
      <div class="p-8">
        <slot />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from './AppSidebar.vue'

const route = useRoute()
const pageTitle = computed(() => route.meta?.title || 'BidEngine')
</script>
