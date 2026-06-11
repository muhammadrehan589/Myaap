import os
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.pdf_service import extract_text_from_pdf
from services.llm_service import extract_requirements_and_entities, generate_proposal
from services.rag_service import retrieve_matches
from services.compliance_service import check_compliance

logger = logging.getLogger(__name__)
router = APIRouter()


class ProposalRequest(BaseModel):
    workspace_id: str


@router.post("/generate-proposal")
async def generate_proposal_endpoint(req: ProposalRequest):
    """Generate a full AI proposal by chaining: extract → RAG → compliance → LLM generation."""
    workspace_dir = os.path.join("uploads", req.workspace_id)
    if not os.path.exists(workspace_dir):
        raise HTTPException(status_code=404, detail="Workspace not found")

    files = os.listdir(workspace_dir)
    if not files:
        raise HTTPException(status_code=404, detail="No file found in workspace")

    filename = files[0]
    text = extract_text_from_pdf(req.workspace_id, filename)
    if not text:
        raise HTTPException(status_code=422, detail="Could not extract text from document")

    try:
        extracted = extract_requirements_and_entities(text)
    except RuntimeError as e:
        logger.error(f"AI extraction failed: {e}")
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {str(e)}")

    requirement_texts = [r["text"] for r in extracted.get("requirements", [])]

    rag_matches = retrieve_matches(requirement_texts)
    compliance = check_compliance(requirement_texts, rag_matches)

    context = {
        "requirements": extracted.get("requirements", []),
        "capability_matches": rag_matches,
        "compliance_results": compliance["results"],
        "budget": extracted.get("budget", "Not specified"),
        "deadlines": extracted.get("deadlines", "Not specified"),
    }

    try:
        proposal_text = generate_proposal(context)
    except RuntimeError as e:
        logger.error(f"AI proposal generation failed: {e}")
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {str(e)}")

    return {"proposal": proposal_text}
