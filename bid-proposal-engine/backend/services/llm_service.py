import json
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-2.0-flash"


def extract_requirements_and_entities(text: str) -> dict:
    """Use Gemini to extract requirements, deadlines, budget, and evaluation criteria from RFP text."""
    prompt = f"""You are an expert RFP analyst. Extract structured data from the following RFP document text.

Return ONLY valid JSON (no markdown, no code fences) with this exact structure:
{{
  "requirements": [
    {{
      "text": "requirement description",
      "type": "compliance | technical | experience"
    }}
  ],
  "deadlines": "extracted deadline or 'Not specified'",
  "budget": "extracted budget or 'Not specified'",
  "evaluation_criteria": ["criterion 1", "criterion 2"]
}}

Rules:
- Extract ALL requirements mentioned in the document
- Classify each as compliance, technical, or experience
- Extract dates/deadlines exactly as stated
- Extract budget figures exactly as stated
- Extract evaluation criteria if mentioned
- If information is missing, use "Not specified"

RFP Document Text:
{text[:8000]}"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )
    raw = response.text.strip()

    # Clean markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()

    return json.loads(raw)


def generate_proposal(context: dict) -> str:
    """Use Gemini to generate a structured business proposal from extracted context."""
    requirements_text = "\n".join(
        f"- {r.get('text', r) if isinstance(r, dict) else str(r)}"
        for r in context.get("requirements", [])
    )
    compliance_text = "\n".join(
        f"- {r['requirement']}: {r['status']} — {r.get('evidence', 'N/A')}"
        for r in context.get("compliance_results", [])
    )
    matches_text = "\n".join(
        f"- {m['requirement']} → {m['evidence']} (score: {m['score']})"
        for m in context.get("capability_matches", [])
    )

    prompt = f"""You are a senior proposal writer at a leading technology company. Generate a professional, detailed business proposal based on the following RFP analysis data.

Requirements Extracted:
{requirements_text}

Capability Matches (RAG Results):
{matches_text}

Compliance Results:
{compliance_text}

Budget: {context.get('budget', 'Not specified')}
Deadline: {context.get('deadlines', 'Not specified')}

Generate a structured proposal with these exact sections:

1. EXECUTIVE SUMMARY
A compelling 2-3 paragraph overview of why our company is the ideal partner.

2. TECHNICAL APPROACH
Detailed technical solution addressing each requirement. Reference specific capabilities matched.

3. COMPLIANCE MAPPING
Map each requirement to our capabilities. Address any gaps with mitigation strategies.

4. EXPERIENCE EVIDENCE
Reference relevant past projects and capabilities that demonstrate our qualifications.

5. CONCLUSION
Strong closing statement with value proposition and next steps.

Write in professional business English. Be specific and reference the actual requirements and matches provided. Do not use placeholder text."""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )
    return response.text.strip()
