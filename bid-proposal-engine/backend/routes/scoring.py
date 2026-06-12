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
    """Calculate win probability using the 3-factor weighted formula.

    Factors: mandatory_compliance (0.60), capability_coverage (0.20),
    historical_fit (0.20).

    Decision: > 70 GO, 40-70 CONDITIONAL GO, < 40 NO-GO
    """
    result = calculate_win_probability(
        mandatory_compliance_score=req.compliance_score,
        capabilities=get_capability_records(),
    )
    return result
