"""Win Probability Service — Procurement intelligence scoring.

Deterministic, explainable scoring using compliance results + capability data.

Scoring model:
    base_score = 0.60 * mandatory_score
               + 0.20 * capability_coverage
               + 0.20 * historical_fit

Rules:
- If any value is missing → treat as 0
- Never output null or undefined
- Clamp result between 0 and 100

Decision tiers:
    > 70 → GO
    40-70 → CONDITIONAL GO
    < 40 → NO-GO

Dependency Rule: This service does NOT import dataset_service directly.
All data is injected via function parameters by the route layer.
"""

import logging

logger = logging.getLogger(__name__)

# Mandated weights — sum to 1.0
WEIGHT_MANDATORY = 0.60
WEIGHT_CAPABILITY = 0.20
WEIGHT_HISTORICAL = 0.20

# Decision thresholds
THRESHOLD_GO = 70
THRESHOLD_CONDITIONAL = 40


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    """Constrain a score to the valid 0-100 range. Never returns NaN."""
    if value is None or value != value:  # NaN check
        return 0.0
    return max(low, min(high, value))


def _compute_capability_coverage(rag_matches: list[dict]) -> tuple[float, str]:
    """Compute capability coverage based on match quality.

    Measures what percentage of requirements have at least a PARTIAL match.
    """
    if not rag_matches:
        return 0.0, "No RAG matches available"

    total = len(rag_matches)
    matched = sum(1 for m in rag_matches if m.get("best_score", m.get("score", 0)) >= 0.50)

    coverage = (matched / total) * 100 if total > 0 else 0.0

    return _clamp(coverage), (
        f"{matched}/{total} requirements have PARTIAL+ match"
    )


def _compute_historical_fit(capabilities: list[dict], rag_matches: list[dict]) -> tuple[float, str]:
    """Compute historical fit based on matched capabilities diversity.

    Measures client type diversity and year recency of matched capabilities.
    """
    if not capabilities:
        return 0.0, "No capability data"

    # Get matched cap_ids
    matched_ids = set()
    for match in rag_matches:
        if match.get("record_id"):
            matched_ids.add(match["record_id"])
        for tm in match.get("top_matches", []):
            if tm.get("cap_id"):
                matched_ids.add(tm["cap_id"])

    if not matched_ids:
        return 0.0, "No matched capabilities"

    matched_caps = [c for c in capabilities if c.get("cap_id") in matched_ids]

    # Client type diversity (max 4 types = 50 points)
    client_types = set(c.get("client_type", "") for c in matched_caps if c.get("client_type"))
    client_diversity = min(len(client_types) / 4.0, 1.0) * 50

    # Year recency (2025 = 50 points)
    years = []
    for c in matched_caps:
        yr = c.get("year_completed")
        if yr:
            try:
                years.append(int(yr))
            except (ValueError, TypeError):
                pass

    if years:
        max_year = max(years)
        recency = min((max_year - 2018) / 7.0, 1.0) * 50
    else:
        recency = 0.0

    score = client_diversity + recency

    return _clamp(score), (
        f"{len(client_types)} client types, "
        f"most recent: {max(years) if years else 'N/A'}"
    )


def calculate_win_probability(
    mandatory_compliance_score: float,
    rag_matches: list[dict] = None,
    capabilities: list[dict] = None,
) -> dict:
    """Calculate win probability using the mandated 3-factor formula.

    base_score = 0.60 * mandatory_score
               + 0.20 * capability_coverage
               + 0.20 * historical_fit

    Args:
        mandatory_compliance_score: 0-100 compliance score (mandatory only)
        rag_matches: List of RAG match dicts (for capability coverage)
        capabilities: List of capability records (for historical fit)

    Returns:
        Structured result with score, decision, factors, reasoning.
    """
    rag_matches = rag_matches or []
    capabilities = capabilities or []
    reasoning = []

    # Validate inputs (prevent NaN/undefined)
    mandatory_compliance_score = _clamp(mandatory_compliance_score if mandatory_compliance_score is not None else 0.0)
    reasoning.append(f"Mandatory compliance: {mandatory_compliance_score:.1f} (weight {WEIGHT_MANDATORY})")

    # Factor 2: Capability coverage (20%)
    capability_score, capability_reason = _compute_capability_coverage(rag_matches)
    reasoning.append(f"Capability coverage: {capability_reason} → {capability_score:.1f}")

    # Factor 3: Historical fit (20%)
    historical_score, historical_reason = _compute_historical_fit(capabilities, rag_matches)
    reasoning.append(f"Historical fit: {historical_reason} → {historical_score:.1f}")

    # Weighted sum
    win_probability = (
        (WEIGHT_MANDATORY * mandatory_compliance_score)
        + (WEIGHT_CAPABILITY * capability_score)
        + (WEIGHT_HISTORICAL * historical_score)
    )
    win_probability = round(_clamp(win_probability), 1)

    # Decision
    if win_probability > THRESHOLD_GO:
        decision = "GO"
    elif win_probability >= THRESHOLD_CONDITIONAL:
        decision = "CONDITIONAL GO"
    else:
        decision = "NO-GO"

    reasoning.append(
        f"Final: {win_probability:.1f} → {decision}"
    )

    logger.info(
        f"Win Probability: {win_probability}% | Decision: {decision} | "
        f"Mandatory={mandatory_compliance_score:.1f} Capability={capability_score:.1f} "
        f"Historical={historical_score:.1f}"
    )

    return {
        "win_probability": win_probability,
        "decision": decision,
        "factors": {
            "mandatory_compliance": round(mandatory_compliance_score, 1),
            "capability_coverage": round(capability_score, 1),
            "historical_fit": round(historical_score, 1),
        },
        "reasoning": reasoning,
    }
