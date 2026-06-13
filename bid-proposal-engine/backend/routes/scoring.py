from fastapi import APIRouter
from pydantic import BaseModel
from services.scoring_service import calculate_win_probability

router = APIRouter()


class ScoreRequest(BaseModel):
    compliance_score: float
    capability_score: float
    experience_score: float
    budget_fit: float


@router.post("/score")
async def score(req: ScoreRequest):
    """Calculate win probability using the mandated weighted formula."""
    result = calculate_win_probability(
        compliance_score=req.compliance_score,
        capability_score=req.capability_score,
        experience_score=req.experience_score,
        budget_fit=req.budget_fit,
    )
    return result
