<template>
  <AppLayout>
    <div v-if="!state.rfpData" class="text-center py-20">
      <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5m6 4.125l2.25 2.25m0 0l2.25 2.25M12 13.875l2.25-2.25M12 13.875l-2.25 2.25M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
      </svg>
      <h3 class="text-lg font-medium text-gray-900 mb-2">No RFP Uploaded</h3>
      <p class="text-gray-500 mb-6">Upload an RFP document to view the analysis dashboard.</p>
      <router-link to="/upload" class="btn-primary">Upload RFP</router-link>
    </div>

    <div v-else class="space-y-6">
      <!-- RFP Summary -->
      <div class="card">
        <div class="flex items-start justify-between mb-4">
          <div>
            <h3 class="text-lg font-semibold text-gray-900">RFP Summary</h3>
            <p class="text-sm text-gray-500 mt-1">{{ state.rfpData.rfpNumber }}</p>
          </div>
          <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-amber-100 text-amber-800">
            {{ state.rfpData.status }}
          </span>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <p class="text-sm text-gray-500">Project Name</p>
            <p class="mt-1 font-semibold text-gray-900">{{ state.rfpData.name }}</p>
          </div>
          <div>
            <p class="text-sm text-gray-500">Agency</p>
            <p class="mt-1 font-semibold text-gray-900">{{ state.rfpData.agency }}</p>
          </div>
          <div>
            <p class="text-sm text-gray-500">Deadline</p>
            <p class="mt-1 font-semibold text-gray-900">{{ state.rfpData.deadline }}</p>
          </div>
          <div>
            <p class="text-sm text-gray-500">Budget</p>
            <p class="mt-1 font-semibold text-gray-900">{{ state.rfpData.budget }}</p>
          </div>
        </div>
      </div>

      <!-- Compliance & Win Score Row -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Compliance Summary -->
        <div class="card">
          <h3 class="text-lg font-semibold text-gray-900 mb-6">Compliance Summary</h3>
          <div class="flex items-center gap-8 mb-6">
            <div class="relative w-32 h-32">
              <svg class="w-32 h-32 transform -rotate-90" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="52" fill="none" stroke="#e5e7eb" stroke-width="10" />
                <circle
                  cx="60" cy="60" r="52" fill="none"
                  :stroke="complianceColor"
                  stroke-width="10"
                  stroke-linecap="round"
                  :stroke-dasharray="circumference"
                  :stroke-dashoffset="circumference - (circumference * state.compliance.score / 100)"
                  class="transition-all duration-1000"
                />
              </svg>
              <div class="absolute inset-0 flex flex-col items-center justify-center">
                <span class="text-3xl font-bold" :class="complianceTextColor">{{ state.compliance.score }}%</span>
                <span class="text-xs text-gray-500">Score</span>
              </div>
            </div>
            <div class="flex-1 space-y-3">
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600">Total Requirements</span>
                <span class="font-semibold text-gray-900">{{ state.compliance.total }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600">Passed</span>
                <span class="font-semibold text-emerald-600">{{ state.compliance.passed }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600">Failed</span>
                <span class="font-semibold text-red-600">{{ state.compliance.failed }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-sm text-gray-600">Pending</span>
                <span class="font-semibold text-amber-600">{{ state.compliance.pending }}</span>
              </div>
            </div>
          </div>
          <!-- Progress bar -->
          <div class="w-full bg-gray-100 rounded-full h-2.5">
            <div class="flex h-2.5 rounded-full overflow-hidden">
              <div class="bg-emerald-500 transition-all duration-1000" :style="{ width: (state.compliance.passed / state.compliance.total * 100) + '%' }"></div>
              <div class="bg-red-500 transition-all duration-1000" :style="{ width: (state.compliance.failed / state.compliance.total * 100) + '%' }"></div>
              <div class="bg-amber-500 transition-all duration-1000" :style="{ width: (state.compliance.pending / state.compliance.total * 100) + '%' }"></div>
            </div>
          </div>
        </div>

        <!-- Win Probability -->
        <div class="card">
          <h3 class="text-lg font-semibold text-gray-900 mb-6">Win Probability</h3>
          <div class="text-center mb-6">
            <div class="inline-flex items-center justify-center w-32 h-32 rounded-full border-8"
              :class="state.winScore.score > 70 ? 'border-emerald-500' : 'border-red-500'">
              <div>
                <span class="text-4xl font-bold" :class="state.winScore.score > 70 ? 'text-emerald-600' : 'text-red-600'">
                  {{ state.winScore.score }}%
                </span>
              </div>
            </div>
            <div class="mt-3">
              <span class="inline-flex items-center px-4 py-1.5 rounded-full text-sm font-bold"
                :class="state.winScore.label === 'GO' ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'">
                {{ state.winScore.label }}
              </span>
            </div>
          </div>
          <!-- Factors -->
          <div class="space-y-3">
            <div v-for="factor in state.winScore.factors" :key="factor.name">
              <div class="flex items-center justify-between text-sm mb-1">
                <span class="text-gray-600">{{ factor.name }}</span>
                <span class="font-medium text-gray-900">{{ factor.score }}%</span>
              </div>
              <div class="w-full bg-gray-100 rounded-full h-1.5">
                <div class="h-1.5 rounded-full transition-all duration-1000"
                  :class="factor.score >= 80 ? 'bg-emerald-500' : factor.score >= 60 ? 'bg-amber-500' : 'bg-red-500'"
                  :style="{ width: factor.score + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Requirements Table -->
      <div class="card">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-lg font-semibold text-gray-900">Extracted Requirements</h3>
          <span class="text-sm text-gray-500">{{ state.requirements.length }} requirements found</span>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="border-b border-gray-200">
                <th class="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">#</th>
                <th class="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Requirement</th>
                <th class="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Type</th>
                <th class="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="(req, index) in state.requirements" :key="req.id" class="hover:bg-gray-50 transition-colors">
                <td class="py-3 px-4 text-sm text-gray-500">{{ index + 1 }}</td>
                <td class="py-3 px-4 text-sm font-medium text-gray-900">{{ req.requirement }}</td>
                <td class="py-3 px-4">
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
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
      <div class="flex justify-end">
        <router-link to="/proposal" class="btn-primary">
          View AI Generated Proposal
          <svg class="w-4 h-4 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
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
  if (state.compliance.score >= 80) return 'text-emerald-600'
  if (state.compliance.score >= 60) return 'text-amber-600'
  return 'text-red-600'
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
