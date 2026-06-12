"""Proposal ORM model — stores RFP proposals and all associated data."""

import uuid
import json
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from config.database import Base, IS_POSTGRES

if IS_POSTGRES:
    UUID_TYPE = UUID(as_uuid=True)
    JSON_TYPE = JSONB
else:
    UUID_TYPE = String(36)
    JSON_TYPE = Text


class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID_TYPE, nullable=False)
    user_id = Column(UUID_TYPE, nullable=True)
    project_name = Column(String(255))
    rfp_filename = Column(String(255))
    rfp_text = Column(Text)
    extracted_data = Column(JSON_TYPE)
    compliance_data = Column(JSON_TYPE)
    scoring_data = Column(JSON_TYPE)
    proposal_data = Column(JSON_TYPE)
    grounding_report = Column(JSON_TYPE)
    effort_metrics = Column(JSON_TYPE)
    status = Column(String(50), default="draft")  # draft, reviewed, approved, exported
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dict for API responses."""
        def _parse_json(val):
            if val is None:
                return None
            if isinstance(val, str):
                return json.loads(val)
            return val

        return {
            "id": str(self.id),
            "workspace_id": str(self.workspace_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "project_name": self.project_name,
            "rfp_filename": self.rfp_filename,
            "status": self.status,
            "extracted_data": _parse_json(self.extracted_data),
            "compliance_data": _parse_json(self.compliance_data),
            "scoring_data": _parse_json(self.scoring_data),
            "proposal_data": _parse_json(self.proposal_data),
            "grounding_report": _parse_json(self.grounding_report),
            "effort_metrics": _parse_json(self.effort_metrics),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
