"""Proposal Repository — CRUD operations for proposals table.

Provides database operations for storing and retrieving proposal data.
"""

import json
import logging
from datetime import datetime
from config.database import SessionLocal
from models.proposal import Proposal
from models.requirement import ExtractedRequirement
from models.compliance import ComplianceResult

logger = logging.getLogger(__name__)


def create_proposal(workspace_id: str, project_name: str = None, rfp_filename: str = None) -> dict:
    """Create a new proposal record."""
    db = SessionLocal()
    try:
        proposal = Proposal(
            workspace_id=workspace_id,
            project_name=project_name,
            rfp_filename=rfp_filename,
            status="draft",
        )
        db.add(proposal)
        db.commit()
        db.refresh(proposal)
        logger.info(f"Created proposal {proposal.id} for workspace {workspace_id}")
        return proposal.to_dict()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create proposal: {e}")
        raise
    finally:
        db.close()


def get_proposal_by_workspace(workspace_id: str) -> dict:
    """Get proposal by workspace ID."""
    db = SessionLocal()
    try:
        proposal = db.query(Proposal).filter(Proposal.workspace_id == workspace_id).first()
        return proposal.to_dict() if proposal else None
    finally:
        db.close()


def get_proposal_by_id(proposal_id: str) -> dict:
    """Get proposal by ID."""
    db = SessionLocal()
    try:
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        return proposal.to_dict() if proposal else None
    finally:
        db.close()


def update_proposal(workspace_id: str, data: dict) -> dict:
    """Update proposal with new data."""
    db = SessionLocal()
    try:
        proposal = db.query(Proposal).filter(Proposal.workspace_id == workspace_id).first()
        if not proposal:
            raise ValueError(f"Proposal not found for workspace {workspace_id}")

        for key, value in data.items():
            if hasattr(proposal, key):
                if isinstance(value, (dict, list)):
                    setattr(proposal, key, json.dumps(value))
                else:
                    setattr(proposal, key, value)

        proposal.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(proposal)
        logger.info(f"Updated proposal for workspace {workspace_id}")
        return proposal.to_dict()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update proposal: {e}")
        raise
    finally:
        db.close()


def store_requirements(workspace_id: str, requirements: list[dict]) -> list[dict]:
    """Store extracted requirements for a proposal."""
    db = SessionLocal()
    try:
        proposal = db.query(Proposal).filter(Proposal.workspace_id == workspace_id).first()
        if not proposal:
            raise ValueError(f"Proposal not found for workspace {workspace_id}")

        stored = []
        for req in requirements:
            requirement = ExtractedRequirement(
                proposal_id=proposal.id,
                requirement_text=req.get("text", ""),
                requirement_type=req.get("type", ""),
                compliance_status="PENDING",
            )
            db.add(requirement)
            stored.append(requirement)

        db.commit()
        logger.info(f"Stored {len(stored)} requirements for proposal {proposal.id}")
        return [r.to_dict() for r in stored]
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to store requirements: {e}")
        raise
    finally:
        db.close()


def store_compliance_results(workspace_id: str, results: list[dict]) -> list[dict]:
    """Store compliance check results for a proposal."""
    db = SessionLocal()
    try:
        proposal = db.query(Proposal).filter(Proposal.workspace_id == workspace_id).first()
        if not proposal:
            raise ValueError(f"Proposal not found for workspace {workspace_id}")

        stored = []
        for result in results:
            compliance = ComplianceResult(
                proposal_id=proposal.id,
                status=result.get("status", ""),
                evidence=result.get("evidence", ""),
                cap_id=result.get("record_id"),
            )
            db.add(compliance)
            stored.append(compliance)

        db.commit()
        logger.info(f"Stored {len(stored)} compliance results for proposal {proposal.id}")
        return [c.to_dict() for c in stored]
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to store compliance results: {e}")
        raise
    finally:
        db.close()


def update_proposal_status(workspace_id: str, status: str) -> dict:
    """Update proposal status (draft, reviewed, approved, exported)."""
    return update_proposal(workspace_id, {"status": status})


def list_proposals(limit: int = 50, offset: int = 0) -> list[dict]:
    """List all proposals with pagination."""
    db = SessionLocal()
    try:
        proposals = db.query(Proposal).order_by(Proposal.created_at.desc()).offset(offset).limit(limit).all()
        return [p.to_dict() for p in proposals]
    finally:
        db.close()


def delete_proposal(workspace_id: str) -> bool:
    """Delete a proposal and all associated data."""
    db = SessionLocal()
    try:
        proposal = db.query(Proposal).filter(Proposal.workspace_id == workspace_id).first()
        if not proposal:
            return False

        # Delete associated requirements and compliance results
        db.query(ExtractedRequirement).filter(ExtractedRequirement.proposal_id == proposal.id).delete()
        db.query(ComplianceResult).filter(ComplianceResult.proposal_id == proposal.id).delete()
        db.delete(proposal)
        db.commit()
        logger.info(f"Deleted proposal for workspace {workspace_id}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete proposal: {e}")
        raise
    finally:
        db.close()
