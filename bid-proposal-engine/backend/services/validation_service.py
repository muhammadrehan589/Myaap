"""Validation Service — Dataset grounding enforcement for proposal generation.

Ensures NO hallucinated projects, invented certifications, fake companies,
or external knowledge enters the proposal generation pipeline.

Every capability reference MUST be backed by a verified dataset entry.

Dependency Rule: This service does NOT import dataset_service directly.
All data is injected via function parameters by the route layer.
"""

import logging

logger = logging.getLogger(__name__)


def validate_dataset_grounding(evidence_list: list[dict], capabilities: list[dict]) -> dict:
    """Validate that every evidence entry is grounded in the dataset.

    For each capability reference, ALL three conditions must hold:
      1. record_id exists and is non-empty
      2. record_id matches an actual cap_id in the dataset
      3. The matched record contains a non-empty project_summary

    Verified entries include the FULL capability record from the dataset
    so the proposal generator has access to all fields (cap_id, domain,
    project_summary, certification, client_type, year_completed, contract_value).

    Args:
        evidence_list: List of RAG match dicts, each with keys:
                       requirement, record_id, evidence, score

    Returns:
        If valid evidence exists:
            {
              "status": "VERIFIED",
              "verified": [...filtered evidence with full capability data...],
              "rejected": [...rejected entries with reasons...],
              "total_input": int,
              "total_verified": int,
              "total_rejected": int
            }
        If NO valid evidence exists:
            {
              "status": "INSUFFICIENT_EVIDENCE",
              "message": "No valid capability matches found in dataset",
              "rejected": [...],
              "total_input": int,
              "total_verified": 0,
              "total_rejected": int
            }
    """
    if not evidence_list:
        logger.warning("Validation called with empty evidence list")
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "message": "No valid capability matches found in dataset",
            "rejected": [],
            "total_input": 0,
            "total_verified": 0,
            "total_rejected": 0,
        }

    # Build a lookup of valid cap_ids from injected capabilities
    valid_cap_ids = {cap["cap_id"] for cap in capabilities}
    cap_lookup = {cap["cap_id"]: cap for cap in capabilities}

    verified = []
    rejected = []

    for entry in evidence_list:
        record_id = entry.get("record_id", "")
        requirement = entry.get("requirement", "unknown")

        # Condition 1: record_id must exist and be non-empty
        if not record_id or str(record_id).strip() == "":
            reason = "Missing or empty record_id"
            logger.warning(f"REJECTED [{requirement}]: {reason}")
            rejected.append({**entry, "_rejection_reason": reason})
            continue

        # Condition 2: record_id must match an actual cap_id in the dataset
        if record_id not in valid_cap_ids:
            reason = f"record_id '{record_id}' not found in dataset"
            logger.warning(f"REJECTED [{requirement}]: {reason}")
            rejected.append({**entry, "_rejection_reason": reason})
            continue

        # Condition 3: matched record must contain a non-empty project_summary
        matched_record = cap_lookup[record_id]
        project_summary = matched_record.get("project_summary", "")
        if not project_summary or str(project_summary).strip() == "":
            reason = f"Record '{record_id}' has no project_summary in dataset"
            logger.warning(f"REJECTED [{requirement}]: {reason}")
            rejected.append({**entry, "_rejection_reason": reason})
            continue

        # All conditions passed — attach full capability record from dataset
        verified_entry = {
            **entry,
            "capability": {
                "cap_id": matched_record["cap_id"],
                "domain": matched_record.get("domain", ""),
                "project_summary": matched_record.get("project_summary", ""),
                "certification": matched_record.get("certification", "N/A"),
                "client_type": matched_record.get("client_type", ""),
                "year_completed": matched_record.get("year_completed", ""),
                "contract_value": matched_record.get("contract_value", ""),
            }
        }
        verified.append(verified_entry)

    total_input = len(evidence_list)
    total_verified = len(verified)
    total_rejected = len(rejected)

    logger.info(
        f"Dataset grounding validation: {total_input} input → "
        f"{total_verified} verified, {total_rejected} rejected"
    )

    if total_verified == 0:
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "message": "No valid capability matches found in dataset",
            "rejected": rejected,
            "total_input": total_input,
            "total_verified": 0,
            "total_rejected": total_rejected,
        }

    return {
        "status": "VERIFIED",
        "verified": verified,
        "rejected": rejected,
        "total_input": total_input,
        "total_verified": total_verified,
        "total_rejected": total_rejected,
    }
