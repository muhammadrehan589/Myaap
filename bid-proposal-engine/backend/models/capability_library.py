"""Capability Library ORM model — maps to the Capability Library sheet from TEKROWE workbook.

Includes pgvector embedding column for semantic search (PostgreSQL only).
Falls back to storing embeddings as JSON blobs in SQLite.
"""

from sqlalchemy import Column, String, Numeric, Integer, Text
from config.database import Base, IS_POSTGRES

if IS_POSTGRES:
    from pgvector.sqlalchemy import Vector
    EMBEDDING_TYPE = Vector(384)
else:
    # SQLite fallback: store embedding as JSON text
    EMBEDDING_TYPE = Text


class CapabilityLibrary(Base):
    __tablename__ = "capability_library"

    cap_id = Column(String(50), primary_key=True)
    domain = Column(String(255))
    project_summary = Column(Text)
    certification = Column(String(255))
    year_completed = Column(String(10))
    contract_value = Column(String(100))  # Stored as string (e.g., "PKR 15M")
    duration_months = Column(Integer)
    client_type = Column(String(255))
    embedding = Column(EMBEDDING_TYPE)  # 384-dim vector for semantic search
    embedding_text = Column(Text)       # text representation used for embedding

    def to_dict(self) -> dict:
        """Convert to dict matching the Excel-based format."""
        return {
            "cap_id": self.cap_id,
            "domain": self.domain,
            "project_summary": self.project_summary,
            "certification": self.certification,
            "year_completed": self.year_completed,
            "contract_value": self.contract_value,
            "duration_months": self.duration_months,
            "client_type": self.client_type,
        }
