"""Compliance Service — Deployment-ready procurement intelligence.

Classification-first approach:
1. Classify each requirement into category
2. Apply category-specific evaluation rules
3. Use semantic similarity + domain overlap (never exact match)

Status values (NOT binary):
    - PASS: similarity >= 0.45 (strong semantic alignment)
    - PARTIAL: 0.30 <= similarity < 0.45 (partial match)
    - WEAK: similarity < 0.30 but related domain exists
    - FAIL: no domain relation exists
    - PENDING: submission instructions (not evaluated)
    - NEEDS_GENERATION: technical narratives requiring LLM output

Compliance score = (PASS + 0.5 * PARTIAL + 0.25 * WEAK) / total_evaluated
"""

import logging

logger = logging.getLogger(__name__)

# Requirement classification categories
REQUIREMENT_CATEGORIES = {
    "capability_requirement": "Must deliver or demonstrate capabilities",
    "submission_instruction": "How to format/submit the proposal",
    "technical_narrative": "Requires LLM-generated technical content",
    "compliance_document": "Must provide specific documents/certifications",
    "evaluation_criteria": "Scoring rules and weights",
}

# Match thresholds (deployment-ready rules)
THRESHOLD_PASS = 0.80      # similarity >= 0.80 → PASS
THRESHOLD_PARTIAL = 0.50   # 0.50-0.79 → PARTIAL
THRESHOLD_WEAK = 0.0       # < 0.50 but related domain exists → WEAK MATCH


def _classify_requirement(text: str) -> str:
    """Classify requirement into category based on content analysis."""
    text_lower = text.lower()

    # Submission instructions
    submission_keywords = [
        "submit", "format", "page", "font", "margin", "copy",
        "sealed", "labeled", "binder", "paper", "email",
        "deadline", "no later than", "must be received"
    ]
    if any(kw in text_lower for kw in submission_keywords):
        # Check if it's about submission process, not capability
        if any(kw in text_lower for kw in ["submit", "format", "page", "font", "copy", "sealed", "binder"]):
            return "submission_instruction"

    # Evaluation criteria
    eval_keywords = ["score", "weight", "point", "rating", "evaluate", "criteria"]
    if any(kw in text_lower for kw in eval_keywords) and "%" in text:
        return "evaluation_criteria"

    # Compliance documents
    doc_keywords = ["certificate", "license", "insurance", "form", "exhibit", "attachment"]
    if any(kw in text_lower for kw in doc_keywords):
        return "compliance_document"

    # Technical narratives
    narrative_keywords = ["describe", "explain", "approach", "methodology", "plan", "strategy"]
    if any(kw in text_lower for kw in narrative_keywords):
        return "technical_narrative"

    # Default: capability requirement
    return "capability_requirement"


def _determine_status(score: float, category: str, has_related_domain: bool) -> str:
    """Determine compliance status based on score, category, and domain relation.

    Rules:
        - capability_requirement: PASS/PARTIAL/WEAK/FAIL based on score
        - submission_instruction: PENDING (not evaluated)
        - technical_narrative: NEEDS_GENERATION (requires LLM output)
        - compliance_document: PASS/PARTIAL/FAIL based on score
        - evaluation_criteria: PENDING (not evaluated)
    """
    # Non-evaluated categories
    if category == "submission_instruction":
        return "PENDING"
    if category == "evaluation_criteria":
        return "PENDING"
    if category == "technical_narrative":
        return "NEEDS_GENERATION"

    # Score-based evaluation
    if score >= THRESHOLD_PASS:
        return "PASS"
    elif score >= THRESHOLD_PARTIAL:
        return "PARTIAL"
    elif score >= THRESHOLD_WEAK and has_related_domain:
        return "WEAK"
    else:
        return "FAIL"


def _has_related_domain(top_matches: list[dict]) -> bool:
    """Check if any match has a related domain (not exact, but semantically close)."""
    if not top_matches:
        return False
    # Any match with score > 0.15 indicates some domain relation
    return any(m.get("similarity_score", 0) > 0.15 for m in top_matches)


def check_compliance(
    mandatory_requirements: list[dict],
    preferred_requirements: list[dict],
    rag_matches: list[dict],
) -> dict:
    """Evaluate compliance with classification-first approach.

    1. Classify each requirement
    2. Apply category-specific rules
    3. Compute weighted compliance score

    Returns:
        Dict with compliance_matrix, compliance_score, results, gaps.
    """
    all_requirements = mandatory_requirements + preferred_requirements
    results = []
    gaps = []

    # Counters for compliance matrix
    pass_count = 0
    partial_count = 0
    pending_count = 0
    fail_count = 0
    weak_count = 0
    needs_gen_count = 0

    total_evaluated = 0
    weighted_score_sum = 0.0

    for i, req in enumerate(all_requirements):
        req_text = req.get("text", str(req))
        is_mandatory = i < len(mandatory_requirements)

        # Step 1: Classify the requirement
        category = _classify_requirement(req_text)

        # Step 2: Get RAG match
        match = rag_matches[i] if i < len(rag_matches) else {
            "score": 0.0, "record_id": "", "evidence": "No match",
            "top_matches": [], "best_score": 0.0,
        }

        best_score = match.get("best_score", match.get("score", 0.0))
        top_matches = match.get("top_matches", [])
        has_related = _has_related_domain(top_matches)

        # Step 3: Determine status
        status = _determine_status(best_score, category, has_related)

        # Step 4: Update counters
        if status == "PASS":
            pass_count += 1
            weighted_score_sum += 1.0
            total_evaluated += 1
        elif status == "PARTIAL":
            partial_count += 1
            weighted_score_sum += 0.5
            total_evaluated += 1
        elif status == "WEAK":
            weak_count += 1
            weighted_score_sum += 0.25
            total_evaluated += 1
        elif status == "FAIL":
            fail_count += 1
            total_evaluated += 1
        elif status == "PENDING":
            pending_count += 1
        elif status == "NEEDS_GENERATION":
            needs_gen_count += 1

        # Track gaps
        if status in ("FAIL", "WEAK"):
            gaps.append({
                "requirement": req_text,
                "category": category,
                "status": status,
                "best_score": round(best_score, 4),
                "reason": f"No sufficient capability match (score: {best_score:.4f})"
            })

        logger.info(
            f"[{i+1}/{len(all_requirements)}] "
            f"category={category} | score={best_score:.4f} | "
            f"status={status} | mandatory={is_mandatory}"
        )

        results.append({
            "requirement": req_text,
            "category": category,
            "priority": "mandatory" if is_mandatory else "preferred",
            "top_matches": top_matches[:3],
            "best_score": round(best_score, 4),
            "status": status,
            "evidence": match.get("evidence", ""),
            "record_id": match.get("record_id", ""),
        })

    # Compute compliance score
    if total_evaluated > 0:
        compliance_score = round((weighted_score_sum / total_evaluated) * 100, 1)
    else:
        compliance_score = 0.0

    logger.info(
        f"Compliance: {compliance_score}% | "
        f"PASS={pass_count} PARTIAL={partial_count} WEAK={weak_count} "
        f"FAIL={fail_count} PENDING={pending_count} NEEDS_GEN={needs_gen_count}"
    )

    return {
        "total_requirements": len(all_requirements),
        "total_mandatory": len(mandatory_requirements),
        "total_preferred": len(preferred_requirements),
        "total_evaluated": total_evaluated,
        "pass": pass_count,
        "partial": partial_count,
        "pending": pending_count,
        "fail": fail_count,
        "weak": weak_count,
        "needs_generation": needs_gen_count,
        "score": compliance_score,
        "results": results,
        "gaps": gaps,
    }
