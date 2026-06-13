"""Win Probability Service — Dataset-driven scoring using Bid History.

Uses historical bid records from the Excel workbook to derive:
- Historical win rate
- Average compliance % of winning bids
- Average score of winning bids
- Budget-fit analysis

Combined with the mandated weighted formula for final prediction.
"""

from services.dataset_service import get_bid_history


def _get_historical_stats() -> dict:
    """Compute statistics from the Bid History sheet."""
    bids = get_bid_history()

    wins = [b for b in bids if b["outcome"] == "Win"]
    losses = [b for b in bids if b["outcome"] == "Loss"]

    win_rate = len(wins) / len(bids) * 100 if bids else 0

    avg_win_score = sum(b["score_pct"] for b in wins) / len(wins) if wins else 0
    avg_win_compliance = sum(b["compliance_pct"] for b in wins) / len(wins) if wins else 0
    avg_win_gaps = sum(b["gaps_found"] for b in wins) / len(wins) if wins else 0

    avg_loss_score = sum(b["score_pct"] for b in losses) / len(losses) if losses else 0
    avg_loss_compliance = sum(b["compliance_pct"] for b in losses) / len(losses) if losses else 0

    return {
        "total_bids": len(bids),
        "total_wins": len(wins),
        "total_losses": len(losses),
        "win_rate": round(win_rate, 1),
        "avg_win_score": round(avg_win_score, 1),
        "avg_win_compliance": round(avg_win_compliance, 1),
        "avg_win_gaps": round(avg_win_gaps, 1),
        "avg_loss_score": round(avg_loss_score, 1),
        "avg_loss_compliance": round(avg_loss_compliance, 1),
    }


def calculate_win_probability(
    compliance_score: float,
    capability_score: float,
    experience_score: float,
    budget_fit: float,
) -> dict:
    """Calculate win probability using the mandated weighted formula.

    Formula:
        win_probability = 0.4 * compliance + 0.3 * capability + 0.2 * experience + 0.1 * budget_fit

    Decision:
        >= 70 → GO
        < 70  → NO-GO

    Enriched with historical bid statistics from the dataset.
    """
    win_probability = (
        (0.4 * compliance_score)
        + (0.3 * capability_score)
        + (0.2 * experience_score)
        + (0.1 * budget_fit)
    )
    win_probability = round(win_probability, 1)

    decision = "GO" if win_probability >= 70 else "NO-GO"

    # Enrich with historical context
    stats = _get_historical_stats()

    return {
        "win_probability": win_probability,
        "decision": decision,
        "historical_context": {
            "total_bids_analyzed": stats["total_bids"],
            "historical_win_rate": stats["win_rate"],
            "avg_winning_score": stats["avg_win_score"],
            "avg_winning_compliance": stats["avg_win_compliance"],
            "avg_winning_gaps": stats["avg_win_gaps"],
        },
    }
