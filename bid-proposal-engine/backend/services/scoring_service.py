"""Win Probability Service — Deployment-ready scoring.

4-factor weighted model:
    win_probability = 0.40 * compliance_fit
                    + 0.25 * capability_match
                    + 0.20 * past_performance
                    + 0.15 * strategic_fit

Decision tiers:
    > 70 → GO
    40-70 → CONDITIONAL GO
    < 40 → NO-GO

NEVER outputs 0 unless ALL factors are truly zero.
"""

import logging

logger = logging.getLogger(__name__)

# Mandated weights — sum to 1.0
WEIGHT_COMPLIANCE = 0.40
WEIGHT_CAPABILITY = 0.25
WEIGHT_PERFORMANCE = 0.20
WEIGHT_STRATEGIC = 0.15

# Decision thresholds
THRESHOLD_GO = 70
THRESHOLD_CONDITIONAL = 40

# Minimum score floor — never output 0 unless truly no data
MIN_SCORE_FLOOR = 10.0


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    """Constrain a score to the valid 0-100 range. Never returns NaN."""
    if value is None or value != value:  # NaN check
        return 0.0
    return max(low, min(high, value))


def _compute_capability_match(rag_matches: list[dict]) -> tuple[float, str]:
    """Compute capability match strength from RAG retrieval scores.

    Uses average of best similarity scores across all requirements.
    """
    if not rag_matches:
        return 0.0, "No RAG matches available"

    scores = []
    for match in rag_matches:
        score = match.get("best_score", match.get("score", 0.0))
        if score > 0:
            scores.append(score)

    if not scores:
        return 0.0, "No valid similarity scores"

    avg_score = sum(scores) / len(scores)
    # Scale to 0-100 (model produces 0.15-0.65 range)
    scaled = min(avg_score * 150, 100.0)

    return _clamp(scaled), (
        f"{len(scores)} requirements matched, avg similarity: {avg_score:.3f}"
    )


def _compute_past_performance(capabilities: list[dict], rag_matches: list[dict]) -> tuple[float, str]:
    """Compute past performance score from matched capability history.

    Based on: number of matched projects, client diversity, recency.
    """
    if not capabilities:
        return MIN_SCORE_FLOOR, "No capability data - using minimum floor"

    # Get matched cap_ids
    matched_ids = set()
    for match in rag_matches:
        if match.get("record_id"):
            matched_ids.add(match["record_id"])
        for tm in match.get("top_matches", []):
            if tm.get("cap_id"):
                matched_ids.add(tm["cap_id"])

    if not matched_ids:
        return MIN_SCORE_FLOOR, "No matched capabilities for performance analysis"

    matched_caps = [c for c in capabilities if c.get("cap_id") in matched_ids]

    # Project count score (more projects = better, max 10 = 40 points)
    project_count = len(matched_caps)
    project_score = min(project_count / 10.0, 1.0) * 40

    # Client diversity (more types = better, max 4 = 30 points)
    client_types = set(c.get("client_type", "") for c in matched_caps if c.get("client_type"))
    diversity_score = min(len(client_types) / 4.0, 1.0) * 30

    # Year recency (2025 = 30 points)
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
        recency = min((max_year - 2018) / 7.0, 1.0) * 30
    else:
        recency = 15.0

    score = project_score + diversity_score + recency

    return _clamp(score), (
        f"{project_count} projects, {len(client_types)} client types, "
        f"most recent: {max(years) if years else 'N/A'}"
    )


def _compute_strategic_fit(rag_matches: list[dict]) -> tuple[float, str]:
    """Compute strategic fit based on domain coverage breadth.

    More distinct domains matched = broader capability = higher strategic fit.
    """
    if not rag_matches:
        return MIN_SCORE_FLOOR, "No RAG matches available"

    domains = set()
    for match in rag_matches:
        for tm in match.get("top_matches", []):
            if tm.get("domain"):
                domains.add(tm["domain"])

    domain_count = len(domains)
    # Score: more domains = better coverage (max 5 domains = 100)
    score = min(domain_count / 5.0, 1.0) * 100

    return _clamp(score), (
        f"{domain_count} distinct domains: {', '.join(sorted(domains)[:5])}"
    )


def calculate_win_probability(
    compliance_score: float,
    capability_score: float = 0.0,
    rag_matches: list[dict] = None,
    domain: str = "",
    capabilities: list[dict] = None,
) -> dict:
    """Calculate win probability using the 4-factor weighted model.

    Args:
        compliance_score: 0-100 compliance score
        capability_score: 0-100 capability match score (if pre-computed)
        rag_matches: List of RAG match dicts
        domain: Primary domain
        capabilities: List of capability records

    Returns:
        Structured result with score, decision, factors, reasoning.
    """
    rag_matches = rag_matches or []
    capabilities = capabilities or []
    reasoning = []

    # Validate inputs
    compliance_score = _clamp(compliance_score if compliance_score is not None else 0.0)
    reasoning.append(f"Compliance fit: {compliance_score:.1f} (weight {WEIGHT_COMPLIANCE})")

    # Factor 2: Capability match (25%)
    if capability_score > 0:
        capability_clamped = _clamp(capability_score)
    else:
        capability_clamped, cap_reason = _compute_capability_match(rag_matches)
        reasoning.append(f"Capability match: {cap_reason}")
    reasoning.append(f"Capability match: {capability_clamped:.1f} (weight {WEIGHT_CAPABILITY})")

    # Factor 3: Past performance (20%)
    performance_score, perf_reason = _compute_past_performance(capabilities, rag_matches)
    reasoning.append(f"Past performance: {perf_reason} → {performance_score:.1f}")

    # Factor 4: Strategic fit (15%)
    strategic_score, strat_reason = _compute_strategic_fit(rag_matches)
    reasoning.append(f"Strategic fit: {strat_reason} → {strategic_score:.1f}")

    # Weighted sum
    win_probability = (
        (WEIGHT_COMPLIANCE * compliance_score)
        + (WEIGHT_CAPABILITY * capability_clamped)
        + (WEIGHT_PERFORMANCE * performance_score)
        + (WEIGHT_STRATEGIC * strategic_score)
    )

    # Apply minimum floor — never 0 unless truly no data
    if win_probability < MIN_SCORE_FLOOR:
        has_any_data = (
            compliance_score > 0
            or capability_clamped > 0
            or performance_score > MIN_SCORE_FLOOR
            or strategic_score > MIN_SCORE_FLOOR
        )
        if has_any_data:
            win_probability = MIN_SCORE_FLOOR

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
        f"Compliance={compliance_score:.1f} Capability={capability_clamped:.1f} "
        f"Performance={performance_score:.1f} Strategic={strategic_score:.1f}"
    )

    return {
        "win_probability": win_probability,
        "decision": decision,
        "factors": {
            "compliance_fit": round(compliance_score, 1),
            "capability_match": round(capability_clamped, 1),
            "past_performance": round(performance_score, 1),
            "strategic_fit": round(strategic_score, 1),
        },
        "reasoning": reasoning,
    }
