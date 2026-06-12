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
    """Clean markdown fences and whitespace from LLM JSON responses."""
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    return raw.strip()


# Maximum characters from RFP text sent to LLM
RFP_TEXT_MAX_CHARS = 100000


def extract_requirements_and_entities(text: str) -> dict:
    """Extract and CLASSIFY all document elements into strict categories.

    Classification rules:
    1. Mandatory Requirement (must / shall / required)
    2. Preferred Requirement (should / nice-to-have)
    3. Evaluation Criteria (scoring rules, weights)
    4. Vendor Question (questions asked to vendor)
    5. Pricing Question (cost fields, pricing templates)
    6. Placeholder / Noise (e.g., "Click here to enter text")

    Vendor Questions are NOT requirements.
    Evaluation Criteria are NOT compliance items.
    Placeholders are ignored.
    """
    prompt = f"""You are an expert procurement intelligence analyst.

Your task is to parse the document and classify EACH item into EXACTLY ONE category.

===== CLASSIFICATION RULES =====
1. Mandatory Requirement — uses words like: must, shall, required, mandatory, necessary
2. Preferred Requirement — uses words like: should, nice-to-have, preferred, desirable
3. Evaluation Criteria — scoring rules, weights, point systems, rating criteria
4. Vendor Question — questions directed at the vendor (e.g., "Describe your approach to...")
5. Pricing Question — cost fields, pricing templates, rate cards, budget forms
6. Placeholder / Noise — "Click here to enter text", "N/A", template instructions, boilerplate

===== CRITICAL RULES =====
- Vendor Questions are NOT requirements
- Evaluation Criteria are NOT compliance items
- Placeholders must be identified and ignored
- Do NOT merge categories
- Do NOT assume everything is a requirement

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

    Returns JSON with strict format. Every capability reference uses real
    cap_id, domain, project_summary, certification, client_type from dataset.
    No hallucination, no external knowledge, no invented projects.

    Uses LLM service with automatic fallback and caching.

    Args:
        context: Dict with requirements, capability_matches (with full capability data),
                 compliance_results, budget, deadlines, grounding_report

    Returns:
        dict with proposal sections as JSON
    """
    requirements = context.get("requirements", [])
    capability_matches = context.get("capability_matches", [])
    compliance_results = context.get("compliance_results", [])

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

    # Build compliance mapping (EXACT output from compliance engine)
    compliance_lines = []
    for r in compliance_results:
        status = r.get("status", "UNKNOWN")
        req_text = r.get("requirement", "")
        evidence = r.get("evidence", "NO EVIDENCE")
        compliance_lines.append(f"- requirement: {req_text}\n  status: {status}\n  evidence: {evidence}")
    compliance_text = "\n".join(compliance_lines) if compliance_lines else "NO COMPLIANCE DATA"

    prompt = f"""You are a Senior Enterprise AI Proposal Generation Engine.

===== CRITICAL RULES (NON-NEGOTIABLE) =====
1. DO NOT invent any project, certification, company, or capability.
2. ONLY use evidence provided in the capability records below.
3. DO NOT generate or modify cap_id values.
4. DO NOT use general world knowledge.
5. If data is missing → explicitly say "NO EVIDENCE AVAILABLE".
6. Compliance engine output is the ONLY truth source for PASS/FAIL.

===== HARD DATA BOUNDARY =====
You are ONLY allowed to use these exact fields from capability records:
- cap_id
- domain
- project_summary
- certification
- client_type
- year_completed
- contract_value

You are NOT allowed to:
- create new projects
- rename projects
- merge projects
- infer missing certifications
- assume any missing field

===== VERIFIED CAPABILITY RECORDS ({len(capability_matches)} entries from dataset) =====
{capabilities_text}

===== EXTRACTED REQUIREMENTS =====
{requirements_text}

===== COMPLIANCE ENGINE OUTPUT (DO NOT OVERRIDE) =====
{compliance_text}

===== BUDGET & DEADLINE =====
Budget: {context.get('budget', 'Not specified')}
Deadline: {context.get('deadlines', 'Not specified')}

===== OUTPUT FORMAT (Return ONLY valid JSON) =====

Return this exact JSON structure. No markdown, no code fences, no extra text:

{{
  "proposal": {{
    "executive_summary": "2-3 paragraphs. ONLY reference verified capabilities by cap_id. If no capabilities exist, state NO EVIDENCE AVAILABLE.",
    "technical_approach": "Address each requirement. ONLY cite real cap_id values from the records above. For unmatched requirements, state the gap.",
    "company_experience": [
      {{
        "cap_id": "use EXACT cap_id from record",
        "domain": "use EXACT domain from record",
        "project_summary": "use EXACT project_summary from record",
        "certification": "use EXACT certification from record",
        "client_type": "use EXACT client_type from record",
        "year_completed": "use EXACT year_completed from record"
      }}
    ],
    "compliance_mapping": [
      {{
        "requirement": "exact requirement text",
        "status": "PASS or FAIL from compliance engine — DO NOT change",
        "evidence": "exact evidence from compliance engine"
      }}
    ],
    "conclusion": "Summarize capabilities and gaps honestly. If gaps exist, acknowledge them."
  }}
}}

===== COMPANY EXPERIENCE RULE =====
For EVERY experience mention, you MUST use the exact format above with real cap_id.
DO NOT fabricate "Project 1, Project 42, etc." — ONLY use real cap_id from dataset.
If no capabilities are available, return an empty array: "company_experience": []

===== COMPLIANCE SECTION RULE =====
Use compliance engine output EXACTLY. Do NOT override FAIL to PASS.
If requirement is FAIL, state FAIL clearly. Do NOT justify it as PASS.

===== LANGUAGE RULE =====
- Formal, enterprise-grade language
- Do NOT over-explain contradictions
- Do NOT add defensive statements about "tool limitations"
- Be direct and professional

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
