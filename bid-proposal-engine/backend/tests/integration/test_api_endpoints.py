"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from main import app
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "database_type" in data


class TestUploadEndpoint:
    """Test file upload endpoint."""

    def test_upload_pdf(self, client):
        import io
        pdf_content = b"%PDF-1.4 test content"
        response = client.post(
            "/upload-rfp",
            files={"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "workspace_id" in data
        assert data["filename"] == "test.pdf"
        assert data["status"] == "uploaded"

    def test_upload_invalid_extension(self, client):
        import io
        response = client.post(
            "/upload-rfp",
            files={"file": ("test.txt", io.BytesIO(b"content"), "text/plain")},
        )
        assert response.status_code == 400

    def test_upload_no_file(self, client):
        response = client.post("/upload-rfp")
        assert response.status_code == 422


class TestScoreEndpoint:
    """Test scoring endpoint."""

    def test_score_returns_valid_response(self, client):
        response = client.post(
            "/score",
            json={
                "compliance_score": 50.0,
                "capability_score": 60.0,
                "domain": "IT Services",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "win_probability" in data
        assert "decision" in data
        assert "factors" in data
        assert "reasoning" in data
        assert data["decision"] in ["GO", "CONDITIONAL GO", "NO-GO"]

    def test_score_with_zero_inputs(self, client):
        response = client.post(
            "/score",
            json={
                "compliance_score": 0.0,
                "capability_score": 0.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["win_probability"] >= 0.0

    def test_score_missing_fields(self, client):
        response = client.post("/score", json={})
        assert response.status_code == 422


class TestComplianceEndpoint:
    """Test compliance check endpoint."""

    def test_compliance_with_requirements(self, client):
        response = client.post(
            "/compliance-check",
            json={
                "mandatory_requirements": ["Must have ISO 27001 certification"],
                "preferred_requirements": ["Cloud experience preferred"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_mandatory" in data
        assert "pass" in data
        assert "partial" in data
        assert "fail" in data
        assert "score" in data
        assert "win_probability" in data

    def test_compliance_empty_requirements(self, client):
        response = client.post(
            "/compliance-check",
            json={
                "mandatory_requirements": [],
                "preferred_requirements": [],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_mandatory"] == 0


class TestLLMStatsEndpoint:
    """Test LLM statistics endpoint."""

    def test_llm_stats(self, client):
        response = client.get("/llm-stats")
        assert response.status_code == 200
        data = response.json()
        assert "providers_registered" in data
        assert "cache" in data
