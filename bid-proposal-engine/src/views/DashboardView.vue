<template>
  <AppLayout>
    <div v-if="!state.rfpData" class="text-center py-20 animate-fade-in">
      <div class="w-20 h-20 bg-surface-800/60 rounded-2xl flex items-center justify-center mx-auto mb-6 border border-white/[0.06]">
        <svg class="w-10 h-10 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5m6 4.125l2.25 2.25m0 0l2.25 2.25M12 13.875l2.25-2.25M12 13.875l-2.25 2.25M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
        </svg>
      </div>
      <h3 class="text-xl font-bold text-black mb-2">No RFP Uploaded</h3>
      <p class="text-black mb-6">Upload an RFP document to view the analysis dashboard.</p>
      <router-link to="/upload" class="btn-primary">Upload RFP</router-link>
    </div>

    <div v-else class="space-y-6">
      <!-- RFP Summary -->
      <div class="card animate-slide-up">
        <div class="flex items-start justify-between mb-4">
          <div>
            <h3 class="text-lg font-bold text-black">RFP Summary</h3>
            <p class="text-sm text-black mt-1">{{ state.rfpData.rfpNumber }}</p>
          </div>
          <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-glow-warning/10 text-glow-warning border border-glow-warning/20">
            {{ state.rfpData.status }}
          </span>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div class="p-3 rounded-xl bg-surface-800/40 border border-white/[0.04]">
            <p class="text-xs text-black uppercase tracking-wider font-medium">Project Name</p>
            <p class="mt-1 font-bold text-black">{{ state.rfpData.name }}</p>
          </div>
          <div class="p-3 rounded-xl bg-surface-800/40 border border-white/[0.04]">
            <p class="text-xs text-black uppercase tracking-wider font-medium">Agency</p>
            <p class="mt-1 font-bold text-black">{{ state.rfpData.agency }}</p>
          </div>
          <div class="p-3 rounded-xl bg-surface-800/40 border border-white/[0.04]">
            <p class="text-xs text-black uppercase tracking-wider font-medium">Deadline</p>
            <p class="mt-1 font-bold text-black">{{ state.rfpData.deadline }}</p>
          </div>
          <div class="p-3 rounded-xl bg-surface-800/40 border border-white/[0.04]">
            <p class="text-xs text-black uppercase tracking-wider font-medium">Budget</p>
            <p class="mt-1 font-bold text-black">{{ state.rfpData.budget }}</p>
          </div>
        </div>
      </div>

      <!-- Compliance & Win Score Row -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Compliance Summary -->
        <div class="card animate-slide-up" style="animation-delay: 100ms;">
          <h3 class="text-lg font-bold text-black mb-6">Compliance Summary</h3>
          <div class="flex items-center gap-8 mb-6">
            <div class="relative w-32 h-32">
              <svg class="w-32 h-32 transform -rotate-90" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="52" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="10" />
                <circle
                  cx="60" cy="60" r="52" fill="none"
                  :stroke="complianceColor"
                  stroke-width="10"
                  stroke-linecap="round"
                  :stroke-dasharray="circumference"
                  :stroke-dashoffset="circumference - (circumference * state.compliance.score / 100)"
                  class="transition-all duration-1000 ease-out"
                  :style="{ filter: `drop-shadow(0 0 8px ${complianceColor}40)` }"
                />
              </svg>
              <div class="absolute inset-0 flex flex-col items-center justify-center">
                <span class="text-3xl font-bold animate-counter" :class="complianceTextColor">{{ state.compliance.score }}%</span>
                <span class="text-xs text-black font-medium">Score</span>
              </div>
            </div>
            <div class="flex-1 space-y-3">
              <div class="flex items-center justify-between py-2 border-b border-white/[0.04]">
                <span class="text-sm text-black">Total Requirements</span>
                <span class="font-bold text-black">{{ state.compliance.total }}</span>
              </div>
              <div class="flex items-center justify-between py-2 border-b border-white/[0.04]">
                <span class="text-sm text-black">Passed</span>
                <span class="font-bold text-glow-success">{{ state.compliance.passed }}</span>
              </div>
              <div class="flex items-center justify-between py-2 border-b border-white/[0.04]">
                <span class="text-sm text-black">Failed</span>
                <span class="font-bold text-glow-error">{{ state.compliance.failed }}</span>
              </div>
              <div class="flex items-center justify-between py-2">
                <span class="text-sm text-black">Pending</span>
                <span class="font-bold text-glow-warning">{{ state.compliance.pending }}</span>
              </div>
            </div>
          </div>
          <!-- Progress bar -->
          <div class="w-full bg-surface-800 rounded-full h-2.5 overflow-hidden">
            <div class="flex h-2.5 rounded-full overflow-hidden">
              <div class="bg-glow-success transition-all duration-1000 ease-out" :style="{ width: (state.compliance.passed / state.compliance.total * 100) + '%', filter: 'drop-shadow(0 0 6px rgba(16,185,129,0.4))' }"></div>
              <div class="bg-glow-error transition-all duration-1000 ease-out" :style="{ width: (state.compliance.failed / state.compliance.total * 100) + '%', filter: 'drop-shadow(0 0 6px rgba(239,68,68,0.4))' }"></div>
              <div class="bg-glow-warning transition-all duration-1000 ease-out" :style="{ width: (state.compliance.pending / state.compliance.total * 100) + '%', filter: 'drop-shadow(0 0 6px rgba(245,158,11,0.4))' }"></div>
            </div>
          </div>
        </div>

        <!-- Win Probability -->
        <div class="card animate-slide-up" style="animation-delay: 200ms;">
          <h3 class="text-lg font-bold text-black mb-6">Win Probability</h3>
          <div class="text-center mb-6">
            <div class="inline-flex items-center justify-center w-32 h-32 rounded-full border-[3px]"
              :class="state.winScore.score > 70 ? 'border-glow-success shadow-glow-success' : 'border-glow-error shadow-glow-error'"
              :style="{ filter: state.winScore.score > 70 ? 'drop-shadow(0 0 20px rgba(16,185,129,0.3))' : 'drop-shadow(0 0 20px rgba(239,68,68,0.3))' }">
              <div>
                <span class="text-4xl font-bold animate-counter" :class="state.winScore.score > 70 ? 'text-glow-success' : 'text-glow-error'">
                  {{ state.winScore.score }}%
                </span>
              </div>
            </div>
            <div class="mt-3">
              <span class="inline-flex items-center px-4 py-1.5 rounded-full text-sm font-bold"
                :class="state.winScore.label === 'GO'
                  ? 'bg-glow-success/15 text-glow-success border border-glow-success/30 shadow-glow-success'
                  : 'bg-glow-error/15 text-glow-error border border-glow-error/30 shadow-glow-error'">
                {{ state.winScore.label }}
              </span>
            </div>
          </div>
          <!-- Factors -->
          <div class="space-y-3">
            <div v-for="(factor, fIndex) in state.winScore.factors" :key="factor.name"
              class="stagger-item"
              :style="{ animationDelay: (fIndex * 60 + 300) + 'ms' }">
              <div class="flex items-center justify-between text-sm mb-1">
                <span class="text-black">{{ factor.name }}</span>
                <span class="font-bold text-surface-200">{{ factor.score }}%</span>
              </div>
              <div class="w-full bg-surface-800 rounded-full h-1.5 overflow-hidden">
                <div class="h-1.5 rounded-full transition-all duration-1000 ease-out"
                  :class="factor.score >= 80 ? 'bg-glow-success' : factor.score >= 60 ? 'bg-glow-warning' : 'bg-glow-error'"
                  :style="{ width: factor.score + '%', filter: factor.score >= 80 ? 'drop-shadow(0 0 4px rgba(16,185,129,0.4))' : factor.score >= 60 ? 'drop-shadow(0 0 4px rgba(245,158,11,0.4))' : 'drop-shadow(0 0 4px rgba(239,68,68,0.4))' }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Requirements Table -->
      <div class="card animate-slide-up" style="animation-delay: 300ms;">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-bold text-black">Extracted Requirements</h3>
          <span class="text-sm text-black font-medium">{{ state.requirements.length }} requirements found</span>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b border-white/[0.06]">
                <th class="text-left py-3 px-4 text-xs font-semibold text-black uppercase tracking-wider">#</th>
                <th class="text-left py-3 px-4 text-xs font-semibold text-black uppercase tracking-wider">Requirement</th>
                <th class="text-left py-3 px-4 text-xs font-semibold text-black uppercase tracking-wider">Type</th>
                <th class="text-left py-3 px-4 text-xs font-semibold text-black uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/[0.04]">
              <tr
                v-for="(req, index) in state.requirements"
                :key="req.id"
                class="hover:bg-surface-800/40 transition-all duration-200 group stagger-item"
                :style="{ animationDelay: (index * 40 + 400) + 'ms' }"
              >
                <td class="py-3 px-4 text-sm text-black font-medium">{{ index + 1 }}</td>
                <td class="py-3 px-4 text-sm font-medium text-black">{{ req.requirement }}</td>
                <td class="py-3 px-4">
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold text-black" style="background: rgba(200, 169, 110, 0.25); border: 1px solid rgba(200, 169, 110, 0.3);">
                    {{ req.type }}
                  </span>
                </td>
                <td class="py-3 px-4">
                  <span :class="statusBadgeClass(req.status)">{{ req.status }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Action Button -->
      <div class="flex justify-end animate-slide-up" style="animation-delay: 400ms;">
        <router-link to="/proposal" class="btn-primary group">
          View AI Generated Proposal
          <svg class="w-4 h-4 ml-2 transition-transform duration-200 group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </router-link>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { computed } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import { useAppStore } from '../store/state'

const { state } = useAppStore()

const circumference = 2 * Math.PI * 52

const complianceColor = computed(() => {
  if (state.compliance.score >= 80) return '#10b981'
  if (state.compliance.score >= 60) return '#f59e0b'
  return '#ef4444'
})

const complianceTextColor = computed(() => {
  if (state.compliance.score >= 80) return 'text-glow-success'
  if (state.compliance.score >= 60) return 'text-glow-warning'
  return 'text-glow-error'
})

function statusBadgeClass(status) {
  const classes = {
    PASS: 'badge-pass',
    FAIL: 'badge-fail',
    PENDING: 'badge-pending',
  }
  return classes[status] || 'badge-pending'
}
</script>
