"""Unit tests for compliance_service.py."""

import pytest
from services.compliance_service import (
    check_compliance,
    _determine_match_level,
    _determine_status,
    THRESHOLD_STRONG,
    THRESHOLD_PARTIAL,
)


class TestDetermineMatchLevel:
    """Test match level determination from similarity score."""

    def test_strong_match(self):
        assert _determine_match_level(0.80) == "STRONG"
        assert _determine_match_level(0.75) == "STRONG"
        assert _determine_match_level(1.0) == "STRONG"

    def test_partial_match(self):
        assert _determine_match_level(0.50) == "PARTIAL"
        assert _determine_match_level(0.65) == "PARTIAL"
        assert _determine_match_level(0.74) == "PARTIAL"

    def test_no_match(self):
        assert _determine_match_level(0.0) == "NONE"
        assert _determine_match_level(0.49) == "NONE"
        assert _determine_match_level(0.25) == "NONE"


class TestDetermineStatus:
    """Test compliance status determination."""

    def test_strong_mandatory_pass(self):
        assert _determine_status("STRONG", True) == "PASS"

    def test_strong_preferred_pass(self):
        assert _determine_status("STRONG", False) == "PASS"

    def test_partial_mandatory_partial(self):
        assert _determine_status("PARTIAL", True) == "PARTIAL"

    def test_partial_preferred_partial(self):
        assert _determine_status("PARTIAL", False) == "PARTIAL"

    def test_none_mandatory_fail(self):
        assert _determine_status("NONE", True) == "FAIL"

    def test_none_preferred_weak(self):
        assert _determine_status("NONE", False) == "WEAK"


class TestCheckCompliance:
    """Test full compliance check."""

    def test_all_pass(self, sample_mandatory_requirements, sample_capabilities):
        rag_matches = [
            {"score": 0.80, "best_score": 0.80, "record_id": "CAP-001", "evidence": "test", "top_matches": []},
            {"score": 0.75, "best_score": 0.75, "record_id": "CAP-003", "evidence": "test", "top_matches": []},
        ]
        result = check_compliance(sample_mandatory_requirements, [], rag_matches)

        assert result["pass"] == 2
        assert result["fail"] == 0
        assert result["score"] == 100.0

    def test_all_fail(self, sample_mandatory_requirements):
        rag_matches = [
            {"score": 0.20, "best_score": 0.20, "record_id": "", "evidence": "", "top_matches": []},
            {"score": 0.10, "best_score": 0.10, "record_id": "", "evidence": "", "top_matches": []},
        ]
        result = check_compliance(sample_mandatory_requirements, [], rag_matches)

        assert result["pass"] == 0
        assert result["fail"] == 2
        assert result["score"] == 0.0

    def test_mixed_results(self):
        mandatory = [
            {"text": "Strong requirement", "type": "compliance", "priority": "mandatory"},
            {"text": "Weak requirement", "type": "technical", "priority": "mandatory"},
        ]
        rag_matches = [
            {"score": 0.80, "best_score": 0.80, "record_id": "CAP-001", "evidence": "test", "top_matches": []},
            {"score": 0.30, "best_score": 0.30, "record_id": "", "evidence": "", "top_matches": []},
        ]
        result = check_compliance(mandatory, [], rag_matches)

        assert result["pass"] == 1
        assert result["fail"] == 1
        assert result["score"] == 50.0

    def test_preferred_not_affecting_score(self):
        mandatory = [{"text": "Test", "type": "technical", "priority": "mandatory"}]
        preferred = [{"text": "Nice to have", "type": "technical", "priority": "preferred"}]
        rag_matches = [
            {"score": 0.50, "best_score": 0.50, "record_id": "CAP-001", "evidence": "", "top_matches": []},
            {"score": 0.10, "best_score": 0.10, "record_id": "", "evidence": "", "top_matches": []},
        ]
        result = check_compliance(mandatory, preferred, rag_matches)

        assert result["total_mandatory"] == 1
        assert result["total_preferred"] == 1
        # Score only based on mandatory
        assert result["score"] == 50.0

    def test_empty_requirements(self):
        result = check_compliance([], [], [])
        assert result["total_mandatory"] == 0
        assert result["score"] == 0.0

    def test_partial_match_score(self):
        mandatory = [{"text": "Test", "type": "technical", "priority": "mandatory"}]
        rag_matches = [
            {"score": 0.60, "best_score": 0.60, "record_id": "CAP-001", "evidence": "", "top_matches": []},
        ]
        result = check_compliance(mandatory, [], rag_matches)

        assert result["partial"] == 1
        # partial gets 0.5 weight: (0 + 0.5*1) / 1 = 0.5 = 50%
        assert result["score"] == 50.0
