import { reactive } from 'vue'

const API_BASE = 'http://localhost:8001'
const DEFAULT_COMPANY_NAME = 'TechCorp Solutions'
const DEFAULT_STATUS = 'Under Review'
const DEFAULT_AGENCY = 'Auto-detected'
const CAPABILITY_SCORE_OFFSET = 10
const EXPERIENCE_SCORE_OFFSET = 5
const DEFAULT_BUDGET_FIT = 85

const state = reactive({
  uploadedFile: null,
  workspaceId: null,
  isUploading: false,
  isAnalyzing: false,
  rfpData: null,
  requirements: [],
  compliance: null,
  winScore: null,
  proposal: null,
})

/**
 * Shared fetch wrapper with error handling.
 * Eliminates duplicated try/catch + response parsing across all API calls.
 */
async function apiFetch(endpoint, options = {}) {
  let res
  try {
    res = await fetch(`${API_BASE}${endpoint}`, options)
  } catch (e) {
    throw new Error(`Cannot connect to backend at ${API_BASE}. Is the server running? (${e.message})`)
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(`${endpoint} failed: ${err.detail || res.statusText}`)
  }
  return res.json()
}

export function useAppStore() {
  async function uploadFile(file) {
    const formData = new FormData()
    formData.append('file', file)

    const data = await apiFetch('/upload-rfp', { method: 'POST', body: formData })
    state.workspaceId = data.workspace_id
    state.uploadedFile = file
    return data
  }

  async function extractRequirements() {
    const data = await apiFetch('/extract-requirements', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workspace_id: state.workspaceId }),
    })

    state.rfpData = {
      name: data.project_name || 'Untitled RFP',
      deadline: data.deadlines || 'Not specified',
      budget: data.budget || 'Not specified',
      status: DEFAULT_STATUS,
      agency: DEFAULT_AGENCY,
      submittedBy: DEFAULT_COMPANY_NAME,
      rfpNumber: `RFP-${state.workspaceId.slice(0, 8).toUpperCase()}`,
    }

    state.requirements = (data.requirements || []).map((r, i) => ({
      id: i + 1,
      requirement: r.text,
      type: r.type,
      status: 'PENDING',
    }))

    return data
  }

  async function runComplianceCheck() {
    const reqTexts = state.requirements.map(r => r.requirement)
    const data = await apiFetch('/compliance-check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ requirements: reqTexts }),
    })

    state.requirements = state.requirements.map((r, i) => ({
      ...r,
      status: data.results[i]?.status || 'PENDING',
    }))

    state.compliance = {
      total: data.total,
      passed: data.passed,
      failed: data.failed,
      pending: state.requirements.filter(r => r.status === 'PENDING').length,
      score: data.score,
    }

    return data
  }

  async function runCapabilityMatch() {
    const reqTexts = state.requirements.map(r => r.requirement)
    return apiFetch('/retrieve-capabilities', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ requirements: reqTexts }),
    })
  }

  async function calculateWinScore() {
    const complianceScore = state.compliance?.score || 0
    const capabilityScore = Math.min(100, complianceScore + CAPABILITY_SCORE_OFFSET)
    const experienceScore = Math.min(100, complianceScore + EXPERIENCE_SCORE_OFFSET)

    const data = await apiFetch('/score', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        compliance_score: complianceScore,
        capability_score: capabilityScore,
        experience_score: experienceScore,
        budget_fit: DEFAULT_BUDGET_FIT,
      }),
    })

    state.winScore = {
      score: data.win_probability,
      label: data.decision,
      factors: [
        { name: 'Compliance', score: complianceScore },
        { name: 'Technical Fit', score: capabilityScore },
        { name: 'Past Performance', score: experienceScore },
        { name: 'Price Competitiveness', score: DEFAULT_BUDGET_FIT },
        { name: 'Team Qualification', score: Math.round((capabilityScore + experienceScore) / 2) },
      ],
    }

    return data
  }

  async function generateProposal() {
    const data = await apiFetch('/generate-proposal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workspace_id: state.workspaceId }),
    })

    // Parse the proposal text into sections
    const raw = data.proposal
    const sections = []
    const sectionRegex = /(?:^|\n)(?:\d+\.\s*)?([A-Z][A-Z\s&]+?)(?:\n|=+\n)([\s\S]*?)(?=\n(?:\d+\.\s*)?[A-Z][A-Z\s&]+?(?:\n|=+\n)|$)/g
    let match
    while ((match = sectionRegex.exec(raw)) !== null) {
      const heading = match[1].trim()
      const content = match[2].trim()
      if (heading && content) {
        sections.push({ heading, content })
      }
    }

    // Fallback: if parsing fails, use raw text as single section
    if (sections.length === 0) {
      sections.push({ heading: 'AI Generated Proposal', content: raw })
    }

    state.proposal = {
      title: state.rfpData?.name || 'AI Generated Proposal',
      subtitle: `Submitted by ${state.rfpData?.submittedBy || DEFAULT_COMPANY_NAME}`,
      date: new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }),
      sections,
    }

    return data
  }

  async function runFullPipeline(file) {
    // Step 1: Upload
    state.isUploading = true
    await uploadFile(file)
    state.isUploading = false

    // Step 2: Extract
    state.isAnalyzing = true
    await extractRequirements()

    // Step 3: Compliance + RAG
    await runComplianceCheck()
    await runCapabilityMatch()

    // Step 4: Win score
    await calculateWinScore()
    state.isAnalyzing = false
  }

  function resetState() {
    state.uploadedFile = null
    state.workspaceId = null
    state.isUploading = false
    state.isAnalyzing = false
    state.rfpData = null
    state.requirements = []
    state.compliance = null
    state.winScore = null
    state.proposal = null
  }

  return {
    state,
    uploadFile,
    extractRequirements,
    runComplianceCheck,
    runCapabilityMatch,
    calculateWinScore,
    generateProposal,
    runFullPipeline,
    resetState,
  }
}
