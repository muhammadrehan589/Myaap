"""Compliance Result ORM model — stores compliance check results per requirement."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from config.database import Base, IS_POSTGRES

if IS_POSTGRES:
    UUID_TYPE = UUID(as_uuid=True)
else:
    UUID_TYPE = String(36)


class ComplianceResult(Base):
    __tablename__ = "compliance_results"

    id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    proposal_id = Column(UUID_TYPE, nullable=False)
    requirement_id = Column(UUID_TYPE, nullable=True)
    status = Column(String(20), nullable=False)  # PASS, FAIL
    evidence = Column(Text)
    cap_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "proposal_id": str(self.proposal_id),
            "requirement_id": str(self.requirement_id) if self.requirement_id else None,
            "status": self.status,
            "evidence": self.evidence,
            "cap_id": self.cap_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
