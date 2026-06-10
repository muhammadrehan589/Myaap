from fastapi import APIRouter
from pydantic import BaseModel
from services.rag_service import retrieve_matches

router = APIRouter()


class RetrieveRequest(BaseModel):
    requirements: list[str]


@router.post("/retrieve-capabilities")
async def retrieve_capabilities(req: RetrieveRequest):
    """Perform RAG-based capability matching against the vector DB."""
    matches = retrieve_matches(req.requirements)
    return {"matches": matches}
