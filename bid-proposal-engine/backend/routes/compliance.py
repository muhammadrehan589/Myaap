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
    """Check compliance using strict procurement intelligence rules.

    ONLY mandatory requirements affect compliance score.
    Preferred requirements are informational only.

    Runs RAG retrieval for top-3 matches per requirement.
    Computes win probability using the 3-factor model.
    """
    # Convert to dicts
    mandatory = [{"text": t} for t in req.mandatory_requirements]
    preferred = [{"text": t} for t in req.preferred_requirements]

    # Combine all requirements for RAG retrieval
    all_requirements = req.mandatory_requirements + req.preferred_requirements
    rag_matches = retrieve_matches(all_requirements, top_k=3)

    # Compliance scoring (mandatory-only)
    compliance = check_compliance(mandatory, preferred, rag_matches)

    # Win probability
    win_probability = calculate_win_probability(
        mandatory_compliance_score=compliance["score"],
        rag_matches=rag_matches,
        capabilities=get_capability_records(),
    )

    return {
        **compliance,
        "win_probability": win_probability,
    }
