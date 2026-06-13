from fastapi import APIRouter
from pydantic import BaseModel
from services.rag_service import retrieve_matches
from services.compliance_service import check_compliance

router = APIRouter()


class ComplianceRequest(BaseModel):
    requirements: list[str]


@router.post("/compliance-check")
async def compliance_check(req: ComplianceRequest):
    """Check compliance by running RAG retrieval and applying threshold logic."""
    rag_matches = retrieve_matches(req.requirements)
    result = check_compliance(req.requirements, rag_matches)
    return result
