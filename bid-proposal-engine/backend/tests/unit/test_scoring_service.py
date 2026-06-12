"""Unit tests for scoring_service.py."""

import pytest
from services.scoring_service import (
    calculate_win_probability,
    _clamp,
    _compute_capability_coverage,
    _compute_historical_fit,
    THRESHOLD_GO,
    THRESHOLD_CONDITIONAL,
)


class TestClamp:
    """Test value clamping."""

    def test_within_range(self):
        assert _clamp(50.0) == 50.0

    def test_below_minimum(self):
        assert _clamp(-10.0) == 0.0

    def test_above_maximum(self):
        assert _clamp(150.0) == 100.0

    def test_none_returns_zero(self):
        assert _clamp(None) == 0.0

    def test_nan_returns_zero(self):
        assert _clamp(float('nan')) == 0.0

    def test_custom_range(self):
        assert _clamp(5.0, 0.0, 10.0) == 5.0
        assert _clamp(-5.0, 0.0, 10.0) == 0.0
        assert _clamp(15.0, 0.0, 10.0) == 10.0


class TestComputeCapabilityCoverage:
    """Test capability coverage computation."""

    def test_full_coverage(self, sample_rag_matches):
        score, reason = _compute_capability_coverage(sample_rag_matches)
        # Both matches have score >= 0.50
        assert score == 100.0
        assert "2/2" in reason

    def test_no_matches(self):
        score, reason = _compute_capability_coverage([])
        assert score == 0.0
        assert "No RAG matches" in reason

    def test_partial_coverage(self):
        matches = [
            {"best_score": 0.75, "score": 0.75},
            {"best_score": 0.30, "score": 0.30},
        ]
        score, reason = _compute_capability_coverage(matches)
        assert score == 50.0


class TestComputeHistoricalFit:
    """Test historical fit computation."""

    def test_with_capabilities_and_matches(self, sample_capabilities, sample_rag_matches):
        score, reason = _compute_historical_fit(sample_capabilities, sample_rag_matches)
        assert 0.0 <= score <= 100.0
        assert "client types" in reason

    def test_empty_capabilities(self):
        score, reason = _compute_historical_fit([], [])
        assert score == 0.0

    def test_no_matched_ids(self, sample_capabilities):
        matches = [{"record_id": "", "top_matches": []}]
        score, reason = _compute_historical_fit(sample_capabilities, matches)
        assert score == 0.0


class TestCalculateWinProbability:
    """Test win probability calculation."""

    def test_high_score_go(self, sample_rag_matches, sample_capabilities):
        result = calculate_win_probability(
            mandatory_compliance_score=80.0,
            rag_matches=sample_rag_matches,
            capabilities=sample_capabilities,
        )
        assert result["win_probability"] >= THRESHOLD_GO
        assert result["decision"] == "GO"

    def test_medium_score_conditional(self, sample_rag_matches, sample_capabilities):
        result = calculate_win_probability(
            mandatory_compliance_score=50.0,
            rag_matches=sample_rag_matches,
            capabilities=sample_capabilities,
        )
        assert THRESHOLD_CONDITIONAL <= result["win_probability"] < THRESHOLD_GO
        assert result["decision"] == "CONDITIONAL GO"

    def test_low_score_nogo(self):
        result = calculate_win_probability(
            mandatory_compliance_score=0.0,
            rag_matches=[],
            capabilities=[],
        )
        assert result["win_probability"] < THRESHOLD_CONDITIONAL
        assert result["decision"] == "NO-GO"

    def test_none_inputs_handled(self):
        result = calculate_win_probability(
            mandatory_compliance_score=None,
            rag_matches=None,
            capabilities=None,
        )
        assert result["win_probability"] == 0.0
        assert result["decision"] == "NO-GO"

    def test_factors_present(self, sample_rag_matches, sample_capabilities):
        result = calculate_win_probability(
            mandatory_compliance_score=60.0,
            rag_matches=sample_rag_matches,
            capabilities=sample_capabilities,
        )
        factors = result["factors"]
        assert "mandatory_compliance" in factors
        assert "capability_coverage" in factors
        assert "historical_fit" in factors
        assert all(isinstance(v, float) for v in factors.values())

    def test_reasoning_present(self, sample_rag_matches, sample_capabilities):
        result = calculate_win_probability(
            mandatory_compliance_score=60.0,
            rag_matches=sample_rag_matches,
            capabilities=sample_capabilities,
        )
        assert isinstance(result["reasoning"], list)
        assert len(result["reasoning"]) > 0

    def test_score_clamped_0_100(self):
        result = calculate_win_probability(
            mandatory_compliance_score=150.0,
            rag_matches=[],
            capabilities=[],
        )
        assert 0.0 <= result["win_probability"] <= 100.0
