from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from services.rag_service import retrieve_matches
from services.compliance_service import check_compliance
from services.dataset_service import get_capability_records
from services.scoring_service import calculate_win_probability

router = APIRouter()


class ComplianceRequest(BaseModel):
    mandatory_requirements: list[str]
    preferred_requirements: Optional[list[str]] = []


@router.post("/compliance-check")
async def compliance_check(req: ComplianceRequest):
    """Check compliance with classification-first approach.

    1. Classify each requirement (capability/submission/technical/etc.)
    2. Apply category-specific evaluation rules
    3. Compute weighted compliance score
    4. Calculate win probability using 4-factor model
    """
    # Convert to dicts
    mandatory = [{"text": t} for t in req.mandatory_requirements]
    preferred = [{"text": t} for t in req.preferred_requirements]

    # Combine all requirements for RAG retrieval
    all_requirements = req.mandatory_requirements + req.preferred_requirements
    rag_matches = retrieve_matches(all_requirements, top_k=3)

    # Compliance scoring with classification
    compliance = check_compliance(mandatory, preferred, rag_matches)

    # Win probability with 4-factor model
    win_probability = calculate_win_probability(
        compliance_score=compliance["score"],
        rag_matches=rag_matches,
        capabilities=get_capability_records(),
    )

    # Build deployment-ready response
    return {
        "rfp_summary": f"{len(all_requirements)} requirements analyzed",
        "requirements_analysis": compliance["results"],
        "compliance_matrix": {
            "pass": compliance["pass"],
            "partial": compliance["partial"],
            "pending": compliance["pending"],
            "fail": compliance["fail"],
        },
        "compliance_score": compliance["score"],
        "capability_matches": [
            {
                "requirement": r["requirement"],
                "matches": r.get("top_matches", []),
                "best_score": r.get("best_score", 0),
                "status": r["status"],
            }
            for r in compliance["results"]
        ],
        "gaps": compliance.get("gaps", []),
        "win_probability": win_probability["win_probability"],
        "decision": win_probability["decision"],
        "recommendation": _build_recommendation(compliance, win_probability),
    }


def _build_recommendation(compliance: dict, win_probability: dict) -> str:
    """Build a short recommendation string."""
    score = compliance["score"]
    decision = win_probability["decision"]
    gaps = len(compliance.get("gaps", []))
    total = compliance["total_requirements"]

    if decision == "GO":
        return f"Strong alignment with {score:.0f}% compliance across {total} requirements. Proceed with proposal."
    elif decision == "CONDITIONAL GO":
        return f"Moderate alignment ({score:.0f}% compliance). {gaps} gaps identified. Proceed with mitigation plan."
    else:
        return f"Limited alignment ({score:.0f}% compliance). {gaps} gaps found. Significant effort required."
