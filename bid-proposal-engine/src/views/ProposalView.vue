<template>
  <AppLayout>
    <!-- Generating state -->
    <div v-if="isGenerating" class="text-center py-20">
      <svg class="animate-spin w-16 h-16 text-primary-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
      </svg>
      <h3 class="text-lg font-medium text-gray-900 mb-2">Generating Proposal...</h3>
      <p class="text-gray-500">AI is analyzing requirements and drafting your proposal.</p>
    </div>

    <!-- Error state -->
    <div v-else-if="generationError" class="text-center py-20">
      <svg class="w-16 h-16 text-red-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
      </svg>
      <h3 class="text-lg font-medium text-gray-900 mb-2">Proposal Generation Failed</h3>
      <p class="text-red-600 mb-6">{{ generationError }}</p>
      <button @click="regenerate" class="btn-primary">Try Again</button>
    </div>

    <!-- No workspace / no proposal state -->
    <div v-else-if="!state.proposal" class="text-center py-20">
      <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
      </svg>
      <h3 class="text-lg font-medium text-gray-900 mb-2">No Proposal Available</h3>
      <p class="text-gray-500 mb-6">Upload and analyze an RFP first to generate a proposal.</p>
      <router-link to="/upload" class="btn-primary">Upload RFP</router-link>
    </div>

    <!-- Proposal content -->
    <div v-else>
      <!-- Header & Actions -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-xl font-bold text-gray-900">AI Generated Proposal</h2>
          <p class="text-sm text-gray-500 mt-1">Generated on {{ state.proposal.date }}</p>
        </div>
        <div class="flex items-center gap-3">
          <button @click="copyProposal" class="btn-secondary">
            <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
            </svg>
            {{ copied ? 'Copied!' : 'Copy Proposal' }}
          </button>
          <button @click="regenerate" :disabled="isRegenerating" class="btn-secondary">
            <svg class="w-4 h-4 mr-2" :class="{ 'animate-spin': isRegenerating }" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {{ isRegenerating ? 'Regenerating...' : 'Regenerate' }}
          </button>
          <button @click="downloadPdf" class="btn-primary">
            <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Download PDF
          </button>
        </div>
      </div>

      <!-- Regenerating overlay -->
      <div v-if="isRegenerating" class="card mb-6">
        <div class="flex items-center gap-4">
          <svg class="animate-spin w-6 h-6 text-primary-600" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
          </svg>
          <div>
            <p class="font-medium text-gray-900">AI is regenerating the proposal...</p>
            <p class="text-sm text-gray-500">This may take a few moments</p>
          </div>
        </div>
      </div>

      <!-- Proposal Document -->
      <div class="card" id="proposal-document">
        <!-- Document Header -->
        <div class="text-center border-b border-gray-200 pb-8 mb-8">
          <div class="w-16 h-16 bg-primary-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h1 class="text-2xl font-bold text-gray-900">{{ state.proposal.title }}</h1>
          <p class="text-gray-500 mt-2">{{ state.proposal.subtitle }}</p>
          <p class="text-sm text-gray-400 mt-1">{{ state.proposal.date }}</p>
        </div>

        <!-- Table of Contents -->
        <div class="mb-8 p-4 bg-gray-50 rounded-lg">
          <h4 class="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-3">Table of Contents</h4>
          <ol class="space-y-1">
            <li v-for="(section, index) in state.proposal.sections" :key="index" class="text-sm text-primary-600 hover:text-primary-700">
              {{ index + 1 }}. {{ section.heading }}
            </li>
          </ol>
        </div>

        <!-- Sections -->
        <div class="space-y-8">
          <div v-for="(section, index) in state.proposal.sections" :key="index">
            <h2 class="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span class="w-7 h-7 bg-primary-100 text-primary-700 rounded-lg flex items-center justify-center text-sm font-bold">
                {{ index + 1 }}
              </span>
              {{ section.heading }}
            </h2>
            <div class="text-gray-700 leading-relaxed whitespace-pre-line pl-9">
              {{ section.content }}
            </div>
          </div>
        </div>

        <!-- Document Footer -->
        <div class="mt-12 pt-8 border-t border-gray-200 text-center text-sm text-gray-500">
          <p>This proposal was generated by BidEngine AI — {{ state.proposal.date }}</p>
          <p class="mt-1">Confidential — For authorized recipients only</p>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AppLayout from '../components/AppLayout.vue'
import { useAppStore } from '../store/state'

const { state, generateProposal } = useAppStore()

const copied = ref(false)
const isRegenerating = ref(false)
// Start as true if we have a workspace but no proposal — prevents blank page flash
const isGenerating = ref(!state.proposal && !!state.workspaceId)
const generationError = ref('')

// Auto-generate proposal when page loads if not already generated
onMounted(async () => {
  if (!state.proposal && state.workspaceId) {
    // isGenerating is already true from ref initialization
    generationError.value = ''
    try {
      await generateProposal()
    } catch (err) {
      generationError.value = err.message
    } finally {
      isGenerating.value = false
    }
  } else if (!state.proposal && !state.workspaceId) {
    // No workspace — nothing to generate
    isGenerating.value = false
  }
})

async function copyProposal() {
  if (!state.proposal) return

  let text = `${state.proposal.title}\n${state.proposal.subtitle}\n${state.proposal.date}\n\n`
  state.proposal.sections.forEach((section, i) => {
    text += `${i + 1}. ${section.heading}\n${section.content}\n\n`
  })

  await navigator.clipboard.writeText(text)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}

async function regenerate() {
  isRegenerating.value = true
  generationError.value = ''
  try {
    await generateProposal()
  } catch (err) {
    generationError.value = err.message
  } finally {
    isRegenerating.value = false
  }
}

function downloadPdf() {
  alert('PDF download simulated — in production, this would generate and download a PDF file.')
}
</script>
