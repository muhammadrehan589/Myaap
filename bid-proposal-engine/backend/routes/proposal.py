import os
import time
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.pdf_service import extract_text_from_pdf
from services.llm_service import extract_requirements_and_entities, generate_proposal
from services.rag_service import retrieve_matches
from services.compliance_service import check_compliance
from services.validation_service import validate_dataset_grounding
from services.scoring_service import calculate_win_probability
from services.dataset_service import get_bid_history, get_capability_records
from services.utils import parse_budget, derive_domain

logger = logging.getLogger(__name__)
router = APIRouter()

# Industry baseline: manual bid preparation takes 40-80 hours (average 60 hours)
# Our automated pipeline targets 95%+ time reduction
MANUAL_BASELINE_HOURS = 60


class ProposalRequest(BaseModel):
    workspace_id: str


def _calculate_effort_metrics(timings: dict) -> dict:
    """Calculate effort reduction metrics comparing automated vs manual baseline.

    Args:
        timings: Dict with step names and their execution times in seconds.

    Returns:
        Dict with effort metrics and reduction percentage.
    """
    total_seconds = sum(timings.values())
    total_minutes = total_seconds / 60

    # Manual baseline estimates per step (in hours)
    manual_estimates = {
        "document_parsing": 4.0,       # Manual reading and note-taking
        "requirement_extraction": 8.0, # Manual requirement identification
        "capability_matching": 12.0,   # Manual search through past projects
        "compliance_checking": 10.0,   # Manual compliance verification
        "scoring_analysis": 6.0,       # Manual win probability assessment
        "proposal_drafting": 20.0,     # Manual proposal writing
    }

    manual_total_hours = sum(manual_estimates.values())
    automated_total_hours = total_minutes / 60

    reduction_pct = ((manual_total_hours - automated_total_hours) / manual_total_hours) * 100

    return {
        "automated_pipeline_seconds": round(total_seconds, 2),
        "automated_pipeline_minutes": round(total_minutes, 2),
        "manual_baseline_hours": manual_total_hours,
        "effort_reduction_percentage": round(min(reduction_pct, 99.9), 1),
        "time_saved_hours": round(manual_total_hours - automated_total_hours, 2),
        "step_timings": {k: round(v, 2) for k, v in timings.items()},
    }


@router.post("/generate-proposal")
async def generate_proposal_endpoint(req: ProposalRequest):
    """Generate a full AI proposal by chaining: extract → RAG → validation → compliance → scoring → LLM.

    Dataset grounding is enforced before any data reaches the LLM.
    Only verified, dataset-backed capability evidence is used.
    Win probability is computed using the 5-factor heuristic model.
    Effort reduction metrics are tracked and returned.
    """
    timings = {}
    pipeline_start = time.time()

    workspace_dir = os.path.join("uploads", req.workspace_id)
    if not os.path.exists(workspace_dir):
        raise HTTPException(status_code=404, detail="Workspace not found")

    files = os.listdir(workspace_dir)
    if not files:
        raise HTTPException(status_code=404, detail="No file found in workspace")

    filename = files[0]

    # Step 0: Document parsing
    t0 = time.time()
    text = extract_text_from_pdf(req.workspace_id, filename)
    timings["document_parsing"] = time.time() - t0

    if not text:
        raise HTTPException(status_code=422, detail="Could not extract text from document")

    # Step 1: Document classification + requirement extraction
    t1 = time.time()
    try:
        extracted = extract_requirements_and_entities(text)
    except RuntimeError as e:
        logger.error(f"AI extraction failed: {e}")
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {str(e)}")
    timings["requirement_extraction"] = time.time() - t1

    # Extract mandatory and preferred requirements separately
    mandatory_reqs = extracted.get("mandatory_requirements", [])
    preferred_reqs = extracted.get("preferred_requirements", [])

    logger.info(
        f"Document classified as: {extracted.get('document_type', 'Unknown')} "
        f"(confidence: {extracted.get('document_confidence', 0)}) | "
        f"Mandatory: {len(mandatory_reqs)} | Preferred: {len(preferred_reqs)}"
    )

    # Combine all requirements for RAG retrieval
    all_requirement_texts = [r["text"] for r in mandatory_reqs] + [r["text"] for r in preferred_reqs]

    # Step 2: RAG retrieval — capability matching (top-3 per requirement)
    t2 = time.time()
    rag_matches = retrieve_matches(all_requirement_texts, top_k=3)
    timings["capability_matching"] = time.time() - t2

    # Step 3: Dataset grounding validation
    all_capabilities = get_capability_records()
    grounding = validate_dataset_grounding(rag_matches, all_capabilities)

    if grounding["status"] == "INSUFFICIENT_EVIDENCE":
        logger.warning("Proposal blocked: no verified dataset evidence")
        raise HTTPException(
            status_code=422,
            detail={
                "error": "INSUFFICIENT_EVIDENCE",
                "message": grounding["message"],
                "total_requirements": len(all_requirement_texts),
                "rejected_count": grounding["total_rejected"],
            },
        )

    # Step 4: Compliance scoring (mandatory-only affects score)
    t3 = time.time()
    verified_matches = grounding["verified"]
    compliance = check_compliance(mandatory_reqs, preferred_reqs, verified_matches)
    timings["compliance_checking"] = time.time() - t3

    # Step 5: Win probability scoring (3-factor model)
    t4 = time.time()
    win_score = calculate_win_probability(
        mandatory_compliance_score=compliance["score"],
        rag_matches=verified_matches,
        capabilities=all_capabilities,
    )
    timings["scoring_analysis"] = time.time() - t4

    # Step 6: Proposal generation
    t5 = time.time()
    context = {
        "requirements": mandatory_reqs + preferred_reqs,
        "capability_matches": verified_matches,
        "compliance_results": compliance["results"],
        "budget": extracted.get("budget", "Not specified"),
        "deadlines": extracted.get("deadlines", "Not specified"),
        "document_type": extracted.get("document_type", "Unknown"),
        "grounding_report": {
            "total_input": grounding["total_input"],
            "total_verified": grounding["total_verified"],
            "total_rejected": grounding["total_rejected"],
        },
    }

    try:
        proposal_data = generate_proposal(context)
    except RuntimeError as e:
        logger.error(f"AI proposal generation failed: {e}")
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {str(e)}")
    timings["proposal_drafting"] = time.time() - t5

    # Calculate effort reduction metrics
    effort_metrics = _calculate_effort_metrics(timings)
    effort_metrics["total_pipeline_seconds"] = round(time.time() - pipeline_start, 2)

    logger.info(
        f"Proposal generated in {effort_metrics['total_pipeline_seconds']}s "
        f"({effort_metrics['effort_reduction_percentage']}% effort reduction)"
    )

    return {
        "document_type": extracted.get("document_type", "Unknown"),
        "document_confidence": extracted.get("document_confidence", 0),
        "proposal": proposal_data,
        "compliance": {
            "score": compliance["score"],
            "total_mandatory": compliance["total_mandatory"],
            "pass": compliance["pass"],
            "partial": compliance["partial"],
            "fail": compliance["fail"],
            "results": compliance["results"],
        },
        "win_score": win_score,
        "grounding_report": context["grounding_report"],
        "effort_metrics": effort_metrics,
        "extracted_entities": {
            "evaluation_criteria": extracted.get("evaluation_criteria", []),
            "vendor_questions": extracted.get("vendor_questions", []),
            "pricing_questions": extracted.get("pricing_questions", []),
            "noise": extracted.get("noise", []),
        },
    }
