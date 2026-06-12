"""Shared test fixtures for all tests."""

import os
import sys
import pytest

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def sample_capability():
    """Sample capability record for testing."""
    return {
        "cap_id": "CAP-001",
        "domain": "Cybersecurity",
        "project_summary": "Cybersecurity deployment for government client",
        "certification": "ISO 27001",
        "year_completed": "2023",
        "contract_value": "100000",
        "duration_months": 12,
        "client_type": "Federal Govt",
    }


@pytest.fixture
def sample_capabilities():
    """Multiple capability records for testing."""
    return [
        {
            "cap_id": "CAP-001",
            "domain": "Cybersecurity",
            "project_summary": "Cybersecurity deployment for government client",
            "certification": "ISO 27001",
            "year_completed": "2023",
            "contract_value": "100000",
            "duration_months": 12,
            "client_type": "Federal Govt",
        },
        {
            "cap_id": "CAP-002",
            "domain": "Hospital IT",
            "project_summary": "Hospital IT systems deployment",
            "certification": "CE Mark",
            "year_completed": "2022",
            "contract_value": "200000",
            "duration_months": 18,
            "client_type": "International",
        },
        {
            "cap_id": "CAP-003",
            "domain": "Cloud Infrastructure",
            "project_summary": "Cloud infrastructure setup for enterprise",
            "certification": "ISO 27001",
            "year_completed": "2024",
            "contract_value": "150000",
            "duration_months": 6,
            "client_type": "Private Sector",
        },
    ]


@pytest.fixture
def sample_rag_matches():
    """Sample RAG matches for testing."""
    return [
        {
            "requirement": "Must have cybersecurity certification",
            "record_id": "CAP-001",
            "evidence": "Domain: Cybersecurity | ISO 27001",
            "score": 0.75,
            "best_score": 0.75,
            "top_matches": [
                {"cap_id": "CAP-001", "similarity_score": 0.75, "domain": "Cybersecurity"},
                {"cap_id": "CAP-003", "similarity_score": 0.45, "domain": "Cloud Infrastructure"},
            ],
        },
        {
            "requirement": "Cloud deployment experience",
            "record_id": "CAP-003",
            "evidence": "Domain: Cloud Infrastructure",
            "score": 0.60,
            "best_score": 0.60,
            "top_matches": [
                {"cap_id": "CAP-003", "similarity_score": 0.60, "domain": "Cloud Infrastructure"},
            ],
        },
    ]


@pytest.fixture
def sample_bid_history():
    """Sample bid history for testing."""
    return [
        {"bid_id": "BID-001", "sector": "IT Services", "outcome": "Win", "score_pct": 85},
        {"bid_id": "BID-002", "sector": "IT Services", "outcome": "Loss", "score_pct": 60},
        {"bid_id": "BID-003", "sector": "Healthcare", "outcome": "Win", "score_pct": 90},
        {"bid_id": "BID-004", "sector": "Cybersecurity", "outcome": "Win", "score_pct": 88},
        {"bid_id": "BID-005", "sector": "Cybersecurity", "outcome": "Loss", "score_pct": 55},
    ]


@pytest.fixture
def sample_mandatory_requirements():
    """Sample mandatory requirements."""
    return [
        {"text": "Must have ISO 27001 certification", "type": "compliance", "priority": "mandatory"},
        {"text": "Experience with cloud deployment", "type": "technical", "priority": "mandatory"},
    ]


@pytest.fixture
def sample_preferred_requirements():
    """Sample preferred requirements."""
    return [
        {"text": "Hospital IT experience preferred", "type": "experience", "priority": "preferred"},
    ]
