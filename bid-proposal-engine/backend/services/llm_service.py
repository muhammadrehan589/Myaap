"""LLM Service — High-level API for LLM operations.

Provides domain-specific functions (extract_requirements, generate_proposal)
that use the production-ready LLMService orchestrator under the hood.

This module is the public API consumed by routes. It delegates all LLM
communication to services/llm/service.py which handles:
- Multi-provider fallback (Gemini → OpenAI → Groq)
- Retry with exponential backoff
- 24-hour response caching
- Error classification and logging
"""

import json
import logging
from services.llm.service import LLMService

logger = logging.getLogger(__name__)

# Singleton LLM service instance (lazy-initialized)
_llm_service: LLMService = None


def _get_llm_service() -> LLMService:
    """Get or create the singleton LLMService instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
        stats = _llm_service.get_stats()
        logger.info(f"LLM service initialized: {stats['providers_registered']}")
    return _llm_service


def _generate(prompt: str) -> str:
    """Generate a response using the LLM service with full fallback/retry/caching."""
    service = _get_llm_service()
    return service.generate(prompt)


def _clean_json_response(raw: str) -> str:
    """Clean markdown fences and whitespace from LLM JSON responses.

    Handles truncated JSON by attempting to close unclosed brackets.
    """
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()

    # Handle truncated JSON - try to close unclosed brackets
    open_braces = raw.count('{') - raw.count('}')
    open_brackets = raw.count('[') - raw.count(']')

    if open_braces > 0 or open_brackets > 0:
        logger.warning(f"JSON appears truncated: {open_braces} unclosed braces, {open_brackets} unclosed brackets")
        # Close any incomplete string
        if raw.count('"') % 2 != 0:
            raw += '"'
        # Close arrays then objects
        raw += ']' * open_brackets
        raw += '}' * open_braces

    return raw


# Maximum characters from RFP text sent to LLM
# Reduced to prevent response truncation and JSON parsing errors
RFP_TEXT_MAX_CHARS = 15000


def extract_requirements_and_entities(text: str) -> dict:
    """Extract and CLASSIFY all document elements into strict categories.

    Classification rules:
    1. Mandatory Requirement — what the vendor MUST deliver/demonstrate
    2. Preferred Requirement — what the vendor SHOULD have
    3. Evaluation Criteria — scoring rules, weights
    4. Vendor Question — questions asked to vendor
    5. Pricing Question — cost fields, pricing templates
    6. Submission Instructions — NOT requirements (formatting, deadlines, packaging)
    7. Placeholder / Noise — template instructions, boilerplate
    """
    prompt = f"""You are an expert procurement intelligence analyst.

Your task is to parse the document and classify EACH item into EXACTLY ONE category.

===== CLASSIFICATION RULES =====

1. Mandatory Requirement — What the vendor MUST deliver, demonstrate, or possess:
   - Technical capabilities required
   - Certifications/licenses needed
   - Experience requirements
   - Staffing qualifications
   - Deliverables expected
   EXAMPLES: "Must have ISO 27001 certification", "Minimum 5 years healthcare IT experience"

2. Preferred Requirement — What the vendor SHOULD have (nice-to-have):
   - Additional capabilities
   - Bonus qualifications
   EXAMPLES: "AWS experience preferred", "HIPAA compliance desirable"

3. Evaluation Criteria — How proposals are scored/weighted:
   - Scoring weights
   - Rating criteria
   EXAMPLES: "Technical approach: 40%", "Past performance: 30%"

4. Vendor Question — Questions the vendor must answer:
   - "Describe your approach to..."
   - "What is your experience with..."

5. Pricing Question — Cost-related fields:
   - Rate cards
   - Budget forms

6. Submission Instructions — NOT requirements, just process/procedure:
   - How to format the proposal
   - Where to submit
   - Number of copies needed
   - Paper size, font requirements
   - Deadline dates for submission
   - Sealing/labeling instructions
   EXAMPLES: "Proposals must be sealed and labeled", "Submit 3 copies", "Use Times Roman 12pt"

7. Placeholder / Noise — Template boilerplate

===== CRITICAL RULES =====
- Submission Instructions are NOT requirements — classify them separately
- Evaluation Criteria are NOT compliance items
- Do NOT extract formatting/packaging instructions as requirements
- Only extract what the vendor MUST DELIVER or DEMONSTRATE as requirements
- If unsure whether something is a requirement or instruction, classify as Submission Instructions

Return ONLY valid JSON (no markdown, no code fences) with this exact structure:
{{
  "document_type": "RFP | Vendor Questionnaire | Mixed | Pricing Form | Other",
  "document_confidence": 0.0 to 1.0,
  "project_name": "extracted project name or 'Not specified'",
  "deadlines": "extracted deadline or 'Not specified'",
  "budget": "extracted budget or 'Not specified'",
  "mandatory_requirements": [
    {{
      "text": "exact requirement text",
      "section": "section number or heading where found",
      "type": "compliance | technical | experience"
    }}
  ],
  "preferred_requirements": [
    {{
      "text": "exact requirement text",
      "section": "section number or heading where found",
      "type": "compliance | technical | experience"
    }}
  ],
  "evaluation_criteria": [
    {{
      "criterion": "criterion name",
      "weight": "percentage or points",
      "description": "what is evaluated"
    }}
  ],
  "vendor_questions": [
    {{
      "question": "exact question text",
      "section": "section where found",
      "response_type": "narrative | table | list | attachment"
    }}
  ],
  "pricing_questions": [
    {{
      "description": "what pricing is requested",
      "section": "section where found"
    }}
  ],
  "submission_instructions": [
    {{
      "text": "submission instruction text",
      "section": "section where found"
    }}
  ],
  "noise": [
    "placeholder or noise text identified"
  ]
}}

===== DOCUMENT TEXT =====
{text[:RFP_TEXT_MAX_CHARS]}"""

    raw = _generate(prompt)
    raw = _clean_json_response(raw)
    return json.loads(raw)


def generate_proposal(context: dict) -> dict:
    """Generate a structured proposal using ONLY verified dataset evidence.

    Applies strict domain-aware matching rules:
    1. Core context analysis before matching
    2. Strict domain alignment (no naive keyword matching)
    3. Financial/scale verification
    4. Semantic meaning over keywords
    5. Zero hallucination with honest gaps

    Returns JSON with strict format.
    """
    requirements = context.get("requirements", [])
    capability_matches = context.get("capability_matches", [])
    compliance_results = context.get("compliance_results", [])
    document_type = context.get("document_type", "RFP")

    # Build capability evidence block with ALL dataset fields
    capability_blocks = []
    for m in capability_matches:
        cap = m.get("capability", {})
        cap_id = cap.get("cap_id", "UNKNOWN")
        domain = cap.get("domain", "")
        project_summary = cap.get("project_summary", "")
        certification = cap.get("certification", "N/A")
        client_type = cap.get("client_type", "")
        year_completed = cap.get("year_completed", "")
        contract_value = cap.get("contract_value", "")

        capability_blocks.append(
            f"cap_id: {cap_id}\n"
            f"domain: {domain}\n"
            f"project_summary: {project_summary}\n"
            f"certification: {certification}\n"
            f"client_type: {client_type}\n"
            f"year_completed: {year_completed}\n"
            f"contract_value: {contract_value}\n"
            f"matched_requirement: {m.get('requirement', '')}\n"
            f"similarity_score: {m.get('score', 0)}"
        )

    capabilities_text = "\n---\n".join(capability_blocks) if capability_blocks else "NO CAPABILITIES AVAILABLE"

    # Build requirements list
    requirements_text = "\n".join(
        f"- {r.get('text', str(r)) if isinstance(r, dict) else str(r)}"
        for r in requirements
    )

    # Build compliance mapping
    compliance_lines = []
    for r in compliance_results:
        status = r.get("status", "UNKNOWN")
        req_text = r.get("requirement", "")
        evidence = r.get("evidence", "NO EVIDENCE")
        compliance_lines.append(f"- requirement: {req_text}\n  status: {status}\n  evidence: {evidence}")
    compliance_text = "\n".join(compliance_lines) if compliance_lines else "NO COMPLIANCE DATA"

    prompt = f"""You are a Senior Bid & Proposal Manager and expert in technical compliance.
Your task is to evaluate an RFP and draft a proposal response using ONLY the provided Capability Library dataset.

===== STEP 1: CORE CONTEXT ANALYSIS =====
Before matching any data, identify the specific domain, scope, and scale of this RFP.
Document type: {document_type}
Keep this core context in mind for every decision you make.

===== STEP 2: STRICT MATCHING RULES (NON-NEGOTIABLE) =====

RULE 1 — STRICT DOMAIN ALIGNMENT:
Do NOT match different sub-domains just because they share a high-level keyword.
For example:
- If RFP asks for "Hospital IT", do NOT propose "Medical Equipment" just because both are healthcare
- If RFP asks for "Cloud AWS", do NOT propose "Network Design" just because both are technical
- If the exact domain is missing, declare "NO RELEVANT EVIDENCE AVAILABLE"

RULE 2 — FINANCIAL & SCALE LOGIC:
If the RFP requires past projects of a specific scale, mathematically verify the Contract Value.
Reject any projects that do not meet the threshold.

RULE 3 — SEMANTIC MEANING OVER KEYWORDS:
For qualitative requirements, do not map random projects just because they exist.
The capability must explicitly prove the specific trait.

RULE 4 — ZERO HALLUCINATION & HONEST GAPS:
Do NOT invent licenses, geographic proximity, or capabilities.
It is better to have a 10% compliance score that is honest than a 90% score that is hallucinated.
If a requirement fails contextual checks, explicitly state the gap.

===== STEP 3: DATA BOUNDARIES =====
You are ONLY allowed to use these exact fields from capability records:
- cap_id, domain, project_summary, certification, client_type, year_completed, contract_value

You are NOT allowed to:
- Create, rename, or merge projects
- Infer missing certifications
- Assume any missing field
- Use general world knowledge

===== VERIFIED CAPABILITY RECORDS ({len(capability_matches)} entries) =====
{capabilities_text}

===== EXTRACTED REQUIREMENTS =====
{requirements_text}

===== COMPLIANCE ENGINE OUTPUT (DO NOT OVERRIDE) =====
{compliance_text}

===== BUDGET & DEADLINE =====
Budget: {context.get('budget', 'Not specified')}
Deadline: {context.get('deadlines', 'Not specified')}

===== OUTPUT FORMAT (Return ONLY valid JSON) =====

{{
  "core_context": {{
    "domain": "identified RFP domain",
    "scope": "identified scope",
    "scale": "identified scale/budget range"
  }},
  "proposal": {{
    "executive_summary": "2-3 paragraphs. ONLY reference verified capabilities that pass strict domain alignment.",
    "technical_approach": "Address each requirement with strict domain matching. If no valid match exists, state: 'NO RELEVANT EVIDENCE AVAILABLE in our capability library.'",
    "company_experience": [
      {{
        "cap_id": "EXACT cap_id from record",
        "domain": "EXACT domain from record",
        "project_summary": "EXACT project_summary from record",
        "certification": "EXACT certification from record",
        "client_type": "EXACT client_type from record",
        "year_completed": "EXACT year_completed from record"
      }}
    ],
    "compliance_mapping": [
      {{
        "requirement": "exact requirement text",
        "status": "PASS or FAIL from compliance engine — DO NOT change",
        "evidence": "exact evidence or 'NO RELEVANT EVIDENCE AVAILABLE'"
      }}
    ],
    "conclusion": "Summarize capabilities and gaps honestly. If gaps exist, acknowledge them directly."
  }}
}}

===== COMPANY EXPERIENCE RULE =====
For EVERY experience mention, you MUST use the exact format with real cap_id.
DO NOT fabricate projects. ONLY use real cap_id from dataset.
If no capabilities pass strict domain alignment, return empty array: "company_experience": []

===== COMPLIANCE RULE =====
Use compliance engine output EXACTLY. Do NOT override FAIL to PASS.
If requirement is FAIL, state FAIL clearly with honest explanation.

===== LANGUAGE RULE =====
- Formal, enterprise-grade language
- Be direct and professional
- An honest FAIL is better than a hallucinated PASS

Return ONLY the JSON object. No markdown fences, no extra text."""

    raw = _generate(prompt)
    raw = _clean_json_response(raw)
    return json.loads(raw)


def get_llm_stats() -> dict:
    """Get LLM service statistics (for monitoring/debugging)."""
    service = _get_llm_service()
    return service.get_stats()


def clear_llm_cache() -> int:
    """Clear the LLM response cache."""
    service = _get_llm_service()
    return service.clear_cache()
