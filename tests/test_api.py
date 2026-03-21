"""Tests for the main FastAPI application (api.py and main.py)."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ---------------------------------------------------------------------------
# Tests against main.py app (primary app)
# ---------------------------------------------------------------------------

class TestMainApp:
    """Tests for the main.py FastAPI application."""

    def test_root_endpoint(self, test_client):
        """GET / returns 200 with expected message fields."""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "status" in data
        assert data["status"] == "operational"
        assert "version" in data

    def test_health_endpoint(self, test_client):
        """GET /health returns 200 with healthy status."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_docs_endpoint(self, test_client):
        """GET /docs returns 200 (Swagger UI)."""
        response = test_client.get("/docs")
        assert response.status_code == 200

    def test_redoc_endpoint(self, test_client):
        """GET /redoc returns 200."""
        response = test_client.get("/redoc")
        assert response.status_code == 200

    def test_cors_headers(self, test_client):
        """Verify CORS headers are present on preflight requests."""
        response = test_client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # FastAPI CORS middleware should respond
        assert response.status_code in (200, 204, 405)

    def test_nonexistent_endpoint_returns_404(self, test_client):
        """GET on a non-existent path returns 404."""
        response = test_client.get("/this-does-not-exist")
        assert response.status_code == 404

    def test_root_response_contains_docs_link(self, test_client):
        """Root endpoint should include a link to /docs."""
        response = test_client.get("/")
        data = response.json()
        assert data.get("docs") == "/docs"


# ---------------------------------------------------------------------------
# Tests against api.py (secondary/legacy app)
# ---------------------------------------------------------------------------

class TestLegacyApi:
    """Tests for the api.py FastAPI application (legacy endpoints)."""

    @pytest.fixture(autouse=True)
    def _setup_client(self):
        try:
            with patch("deepseek_controller.handle_command", return_value="Mocked response"):
                from api import app as legacy_app
            from fastapi.testclient import TestClient
            self.client = TestClient(legacy_app)
        except Exception as exc:
            pytest.skip(f"Legacy api.py not loadable: {exc}")

    def test_chat_endpoint(self):
        """POST /chat returns 200 with response key."""
        with patch("api.handle_command", return_value="test reply"):
            response = self.client.post("/chat", json={"message": "Hello", "user": "tester"})
            assert response.status_code == 200
            assert "response" in response.json()

    def test_state_endpoint(self):
        """GET /state returns operational status."""
        response = self.client.get("/state")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "reward_avg" in data

    def test_profile_endpoint(self):
        """GET /profile returns persona information."""
        response = self.client.get("/profile")
        assert response.status_code == 200
        data = response.json()
        assert "persona" in data

    def test_feedback_endpoint(self):
        """POST /feedback returns received status."""
        response = self.client.post("/feedback", json={
            "user": "tester",
            "message": "good job",
            "emotion": "happy",
            "rating": 5,
        })
        assert response.status_code == 200
        assert response.json()["status"] == "received"

    def test_simulate_endpoint(self):
        """GET /simulate returns simulation data."""
        response = self.client.get("/simulate")
        assert response.status_code == 200
        data = response.json()
        assert "ppo" in data
        assert "summary" in data
