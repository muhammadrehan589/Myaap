"""Unit tests for utils.py."""

import pytest
from services.utils import parse_budget, derive_domain


class TestParseBudget:
    """Test budget string parsing."""

    def test_dollar_amount(self):
        assert parse_budget("$500,000") == 500000.0

    def test_dollar_with_decimals(self):
        assert parse_budget("$1,234.56") == 1234.56

    def test_number_only(self):
        assert parse_budget("500000") == 500000.0

    def test_not_specified(self):
        assert parse_budget("Not specified") is None

    def test_empty_string(self):
        assert parse_budget("") is None

    def test_none_input(self):
        assert parse_budget(None) is None

    def test_pkr_format(self):
        result = parse_budget("PKR 500,000")
        assert result == 500000.0


class TestDeriveDomain:
    """Test domain derivation from capability matches."""

    def test_with_capability_data(self):
        matches = [
            {"capability": {"domain": "Cybersecurity"}},
            {"capability": {"domain": "Cloud Infrastructure"}},
        ]
        assert derive_domain(matches) == "Cybersecurity"

    def test_empty_matches(self):
        assert derive_domain([]) == ""

    def test_no_capability_key(self):
        matches = [{"record_id": "CAP-001"}]
        assert derive_domain(matches) == ""

    def test_empty_domain(self):
        matches = [{"capability": {"domain": ""}}]
        assert derive_domain(matches) == ""
