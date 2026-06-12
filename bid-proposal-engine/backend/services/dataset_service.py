"""Dataset Service — Database-backed data access layer.

Replaces Excel workbook with PostgreSQL/SQLite database.
Maintains backward compatibility with existing function signatures.
Falls back to Excel if database is not available.
"""

import os
import logging
from config.database import SessionLocal, IS_POSTGRES

logger = logging.getLogger(__name__)

# Excel fallback path
EXCEL_PATH = os.path.join(os.path.dirname(__file__), "..", "data",
                          "Problem#1_Sample_Datasets (TEKROWE).xlsx")

# Cache for database results
_bid_history = None
_capability_library = None
_use_database = True


def _load_from_database():
    """Load data from database."""
    global _bid_history, _capability_library

    try:
        from models.bid_history import BidHistory
        from models.capability_library import CapabilityLibrary

        db = SessionLocal()
        try:
            bids = db.query(BidHistory).all()
            caps = db.query(CapabilityLibrary).all()

            _bid_history = [b.to_dict() for b in bids]
            _capability_library = [c.to_dict() for c in caps]

            logger.info(f"Loaded from database: {len(_bid_history)} bids, {len(_capability_library)} capabilities")
            return True
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Database load failed: {e}")
        return False


def _load_from_excel():
    """Fallback: Load data from Excel workbook."""
    global _bid_history, _capability_library

    import openpyxl

    BID_HISTORY_COLS = [
        "bid_id", "client", "sector", "budget", "score_pct",
        "outcome", "response_time_hrs", "compliance_pct",
        "doc_pages", "gaps_found", "bid_manager", "submission_date"
    ]

    CAPABILITY_COLS = [
        "cap_id", "domain", "project_summary", "certification",
        "year_completed", "contract_value", "duration_months", "client_type"
    ]

    wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True)

    # Bid History
    ws_bh = wb[wb.sheetnames[0]]
    raw_bh = list(ws_bh.iter_rows(values_only=True))
    _bid_history = []
    for row in raw_bh[2:]:
        if not row[0] or str(row[0]).strip() == "":
            continue
        if str(row[0]).strip().lower() in ("bid_id", "bid id", "id"):
            continue
        record = {}
        for i, col in enumerate(BID_HISTORY_COLS):
            val = row[i] if i < len(row) else None
            record[col] = val
        _bid_history.append(record)

    # Capability Library
    ws_cl = wb[wb.sheetnames[1]]
    raw_cl = list(ws_cl.iter_rows(values_only=True))
    _capability_library = []
    for row in raw_cl[2:]:
        if not row[0] or str(row[0]).strip() == "":
            continue
        if str(row[0]).strip().lower() in ("cap_id", "cap id", "id"):
            continue
        record = {}
        for i, col in enumerate(CAPABILITY_COLS):
            val = row[i] if i < len(row) else None
            record[col] = val
        _capability_library.append(record)

    wb.close()
    logger.info(f"Loaded from Excel: {len(_bid_history)} bids, {len(_capability_library)} capabilities")


def _ensure_loaded():
    """Ensure data is loaded (from database or Excel fallback)."""
    global _bid_history, _capability_library, _use_database

    if _bid_history is not None and _capability_library is not None:
        return

    if _use_database:
        if _load_from_database():
            return
        else:
            logger.info("Falling back to Excel data source")
            _use_database = False

    _load_from_excel()


def get_bid_history() -> list[dict]:
    """Return all bid history records."""
    _ensure_loaded()
    return _bid_history


def get_capability_records() -> list[dict]:
    """Return all capability library records."""
    _ensure_loaded()
    return _capability_library


def get_evaluation_taxonomy() -> dict:
    """Return derived taxonomy: sectors, domains, certifications, client types."""
    _ensure_loaded()

    sectors = sorted(set(r["sector"] for r in _bid_history if r.get("sector")))
    domains = sorted(set(r["domain"] for r in _capability_library if r.get("domain")))
    certifications = sorted(set(r["certification"] for r in _capability_library
                                if r.get("certification") and r["certification"] != "N/A"))
    client_types = sorted(set(r["client_type"] for r in _capability_library if r.get("client_type")))

    return {
        "sectors": sectors,
        "domains": domains,
        "certifications": certifications,
        "client_types": client_types,
    }


def get_capability_text(record: dict) -> str:
    """Build a natural-language text representation for embedding.

    Uses sentence structure instead of metadata format to improve
    semantic similarity with requirement text from RFPs.
    """
    domain = record.get("domain", "")
    summary = record.get("project_summary", "")
    cert = record.get("certification", "N/A")
    client = record.get("client_type", "")
    year = record.get("year_completed", "")

    # Build natural language sentence for better embedding quality
    text = f"This is a {domain} project. {summary}."
    if cert and cert != "N/A":
        text += f" The team holds {cert} certification."
    if client:
        text += f" The client was a {client} organization."
    if year:
        text += f" Completed in {year}."

    return text
