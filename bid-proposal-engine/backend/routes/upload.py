import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter()

UPLOAD_DIR = "uploads"


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

    workspace_id = str(uuid.uuid4())
    workspace_dir = os.path.join(UPLOAD_DIR, workspace_id)
    os.makedirs(workspace_dir, exist_ok=True)

    file_path = os.path.join(workspace_dir, file.filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "workspace_id": workspace_id,
        "filename": file.filename,
        "status": "uploaded",
    }
