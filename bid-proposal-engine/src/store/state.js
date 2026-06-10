import { reactive } from 'vue'

const API_BASE = 'http://localhost:8000'

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

export function useAppStore() {
  function setUploadedFile(file) {
    state.uploadedFile = file
  }

  function setUploading(val) {
    state.isUploading = val
  }

  function setAnalyzing(val) {
    state.isAnalyzing = val
  }

  async function uploadFile(file) {
    const formData = new FormData()
    formData.append('file', file)

    const res = await fetch(`${API_BASE}/upload-rfp`, {
      method: 'POST',
      body: formData,
    })
    if (!res.ok) throw new Error('Upload failed')
    const data = await res.json()
    state.workspaceId = data.workspace_id
    state.uploadedFile = file
    return data
  }

  async function extractRequirements() {
    const res = await fetch(`${API_BASE}/extract-requirements`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workspace_id: state.workspaceId }),
    })
    if (!res.ok) throw new Error('Extraction failed')
    const data = await res.json()

    state.rfpData = {
      name: 'Hospital Management System',
      deadline: data.deadlines || 'Not specified',
      budget: data.budget || 'Not specified',
      status: 'Under Review',
      agency: 'Auto-detected',
      submittedBy: 'TechCorp Solutions',
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
    const res = await fetch(`${API_BASE}/compliance-check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ requirements: reqTexts }),
    })
    if (!res.ok) throw new Error('Compliance check failed')
    const data = await res.json()

    // Update requirement statuses
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
    const res = await fetch(`${API_BASE}/retrieve-capabilities`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ requirements: reqTexts }),
    })
    if (!res.ok) throw new Error('Capability matching failed')
    return await res.json()
  }

  async function calculateWinScore() {
    const complianceScore = state.compliance?.score || 0
    const capabilityScore = Math.min(100, complianceScore + 10)
    const experienceScore = Math.min(100, complianceScore + 5)
    const budgetFit = 85

    const res = await fetch(`${API_BASE}/score`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        compliance_score: complianceScore,
        capability_score: capabilityScore,
        experience_score: experienceScore,
        budget_fit: budgetFit,
      }),
    })
    if (!res.ok) throw new Error('Scoring failed')
    const data = await res.json()

    state.winScore = {
      score: data.win_probability,
      label: data.decision,
      factors: [
        { name: 'Compliance', score: complianceScore },
        { name: 'Technical Fit', score: capabilityScore },
        { name: 'Past Performance', score: experienceScore },
        { name: 'Price Competitiveness', score: budgetFit },
        { name: 'Team Qualification', score: Math.round((capabilityScore + experienceScore) / 2) },
      ],
    }

    return data
  }

  async function generateProposal() {
    const res = await fetch(`${API_BASE}/generate-proposal`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workspace_id: state.workspaceId }),
    })
    if (!res.ok) throw new Error('Proposal generation failed')
    const data = await res.json()

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
      subtitle: `Submitted by ${state.rfpData?.submittedBy || 'TechCorp Solutions'}`,
      date: new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }),
      sections,
    }

    return data
  }

  async function runFullPipeline(file) {
    // Step 1: Upload
    setUploading(true)
    await uploadFile(file)
    setUploading(false)

    // Step 2: Extract
    setAnalyzing(true)
    await extractRequirements()

    // Step 3: Compliance + RAG
    await runComplianceCheck()
    await runCapabilityMatch()

    // Step 4: Win score
    await calculateWinScore()
    setAnalyzing(false)
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
    setUploadedFile,
    setUploading,
    setAnalyzing,
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
