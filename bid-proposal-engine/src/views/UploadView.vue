<template>
  <AppLayout>
    <div class="max-w-2xl mx-auto mt-12">
      <!-- Upload Card -->
      <div class="card">
        <div class="text-center mb-8">
          <div class="w-16 h-16 bg-primary-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <svg class="w-8 h-8 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          <h2 class="text-2xl font-bold text-gray-900 mb-2">Upload RFP Document</h2>
          <p class="text-gray-500">Upload your Request for Proposal document and let AI analyze it for you.</p>
        </div>

        <!-- Drop Zone -->
        <div
          @dragover.prevent="isDragging = true"
          @dragleave="isDragging = false"
          @drop.prevent="handleDrop"
          @click="triggerFileInput"
          class="border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-200"
          :class="isDragging
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'"
        >
          <input
            ref="fileInput"
            type="file"
            accept=".pdf,.doc,.docx"
            class="hidden"
            @change="handleFileSelect"
          />

          <div v-if="!selectedFile">
            <svg class="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m6.75 12l-3-3m0 0l-3 3m3-3v6m-1.5-15H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
            <p class="text-gray-600 font-medium mb-1">Drag and drop your RFP document here</p>
            <p class="text-sm text-gray-400">PDF, DOC, or DOCX up to 50MB</p>
          </div>

          <div v-else class="flex items-center justify-center gap-4">
            <svg class="w-10 h-10 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <div class="text-left">
              <p class="font-medium text-gray-900">{{ selectedFile.name }}</p>
              <p class="text-sm text-gray-500">{{ formatFileSize(selectedFile.size) }}</p>
            </div>
            <button @click.stop="clearFile" class="ml-4 p-1 text-gray-400 hover:text-red-500 rounded">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Upload Button -->
        <div class="mt-6 flex justify-center">
          <button
            @click="uploadFile"
            :disabled="!selectedFile || isProcessing"
            class="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg v-if="!isProcessing" class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            {{ isProcessing ? 'Processing...' : 'Upload RFP' }}
          </button>
        </div>
      </div>

      <!-- Processing Overlay -->
      <div v-if="isProcessing" class="mt-6 card">
        <div class="flex items-center gap-4">
          <div class="flex-shrink-0">
            <div class="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
              <svg class="animate-spin w-5 h-5 text-primary-600" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
              </svg>
            </div>
          </div>
          <div class="flex-1">
            <p class="font-medium text-gray-900">{{ processingStep }}</p>
            <p class="text-sm text-gray-500">This may take a few moments...</p>
          </div>
        </div>

        <!-- Progress Steps -->
        <div class="mt-6 space-y-3">
          <div v-for="(step, index) in steps" :key="index" class="flex items-center gap-3">
            <div class="flex-shrink-0">
              <div v-if="index < currentStep" class="w-6 h-6 bg-emerald-500 rounded-full flex items-center justify-center">
                <svg class="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div v-else-if="index === currentStep" class="w-6 h-6 bg-primary-500 rounded-full flex items-center justify-center">
                <div class="w-2 h-2 bg-white rounded-full animate-pulse"></div>
              </div>
              <div v-else class="w-6 h-6 bg-gray-200 rounded-full"></div>
            </div>
            <span :class="index <= currentStep ? 'text-gray-900 font-medium' : 'text-gray-400'">{{ step }}</span>
          </div>
        </div>
      </div>

      <!-- Supported Formats -->
      <div class="mt-6 flex items-center justify-center gap-6 text-xs text-gray-400">
        <span class="flex items-center gap-1">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 2l5 5h-5V4zM6 20V4h5v7h7v9H6z"/></svg>
          PDF
        </span>
        <span class="flex items-center gap-1">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 2l5 5h-5V4zM6 20V4h5v7h7v9H6z"/></svg>
          DOCX
        </span>
        <span class="flex items-center gap-1">
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 2l5 5h-5V4zM6 20V4h5v7h7v9H6z"/></svg>
          DOC
        </span>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'
import { useAppStore } from '../store/state'

const router = useRouter()
const { runFullPipeline } = useAppStore()

const fileInput = ref(null)
const selectedFile = ref(null)
const isDragging = ref(false)
const isProcessing = ref(false)
const currentStep = ref(0)

const steps = [
  'Parsing document structure...',
  'Extracting requirements...',
  'Running compliance analysis...',
  'Calculating win probability...',
  'Generating insights...',
]

const processingStep = ref(steps[0])

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileSelect(event) {
  const file = event.target.files[0]
  if (file) {
    selectedFile.value = file
  }
}

function handleDrop(event) {
  isDragging.value = false
  const file = event.dataTransfer.files[0]
  if (file) {
    selectedFile.value = file
  }
}

function clearFile() {
  selectedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

async function uploadFile() {
  if (!selectedFile.value || isProcessing.value) return

  isProcessing.value = true

  try {
    // Step 1: Upload
    currentStep.value = 0
    processingStep.value = steps[0]
    await runFullPipeline(selectedFile.value)

    router.push('/dashboard')
  } catch (err) {
    alert('Error: ' + err.message)
  } finally {
    isProcessing.value = false
  }
}
</script>
