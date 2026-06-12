from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from services.scoring_service import calculate_win_probability
from services.dataset_service import get_capability_records

router = APIRouter()


class ScoreRequest(BaseModel):
    compliance_score: float
    capability_score: float
    domain: str = ""
    rfp_budget: Optional[float] = None


@router.post("/score")
async def score(req: ScoreRequest):
    """Calculate win probability using the 4-factor weighted formula.

    Factors: compliance (0.50), capability_match (0.25),
    domain_relevance (0.15), historical_diversity (0.10).

    Decision: >= 70 GO, 40-69 CONDITIONAL GO, < 40 NO-GO
    """
    result = calculate_win_probability(
        compliance_score=req.compliance_score,
        capability_score=req.capability_score,
        domain=req.domain,
        capabilities=get_capability_records(),
    )
    return result
