import os
import uuid
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from repositories.proposal_repository import create_proposal

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = "uploads"
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/upload-rfp")
async def upload_rfp(file: UploadFile = File(...)):
    """Upload an RFP document (PDF/DOCX) and store it under a new workspace."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    allowed_extensions = {".pdf", ".doc", ".docx"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {', '.join(allowed_extensions)}"
        )

    # Read file content
    content = await file.read()

    # Enforce file size limit
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {len(content) / (1024*1024):.1f}MB. Maximum allowed: {MAX_FILE_SIZE_MB}MB"
        )

    workspace_id = str(uuid.uuid4())
    workspace_dir = os.path.join(UPLOAD_DIR, workspace_id)
    os.makedirs(workspace_dir, exist_ok=True)

    file_path = os.path.join(workspace_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(content)

    # Create proposal record in database
    try:
        create_proposal(
            workspace_id=workspace_id,
            rfp_filename=file.filename,
        )
    except Exception as e:
        logger.warning(f"Failed to create proposal record: {e}")
        # Continue even if database fails — file is already saved

    return {
        "workspace_id": workspace_id,
        "filename": file.filename,
        "size_mb": round(len(content) / (1024 * 1024), 2),
        "status": "uploaded",
    }
