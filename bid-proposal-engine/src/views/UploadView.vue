<template>
  <AppLayout>
    <div class="max-w-2xl mx-auto mt-12">
      <!-- Page header with cinematic numbering -->
      <div class="text-center mb-10 animate-fade-in">
        <span class="text-sm font-bold tracking-[0.3em] uppercase" style="color: #000000;">01</span>
        <h1 class="text-4xl font-black mt-2 tracking-tight" style="color: #000000;">Upload RFP</h1>
        <div class="w-16 h-[1px] mx-auto mt-4" style="background: linear-gradient(90deg, transparent, rgba(200, 169, 110, 0.4), transparent);"></div>
      </div>

      <!-- Upload Card — Portal/Gate style -->
      <div class="card-portal animate-slide-up" style="animation-delay: 200ms;">
        <!-- Atmospheric glow behind card -->
        <div class="card-atmosphere"></div>

        <div class="relative z-10">
          <!-- Icon with golden ring -->
          <div class="text-center mb-8">
            <div class="icon-ring mx-auto mb-5">
              <div class="icon-inner">
                <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="#c8a96e" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
            </div>
            <h2 class="text-2xl font-bold mb-2 tracking-tight" style="color: #000000;">Upload RFP Document</h2>
            <p class="text-sm" style="color: #000000;">Upload your Request for Proposal document and let AI analyze it for you.</p>
          </div>

          <!-- Drop Zone — Gateway style -->
          <div
            @dragover.prevent="isDragging = true"
            @dragleave="isDragging = false"
            @drop.prevent="handleDrop"
            @click="triggerFileInput"
            class="dropzone-gateway"
            :class="{ 'active': isDragging, 'has-file': selectedFile }"
          >
            <input
              ref="fileInput"
              type="file"
              accept=".pdf,.doc,.docx"
              class="hidden"
              @change="handleFileSelect"
            />

            <!-- Dropzone glow effect -->
            <div class="dropzone-glow" :class="{ 'active': isDragging }"></div>

            <div v-if="!selectedFile" class="relative z-10">
              <svg class="w-14 h-14 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="#000000" stroke-width="1">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m6.75 12l-3-3m0 0l-3 3m3-3v6m-1.5-15H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
              <p class="font-semibold mb-1" style="color: #000000;">Drag and drop your RFP document here</p>
              <p class="text-xs tracking-wider uppercase" style="color: #000000;">PDF, DOC, or DOCX up to 50MB</p>
            </div>

            <div v-else class="relative z-10 flex items-center justify-center gap-4">
              <div class="w-12 h-12 rounded-xl flex items-center justify-center" style="background: rgba(200, 169, 110, 0.15); border: 1px solid rgba(200, 169, 110, 0.25);">
                <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="#c8a96e" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div class="text-left">
                <p class="font-semibold" style="color: #000000;">{{ selectedFile.name }}</p>
                <p class="text-sm" style="color: #000000;">{{ formatFileSize(selectedFile.size) }}</p>
              </div>
              <button @click.stop="clearFile" class="ml-4 p-2 rounded-lg transition-all" style="color: #000000;" @mouseover="$event.target.style.color='#dc2626'" @mouseleave="$event.target.style.color='#000000'">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Upload Button -->
          <div class="mt-8 flex justify-center">
            <button
              @click="uploadFile"
              :disabled="!selectedFile || isProcessing"
              class="btn-golden disabled:opacity-30 disabled:cursor-not-allowed disabled:shadow-none"
            >
              <svg v-if="!isProcessing" class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              {{ isProcessing ? 'Processing...' : 'Upload RFP' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Processing Overlay — Cinematic progress -->
      <div v-if="isProcessing" class="mt-6 card-portal animate-slide-up">
        <div class="relative z-10">
          <div class="flex items-center gap-4">
            <div class="flex-shrink-0">
              <div class="w-10 h-10 rounded-full border border-primary-500/30 flex items-center justify-center animate-glow-pulse">
                <svg class="animate-spin w-5 h-5 text-black-400" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                </svg>
              </div>
            </div>
            <div class="flex-1">
              <p class="font-semibold" style="color: #000000;">{{ processingStep }}</p>
              <p class="text-sm" style="color: #000000;">This may take a few moments...</p>
            </div>
          </div>

          <!-- Progress Steps — Sequential reveal -->
          <div class="mt-8 space-y-4">
            <div
              v-for="(step, index) in steps"
              :key="index"
              class="flex items-center gap-4 stagger-item"
              :style="{ animationDelay: (index * 100) + 'ms' }"
            >
              <div class="flex-shrink-0">
                <div v-if="index < currentStep" class="w-7 h-7 rounded-full flex items-center justify-center" style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3);">
                  <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="#059669" stroke-width="3">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div v-else-if="index === currentStep" class="w-7 h-7 rounded-full flex items-center justify-center animate-glow-pulse" style="border: 1px solid rgba(200, 169, 110, 0.5);">
                  <div class="w-2 h-2 rounded-full animate-pulse" style="background: #c8a96e;"></div>
                </div>
                <div v-else class="w-7 h-7 rounded-full" style="border: 1px solid rgba(200, 169, 110, 0.2);"></div>
              </div>
              <span class="text-sm" :style="{ color: '#000000', fontWeight: index <= currentStep ? '500' : '400' }">{{ step }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Supported Formats -->
      <div class="mt-8 flex items-center justify-center gap-8 text-xs tracking-wider uppercase" style="color: #000000;">
        <span class="flex items-center gap-2">
          <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 2l5 5h-5V4zM6 20V4h5v7h7v9H6z"/></svg>
          PDF
        </span>
        <span class="flex items-center gap-2">
          <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 2l5 5h-5V4zM6 20V4h5v7h7v9H6z"/></svg>
          DOCX
        </span>
        <span class="flex items-center gap-2">
          <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zm-1 2l5 5h-5V4zM6 20V4h5v7h7v9H6z"/></svg>
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

<style scoped>
/* Portal/Gate card style */
.card-portal {
  position: relative;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(200, 169, 110, 0.2);
  border-radius: 1rem;
  padding: 2rem;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}

.card-portal:hover {
  border-color: rgba(200, 169, 110, 0.35);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

/* Atmospheric glow behind card */
.card-atmosphere {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 120%;
  height: 120%;
  transform: translate(-50%, -50%);
  background: radial-gradient(ellipse, rgba(200, 169, 110, 0.08) 0%, transparent 60%);
  pointer-events: none;
}

/* Icon ring */
.icon-ring {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  border: 1px solid rgba(200, 169, 110, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: ringGlow 4s ease-in-out infinite;
}

.icon-inner {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(200, 169, 110, 0.12), rgba(200, 169, 110, 0.08));
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(200, 169, 110, 0.18);
}

@keyframes ringGlow {
  0%, 100% { box-shadow: 0 0 15px rgba(200, 169, 110, 0.15); }
  50% { box-shadow: 0 0 30px rgba(200, 169, 110, 0.3); }
}

/* Dropzone — Gateway style */
.dropzone-gateway {
  position: relative;
  border: 1px dashed rgba(200, 169, 110, 0.25);
  border-radius: 1rem;
  padding: 3rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  overflow: hidden;
  background: rgba(255, 255, 255, 0.4);
}

.dropzone-gateway:hover {
  border-color: rgba(200, 169, 110, 0.45);
  background: rgba(200, 169, 110, 0.06);
}

.dropzone-gateway.active {
  border-color: rgba(200, 169, 110, 0.6);
  background: rgba(200, 169, 110, 0.1);
}

.dropzone-gateway.has-file {
  border-color: rgba(200, 169, 110, 0.3);
  background: rgba(200, 169, 110, 0.05);
}

/* Dropzone glow */
.dropzone-glow {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at center, rgba(200, 169, 110, 0.12) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.4s ease;
}

.dropzone-glow.active {
  opacity: 1;
}

/* Golden button */
.btn-golden {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem 2rem;
  background: linear-gradient(135deg, #c8a96e, #d4b87a);
  color: #1a1510;
  font-weight: 700;
  font-size: 0.875rem;
  letter-spacing: 0.05em;
  border-radius: 0.75rem;
  box-shadow: 0 0 20px rgba(200, 169, 110, 0.25);
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.btn-golden:hover:not(:disabled) {
  box-shadow: 0 0 35px rgba(200, 169, 110, 0.4);
  transform: translateY(-1px);
}

.btn-golden:active:not(:disabled) {
  transform: scale(0.97);
}
</style>
