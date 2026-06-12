"""Extracted Requirement ORM model — stores requirements extracted from RFPs."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from config.database import Base, IS_POSTGRES

if IS_POSTGRES:
    UUID_TYPE = UUID(as_uuid=True)
else:
    UUID_TYPE = String(36)


class ExtractedRequirement(Base):
    __tablename__ = "extracted_requirements"

    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    proposal_id = Column(UUID_TYPE, nullable=False)
    requirement_text = Column(Text, nullable=False)
    requirement_type = Column(String(50))  # compliance, technical, experience
    compliance_status = Column(String(20))  # PASS, FAIL, PENDING
    matched_cap_id = Column(String(50), nullable=True)
    match_score = Column(Numeric)
    match_evidence = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "proposal_id": str(self.proposal_id),
            "requirement_text": self.requirement_text,
            "requirement_type": self.requirement_type,
            "compliance_status": self.compliance_status,
            "matched_cap_id": self.matched_cap_id,
            "match_score": float(self.match_score) if self.match_score else None,
            "match_evidence": self.match_evidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
