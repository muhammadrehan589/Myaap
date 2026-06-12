"""Utility functions for data parsing and extraction.

Single location for cross-cutting concerns like budget parsing and domain extraction.
"""

import re


def parse_budget(budget_str: str) -> float:
    """Extract a numeric budget value from a string like '$500,000' or '500000'.

    Args:
        budget_str: Raw budget string from RFP extraction.

    Returns:
        Float value if parseable, None otherwise.
    """
    if not budget_str or budget_str == "Not specified":
        return None
    cleaned = re.sub(r"[^\d.]", "", budget_str)
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def derive_domain(capability_matches: list[dict]) -> str:
    """Derive the primary domain from verified capability matches.

    Uses the capability data attached by validation_service, not fragile
    string parsing of evidence text.

    Args:
        capability_matches: List of verified matches with 'capability' dict attached.

    Returns:
        Domain string from the first matched capability, or empty string.
    """
    for m in capability_matches:
        cap = m.get("capability", {})
        domain = cap.get("domain", "")
        if domain:
            return domain
    return ""
