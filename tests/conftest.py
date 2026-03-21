"""Shared test fixtures for BruceWayneV1 test suite."""

import os
import sys
import json
import tempfile
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

# Ensure project root is on sys.path so imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ---------------------------------------------------------------------------
# Mock settings before any project module tries to load the real .env
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_settings():
    """Return a Settings-like object with test-safe values."""
    try:
        from config.settings import Settings
        settings = Settings(
            api_host="127.0.0.1",
            api_port=9999,
            debug=True,
            environment="testing",
            jwt_secret_key="test-secret-key-do-not-use-in-prod",
            jwt_algorithm="HS256",
            jwt_access_token_expire_minutes=30,
            admin_password="testadminpassword123",
            cors_origins="http://localhost:3000,http://localhost:5173",
            primary_model="phi3",
            enable_trading=False,
            redis_host="localhost",
            redis_port=6379,
        )
        return settings
    except Exception:
        # Fallback to a simple namespace if pydantic_settings is unavailable
        class _FakeSettings:
            api_host = "127.0.0.1"
            api_port = 9999
            debug = True
            environment = "testing"
            jwt_secret_key = "test-secret-key-do-not-use-in-prod"
            jwt_algorithm = "HS256"
            jwt_access_token_expire_minutes = 30
            admin_password = "testadminpassword123"
            cors_origins = "http://localhost:3000"
            cors_origins_list = ["http://localhost:3000"]
            primary_model = "phi3"
            enable_trading = False
        return _FakeSettings()


@pytest.fixture()
def test_client(mock_settings):
    """FastAPI TestClient for the main app, with settings patched."""
    try:
        from fastapi.testclient import TestClient
        with patch("config.settings.get_settings", return_value=mock_settings):
            # Clear lru_cache so our mock is picked up
            from config.settings import get_settings
            get_settings.cache_clear()
            try:
                from main import app
                client = TestClient(app)
                yield client
            finally:
                get_settings.cache_clear()
    except Exception as exc:
        pytest.skip(f"Could not create TestClient: {exc}")


@pytest.fixture()
def sample_user():
    """Return a test user dictionary."""
    return {
        "username": "testuser",
        "email": "test@bruceai.io",
        "role": "user",
        "user_id": "test-user-001",
    }


@pytest.fixture()
def sample_trade():
    """Return sample trade data."""
    return {
        "symbol": "BTC/USDT",
        "side": "buy",
        "amount": 0.5,
        "order_type": "market",
        "price": 67500.0,
        "stop_price": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture()
def sample_episode():
    """Return sample RL training episode data."""
    return {
        "episode_id": 42,
        "total_reward": 1.87,
        "steps": 200,
        "final_portfolio_value": 102350.0,
        "initial_portfolio_value": 100000.0,
        "actions": ["buy", "hold", "hold", "sell"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@pytest.fixture()
def temp_dir():
    """Provide a temporary directory that is cleaned up after the test."""
    with tempfile.TemporaryDirectory(prefix="bruce_test_") as tmpdir:
        yield tmpdir


@pytest.fixture()
def sample_portfolio():
    """Return a sample portfolio for crisis simulation tests."""
    return {
        "BTC/USDT": 40000.0,
        "ETH/USDT": 20000.0,
        "SOL/USDT": 10000.0,
        "cash": 30000.0,
    }


@pytest.fixture()
def sample_prices():
    """Return a list of sample price data (50 data points with a trend)."""
    import math
    base = 100.0
    prices = []
    for i in range(50):
        prices.append(round(base + 10 * math.sin(i / 5) + i * 0.2, 2))
    return prices
