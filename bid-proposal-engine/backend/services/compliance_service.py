"""Compliance Service — Strict procurement intelligence scoring.

ONLY mandatory requirements count for PASS/FAIL compliance.

Scoring rules:
- similarity >= 0.75 → STRONG MATCH → PASS
- 0.50 <= similarity < 0.75 → PARTIAL MATCH → PARTIAL
- similarity < 0.50 → NO MATCH → FAIL

Formula:
    mandatory_score = (PASS + 0.5 * PARTIAL) / total_mandatory

Preferred requirements are informational only — they do NOT affect compliance score.
"""

import logging

logger = logging.getLogger(__name__)

# Match thresholds
THRESHOLD_STRONG = 0.75   # PASS
THRESHOLD_PARTIAL = 0.50  # PARTIAL


def _determine_match_level(score: float) -> str:
    """Determine match level from similarity score."""
    if score >= THRESHOLD_STRONG:
        return "STRONG"
    elif score >= THRESHOLD_PARTIAL:
        return "PARTIAL"
    return "NONE"


def _determine_status(match_level: str, is_mandatory: bool) -> str:
    """Determine compliance status based on match level and requirement type.

    Rules:
        - STRONG + mandatory → PASS
        - PARTIAL + mandatory → PARTIAL
        - NONE + mandatory → FAIL
        - Any + preferred → informational only (WEAK/PASS)
    """
    if is_mandatory:
        if match_level == "STRONG":
            return "PASS"
        elif match_level == "PARTIAL":
            return "PARTIAL"
        return "FAIL"
    else:
        # Preferred requirements are informational
        if match_level == "STRONG":
            return "PASS"
        elif match_level == "PARTIAL":
            return "PARTIAL"
        return "WEAK"


def check_compliance(
    mandatory_requirements: list[dict],
    preferred_requirements: list[dict],
    rag_matches: list[dict],
) -> dict:
    """Evaluate compliance using strict procurement intelligence rules.

    ONLY mandatory requirements affect the compliance score.
    Preferred requirements are informational only.

    Args:
        mandatory_requirements: List of mandatory requirement dicts with 'text'
        preferred_requirements: List of preferred requirement dicts with 'text'
        rag_matches: Combined RAG matches for all requirements

    Returns:
        Dict with compliance_results, mandatory_score, status counts.
    """
    results = []
    mandatory_pass = 0
    mandatory_partial = 0
    mandatory_fail = 0
    total_mandatory = len(mandatory_requirements)

    # Process mandatory requirements
    for i, req in enumerate(mandatory_requirements):
        req_text = req.get("text", str(req))
        match = rag_matches[i] if i < len(rag_matches) else {
            "score": 0.0, "record_id": "", "evidence": "No match",
            "top_matches": [], "best_score": 0.0,
        }

        best_score = match.get("best_score", match.get("score", 0.0))
        match_level = _determine_match_level(best_score)
        status = _determine_status(match_level, is_mandatory=True)

        if status == "PASS":
            mandatory_pass += 1
        elif status == "PARTIAL":
            mandatory_partial += 1
        else:
            mandatory_fail += 1

        logger.info(
            f"Mandatory [{i+1}/{total_mandatory}]: "
            f"'{req_text[:50]}...' | score={best_score:.4f} | "
            f"match={match_level} | status={status}"
        )

        results.append({
            "requirement": req_text,
            "priority": "mandatory",
            "top_matches": match.get("top_matches", [])[:3],
            "best_score": round(best_score, 4),
            "match_level": match_level,
            "status": status,
            "evidence": match.get("evidence", ""),
            "record_id": match.get("record_id", ""),
        })

    # Process preferred requirements (informational only)
    offset = len(mandatory_requirements)
    for i, req in enumerate(preferred_requirements):
        req_text = req.get("text", str(req))
        match_idx = offset + i
        match = rag_matches[match_idx] if match_idx < len(rag_matches) else {
            "score": 0.0, "record_id": "", "evidence": "No match",
            "top_matches": [], "best_score": 0.0,
        }

        best_score = match.get("best_score", match.get("score", 0.0))
        match_level = _determine_match_level(best_score)
        status = _determine_status(match_level, is_mandatory=False)

        logger.info(
            f"Preferred [{i+1}/{len(preferred_requirements)}]: "
            f"'{req_text[:50]}...' | score={best_score:.4f} | "
            f"match={match_level} | status={status} (informational)"
        )

        results.append({
            "requirement": req_text,
            "priority": "preferred",
            "top_matches": match.get("top_matches", [])[:3],
            "best_score": round(best_score, 4),
            "match_level": match_level,
            "status": status,
            "evidence": match.get("evidence", ""),
            "record_id": match.get("record_id", ""),
        })

    # Compute mandatory compliance score
    # mandatory_score = (PASS + 0.5 * PARTIAL) / total_mandatory
    if total_mandatory > 0:
        mandatory_score = round(
            ((mandatory_pass + 0.5 * mandatory_partial) / total_mandatory) * 100, 1
        )
    else:
        mandatory_score = 0.0

    logger.info(
        f"Compliance: {mandatory_score}% | "
        f"PASS={mandatory_pass} PARTIAL={mandatory_partial} FAIL={mandatory_fail} | "
        f"mandatory={total_mandatory}"
    )

    return {
        "total_mandatory": total_mandatory,
        "total_preferred": len(preferred_requirements),
        "pass": mandatory_pass,
        "partial": mandatory_partial,
        "fail": mandatory_fail,
        "score": mandatory_score,
        "results": results,
    }
