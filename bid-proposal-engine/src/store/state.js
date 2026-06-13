import { reactive } from 'vue'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8001'
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

    // Combine mandatory and preferred requirements
    const mandatory = (data.mandatory_requirements || []).map((r, i) => ({
      id: i + 1,
      requirement: r.text,
      type: r.type || 'compliance',
      priority: 'mandatory',
      status: 'PENDING',
    }))

    const preferred = (data.preferred_requirements || []).map((r, i) => ({
      id: mandatory.length + i + 1,
      requirement: r.text,
      type: r.type || 'technical',
      priority: 'preferred',
      status: 'PENDING',
    }))

    state.requirements = [...mandatory, ...preferred]

    return data
  }

  async function runComplianceCheck() {
    const mandatory = state.requirements.filter(r => r.priority === 'mandatory').map(r => r.requirement)
    const preferred = state.requirements.filter(r => r.priority === 'preferred').map(r => r.requirement)

    const data = await apiFetch('/compliance-check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mandatory_requirements: mandatory, preferred_requirements: preferred }),
    })

    state.requirements = state.requirements.map((r, i) => ({
      ...r,
      status: data.results[i]?.status || 'PENDING',
    }))

    state.compliance = {
      total: data.total_mandatory || mandatory.length,
      passed: data.pass || 0,
      partial: data.partial || 0,
      failed: data.fail || 0,
      pending: state.requirements.filter(r => r.status === 'PENDING').length,
      score: data.score || 0,
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

    // Backend now returns structured JSON proposal
    const proposalData = data.proposal?.proposal || data.proposal
    const sections = []

    // Map JSON sections to display format
    if (proposalData.executive_summary) {
      sections.push({ heading: 'Executive Summary', content: proposalData.executive_summary })
    }
    if (proposalData.technical_approach) {
      sections.push({ heading: 'Technical Approach', content: proposalData.technical_approach })
    }
    if (proposalData.company_experience && proposalData.company_experience.length > 0) {
      // Format company experience as readable text
      const expText = proposalData.company_experience.map((exp, i) => {
        return `[${exp.cap_id}] ${exp.domain}\n${exp.project_summary}\nCertification: ${exp.certification} | Client: ${exp.client_type} | Year: ${exp.year_completed}`
      }).join('\n\n')
      sections.push({ heading: 'Company Experience', content: expText })
    }
    if (proposalData.compliance_mapping && proposalData.compliance_mapping.length > 0) {
      const compText = proposalData.compliance_mapping.map(c => {
        return `${c.requirement}\nStatus: ${c.status}\nEvidence: ${c.evidence}`
      }).join('\n\n')
      sections.push({ heading: 'Compliance Mapping', content: compText })
    }
    if (proposalData.conclusion) {
      sections.push({ heading: 'Conclusion', content: proposalData.conclusion })
    }

    // Fallback if no sections parsed
    if (sections.length === 0) {
      sections.push({ heading: 'AI Generated Proposal', content: JSON.stringify(proposalData, null, 2) })
    }

    state.proposal = {
      title: state.rfpData?.name || 'AI Generated Proposal',
      subtitle: `Submitted by ${state.rfpData?.submittedBy || DEFAULT_COMPANY_NAME}`,
      date: new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }),
      sections,
      grounding_report: data.grounding_report,
      win_score: data.win_score,
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
