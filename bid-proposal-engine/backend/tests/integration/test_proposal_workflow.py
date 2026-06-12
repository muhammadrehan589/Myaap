"""Integration tests for full proposal generation workflow."""

import pytest
import io
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from main import app
    return TestClient(app)


@pytest.fixture
def uploaded_workspace(client):
    """Upload a test PDF and return workspace_id."""
    pdf_content = b"%PDF-1.4 test content for proposal generation"
    response = client.post(
        "/upload-rfp",
        files={"file": ("test_rfp.pdf", io.BytesIO(pdf_content), "application/pdf")},
    )
    assert response.status_code == 200
    return response.json()["workspace_id"]


class TestFullProposalWorkflow:
    """Test the complete proposal generation pipeline."""

    def test_upload_creates_workspace(self, client):
        pdf_content = b"%PDF-1.4 test"
        response = client.post(
            "/upload-rfp",
            files={"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "workspace_id" in data
        assert len(data["workspace_id"]) > 0

    def test_compliance_returns_structured_data(self, client):
        response = client.post(
            "/compliance-check",
            json={
                "mandatory_requirements": [
                    "Must have ISO certification",
                    "Cloud deployment required",
                ],
                "preferred_requirements": [
                    "Healthcare experience preferred",
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "total_mandatory" in data
        assert "total_preferred" in data
        assert "pass" in data
        assert "partial" in data
        assert "fail" in data
        assert "score" in data
        assert "results" in data
        assert "win_probability" in data

        # Verify results match input counts
        assert data["total_mandatory"] == 2
        assert data["total_preferred"] == 1
        assert len(data["results"]) == 3

        # Verify mandatory results have correct priority
        mandatory_results = [r for r in data["results"] if r["priority"] == "mandatory"]
        assert len(mandatory_results) == 2

        # Verify preferred results have correct priority
        preferred_results = [r for r in data["results"] if r["priority"] == "preferred"]
        assert len(preferred_results) == 1

    def test_score_returns_valid_decision(self, client):
        response = client.post(
            "/score",
            json={
                "compliance_score": 60.0,
                "capability_score": 70.0,
                "domain": "IT Services",
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert "win_probability" in data
        assert "decision" in data
        assert "factors" in data
        assert "reasoning" in data

        # Verify decision is valid
        assert data["decision"] in ["GO", "CONDITIONAL GO", "NO-GO"]

        # Verify score is in valid range
        assert 0.0 <= data["win_probability"] <= 100.0

        # Verify factors are present
        factors = data["factors"]
        assert "mandatory_compliance" in factors
        assert "capability_coverage" in factors
        assert "historical_fit" in factors

    def test_rag_returns_top_matches(self, client):
        response = client.post(
            "/retrieve-capabilities",
            json={"requirements": ["cybersecurity certification", "cloud deployment"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "matches" in data
        assert len(data["matches"]) == 2

        # Each match should have required fields
        for match in data["matches"]:
            assert "requirement" in match
            assert "score" in match
            assert "top_matches" in match
            assert len(match["top_matches"]) <= 3

    def test_proposal_generation_workflow(self, client):
        """Test the full proposal generation pipeline with real PDF."""
        import os
        pdf_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "test_rfp.pdf"
        )
        if not os.path.exists(pdf_path):
            pytest.skip("test_rfp.pdf not found")

        with open(pdf_path, "rb") as f:
            response = client.post(
                "/upload-rfp",
                files={"file": ("test_rfp.pdf", f, "application/pdf")},
            )
        assert response.status_code == 200
        workspace_id = response.json()["workspace_id"]

        response = client.post(
            "/generate-proposal",
            json={"workspace_id": workspace_id},
        )

        # Should return 200 or 503 (if LLM unavailable)
        assert response.status_code in [200, 503, 422]

        if response.status_code == 200:
            data = response.json()

            # Verify top-level structure
            assert "document_type" in data
            assert "proposal" in data
            assert "compliance" in data
            assert "win_score" in data
            assert "effort_metrics" in data

            # Verify compliance structure
            compliance = data["compliance"]
            assert "score" in compliance
            assert "total_mandatory" in compliance
            assert "pass" in compliance
            assert "fail" in compliance

            # Verify win score structure
            win_score = data["win_score"]
            assert "win_probability" in win_score
            assert "decision" in win_score
            assert win_score["decision"] in ["GO", "CONDITIONAL GO", "NO-GO"]

            # Verify effort metrics
            metrics = data["effort_metrics"]
            assert "total_pipeline_seconds" in metrics
            assert "effort_reduction_percentage" in metrics

    def test_nonexistent_workspace_returns_404(self, client):
        response = client.post(
            "/generate-proposal",
            json={"workspace_id": "nonexistent-id"},
        )
        assert response.status_code == 404
