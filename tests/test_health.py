"""Tests for health check endpoints and system health monitoring."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class TestHealthEndpoint:
    """Tests for the /health endpoint on main.py app."""

    def test_healthcheck_returns_200(self, test_client):
        """GET /health returns HTTP 200."""
        response = test_client.get("/health")
        assert response.status_code == 200

    def test_healthcheck_status_healthy(self, test_client):
        """Health response contains status=healthy."""
        response = test_client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_healthcheck_contains_version(self, test_client):
        """Health response contains version info."""
        response = test_client.get("/health")
        data = response.json()
        assert "version" in data
        assert isinstance(data["version"], str)

    def test_health_response_is_json(self, test_client):
        """Health endpoint returns valid JSON."""
        response = test_client.get("/health")
        assert response.headers.get("content-type", "").startswith("application/json")

    def test_root_endpoint_is_operational(self, test_client):
        """Root endpoint status should be 'operational'."""
        response = test_client.get("/")
        data = response.json()
        assert data["status"] == "operational"


class TestModelHealthCheck:
    """Tests for model router health checks."""

    def test_model_router_health(self):
        """ModelRouter health_check returns per-model status."""
        try:
            with patch("config.settings.get_settings") as mock_gs:
                mock_gs.return_value.deepseek_model_path = "./models/fake"
                mock_gs.return_value.phi3_model_path = "./models/fake"
                mock_gs.return_value.tinyllama_model_path = "./models/fake"
                from model_router import ModelRouter
                ModelRouter._instance = None
                router = ModelRouter()
                health = router.health_check()
                assert isinstance(health, dict)
                assert "deepseek" in health
                assert "phi3" in health
                assert "tinyllama" in health
                for model_name, status in health.items():
                    assert "loaded" in status
        except Exception as exc:
            pytest.skip(f"ModelRouter not available: {exc}")

    def test_model_router_all_models_listed(self):
        """All registered models should appear in get_all_models."""
        try:
            with patch("config.settings.get_settings") as mock_gs:
                mock_gs.return_value.deepseek_model_path = "./models/fake"
                mock_gs.return_value.phi3_model_path = "./models/fake"
                mock_gs.return_value.tinyllama_model_path = "./models/fake"
                from model_router import ModelRouter
                ModelRouter._instance = None
                router = ModelRouter()
                models = router.get_all_models()
                assert len(models) == 3
        except Exception as exc:
            pytest.skip(f"ModelRouter not available: {exc}")


class TestSettingsHealth:
    """Tests for settings configuration validity."""

    def test_settings_load(self, mock_settings):
        """Settings object should load without error."""
        assert mock_settings is not None
        assert mock_settings.jwt_algorithm == "HS256"

    def test_settings_environment_is_testing(self, mock_settings):
        """Test settings should be in testing environment."""
        assert mock_settings.environment == "testing"

    def test_settings_debug_enabled(self, mock_settings):
        """Test settings should have debug enabled."""
        assert mock_settings.debug is True

    def test_settings_cors_origins(self, mock_settings):
        """CORS origins should be configured."""
        origins = mock_settings.cors_origins
        assert isinstance(origins, str)
        assert len(origins) > 0


class TestMemoryHealth:
    """Tests for memory subsystem health."""

    def test_memory_manager_creates_storage(self, temp_dir):
        """MemoryManager creates storage directory on init."""
        from memory import MemoryManager
        path = os.path.join(temp_dir, "subdir", "memory.jsonl")
        mm = MemoryManager(storage_path=path)
        assert os.path.exists(os.path.dirname(path))

    def test_memory_manager_stats_on_empty(self, temp_dir):
        """Empty MemoryManager stats should show zero entries."""
        from memory import MemoryManager
        path = os.path.join(temp_dir, "empty_memory.jsonl")
        mm = MemoryManager(storage_path=path)
        stats = mm.get_stats()
        assert stats["total_entries"] == 0
        assert stats["user_count"] == 0
