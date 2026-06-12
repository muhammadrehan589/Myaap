"""Bid History ORM model — maps to the Bid History sheet from TEKROWE workbook."""

from sqlalchemy import Column, String, Numeric, Integer
from config.database import Base


class BidHistory(Base):
    __tablename__ = "bid_history"

    bid_id = Column(String(50), primary_key=True)
    client = Column(String(255))
    sector = Column(String(255))
    budget = Column(String(100))  # Stored as string (e.g., "PKR 22M")
    score_pct = Column(Numeric)
    outcome = Column(String(20))  # 'Win' or 'Loss'
    response_time_hrs = Column(Numeric)
    compliance_pct = Column(Numeric)
    doc_pages = Column(Integer)
    gaps_found = Column(String(255))
    bid_manager = Column(String(255))
    submission_date = Column(String(50))

    def to_dict(self) -> dict:
        """Convert to dict matching the Excel-based format."""
        return {
            "bid_id": self.bid_id,
            "client": self.client,
            "sector": self.sector,
            "budget": self.budget,
            "score_pct": self.score_pct,
            "outcome": self.outcome,
            "response_time_hrs": self.response_time_hrs,
            "compliance_pct": self.compliance_pct,
            "doc_pages": self.doc_pages,
            "gaps_found": self.gaps_found,
            "bid_manager": self.bid_manager,
            "submission_date": self.submission_date,
        }
