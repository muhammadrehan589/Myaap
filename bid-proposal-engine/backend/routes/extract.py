import os
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.pdf_service import extract_text_from_pdf
from services.llm_service import extract_requirements_and_entities

logger = logging.getLogger(__name__)
router = APIRouter()


class ExtractRequest(BaseModel):
    workspace_id: str


@router.post("/extract-requirements")
async def extract_requirements(req: ExtractRequest):
    """Extract requirements, deadlines, budget, and evaluation criteria from uploaded RFP."""
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
        result = extract_requirements_and_entities(text)
        return result
    except RuntimeError as e:
        logger.error(f"AI extraction failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"AI service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")
