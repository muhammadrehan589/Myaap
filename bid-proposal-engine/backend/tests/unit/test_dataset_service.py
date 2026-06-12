"""Unit tests for dataset_service.py."""

import pytest
from services.dataset_service import get_capability_text


class TestGetCapabilityText:
    """Test capability text generation for embeddings."""

    def test_full_record(self, sample_capability):
        text = get_capability_text(sample_capability)
        assert "Cybersecurity" in text
        assert "Cybersecurity deployment" in text
        assert "ISO 27001" in text
        assert "Federal Govt" in text
        assert "2023" in text

    def test_missing_certification(self):
        record = {
            "domain": "IT",
            "project_summary": "Test project",
            "certification": "N/A",
            "client_type": "Private",
            "year_completed": "2020",
        }
        text = get_capability_text(record)
        assert "N/A" not in text
        assert "IT" in text

    def test_empty_record(self):
        text = get_capability_text({})
        assert "This is a" in text

    def test_natural_language_format(self, sample_capability):
        text = get_capability_text(sample_capability)
        # Should be sentences, not key-value pairs
        assert "This is a" in text
        assert "The team holds" in text
        assert "The client was" in text
        assert "Completed in" in text
