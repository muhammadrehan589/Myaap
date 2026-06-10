import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.pdf_service import extract_text_from_pdf
from services.llm_service import extract_requirements_and_entities

router = APIRouter()


class ExtractRequest(BaseModel):
    workspace_id: str


@router.post("/extract-requirements")
async def extract_requirements(req: ExtractRequest):
    """Extract requirements, deadlines, budget, and evaluation criteria from uploaded RFP."""
    workspace_dir = os.path.join("uploads", req.workspace_id)
    if not os.path.exists(workspace_dir):
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Find the uploaded file
    files = os.listdir(workspace_dir)
    if not files:
        raise HTTPException(status_code=404, detail="No file found in workspace")

    filename = files[0]
    text = extract_text_from_pdf(req.workspace_id, filename)

    if not text:
        raise HTTPException(status_code=422, detail="Could not extract text from document")

    result = extract_requirements_and_entities(text)
    return result
