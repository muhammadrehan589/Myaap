"""Unit tests for validation_service.py."""

import pytest
from services.validation_service import validate_dataset_grounding


class TestValidateDatasetGrounding:
    """Test dataset grounding validation."""

    def test_valid_evidence_passes(self, sample_capabilities):
        evidence = [
            {"requirement": "test", "record_id": "CAP-001", "evidence": "test", "score": 0.8}
        ]
        result = validate_dataset_grounding(evidence, sample_capabilities)

        assert result["status"] == "VERIFIED"
        assert result["total_verified"] == 1
        assert result["total_rejected"] == 0

    def test_empty_record_id_rejected(self, sample_capabilities):
        evidence = [
            {"requirement": "test", "record_id": "", "evidence": "test", "score": 0.5}
        ]
        result = validate_dataset_grounding(evidence, sample_capabilities)

        assert result["status"] == "INSUFFICIENT_EVIDENCE"
        assert result["total_rejected"] == 1

    def test_invalid_record_id_rejected(self, sample_capabilities):
        evidence = [
            {"requirement": "test", "record_id": "FAKE-ID", "evidence": "test", "score": 0.5}
        ]
        result = validate_dataset_grounding(evidence, sample_capabilities)

        assert result["status"] == "INSUFFICIENT_EVIDENCE"
        assert result["total_rejected"] == 1

    def test_empty_project_summary_rejected(self):
        capabilities = [
            {"cap_id": "CAP-001", "domain": "IT", "project_summary": "", "certification": "N/A"}
        ]
        evidence = [
            {"requirement": "test", "record_id": "CAP-001", "evidence": "test", "score": 0.5}
        ]
        result = validate_dataset_grounding(evidence, capabilities)

        assert result["status"] == "INSUFFICIENT_EVIDENCE"

    def test_empty_evidence_list(self, sample_capabilities):
        result = validate_dataset_grounding([], sample_capabilities)

        assert result["status"] == "INSUFFICIENT_EVIDENCE"
        assert result["total_input"] == 0

    def test_mixed_valid_invalid(self, sample_capabilities):
        evidence = [
            {"requirement": "valid", "record_id": "CAP-001", "evidence": "test", "score": 0.8},
            {"requirement": "invalid", "record_id": "", "evidence": "test", "score": 0.5},
        ]
        result = validate_dataset_grounding(evidence, sample_capabilities)

        assert result["status"] == "VERIFIED"
        assert result["total_verified"] == 1
        assert result["total_rejected"] == 1

    def test_verified_includes_capability_data(self, sample_capabilities):
        evidence = [
            {"requirement": "test", "record_id": "CAP-001", "evidence": "test", "score": 0.8}
        ]
        result = validate_dataset_grounding(evidence, sample_capabilities)

        verified = result["verified"][0]
        assert "capability" in verified
        assert verified["capability"]["cap_id"] == "CAP-001"
        assert verified["capability"]["domain"] == "Cybersecurity"
