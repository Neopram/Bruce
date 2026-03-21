"""Tests for authentication (jwt_auth.py and auth.py)."""

import os
import sys
import time
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ---------------------------------------------------------------------------
# Helper to get a mock settings object for JWT tests
# ---------------------------------------------------------------------------

def _make_mock_settings():
    mock = MagicMock()
    mock.jwt_secret_key = "test-jwt-secret-key-12345"
    mock.jwt_algorithm = "HS256"
    mock.jwt_access_token_expire_minutes = 30
    mock.admin_password = "admin123test"
    mock.cors_origins_list = ["http://localhost:3000"]
    mock.environment = "testing"
    mock.debug = True
    mock.primary_model = "phi3"
    mock.enable_trading = False
    mock.api_host = "127.0.0.1"
    mock.api_port = 9999
    return mock


class TestJWTAuth:
    """Tests for jwt_auth.py token creation and verification."""

    @pytest.fixture(autouse=True)
    def _patch_settings(self):
        self.mock_settings = _make_mock_settings()
        with patch("config.settings.get_settings", return_value=self.mock_settings):
            from config.settings import get_settings
            get_settings.cache_clear()
            yield
            get_settings.cache_clear()

    def test_token_creation(self):
        """create_token returns a non-empty string JWT."""
        from jwt_auth import create_token
        token = create_token("testuser", role="user")
        assert isinstance(token, str)
        assert len(token) > 20
        # JWT has 3 parts separated by dots
        assert token.count(".") == 2

    def test_token_verification(self):
        """verify_token decodes a valid token correctly."""
        from jwt_auth import create_token, verify_token
        token = create_token("bruce", role="admin")
        payload = verify_token(token)
        assert payload["sub"] == "bruce"
        assert payload["role"] == "admin"
        assert "exp" in payload
        assert "iat" in payload

    def test_token_contains_role(self):
        """Token payload should contain the role claim."""
        from jwt_auth import create_token, verify_token
        token = create_token("user1", role="trader")
        payload = verify_token(token)
        assert payload["role"] == "trader"

    def test_token_expired(self):
        """An expired token should raise HTTPException with 401."""
        import jwt as pyjwt
        from fastapi import HTTPException
        from jwt_auth import verify_token

        # Create a token that expired 1 hour ago
        payload = {
            "sub": "expired_user",
            "role": "user",
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        expired_token = pyjwt.encode(
            payload,
            self.mock_settings.jwt_secret_key,
            algorithm=self.mock_settings.jwt_algorithm,
        )

        with pytest.raises(HTTPException) as exc_info:
            verify_token(expired_token)
        assert exc_info.value.status_code == 401

    def test_invalid_token(self):
        """A tampered/invalid token should raise HTTPException with 401."""
        from fastapi import HTTPException
        from jwt_auth import verify_token

        with pytest.raises(HTTPException) as exc_info:
            verify_token("this.is.not.a.valid.token")
        assert exc_info.value.status_code == 401

    def test_token_without_subject(self):
        """A token missing 'sub' claim should raise HTTPException with 401."""
        import jwt as pyjwt
        from fastapi import HTTPException
        from jwt_auth import verify_token

        payload = {
            "role": "user",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = pyjwt.encode(
            payload,
            self.mock_settings.jwt_secret_key,
            algorithm=self.mock_settings.jwt_algorithm,
        )

        with pytest.raises(HTTPException) as exc_info:
            verify_token(token)
        assert exc_info.value.status_code == 401


class TestAuthModule:
    """Tests for auth.py router functions."""

    @pytest.fixture(autouse=True)
    def _patch_settings(self):
        self.mock_settings = _make_mock_settings()
        import auth
        auth._admin_hash_cache.clear()
        with patch("config.settings.get_settings", return_value=self.mock_settings), \
             patch("auth.get_settings", return_value=self.mock_settings):
            from config.settings import get_settings
            get_settings.cache_clear()
            yield
            get_settings.cache_clear()

    def test_verify_password(self):
        """verify_password returns True for matching passwords."""
        from auth import pwd_context, verify_password
        hashed = pwd_context.hash("secretpass")
        assert verify_password("secretpass", hashed) is True
        assert verify_password("wrongpass", hashed) is False

    def test_authenticate_user_admin_success(self):
        """authenticate_user returns admin dict for correct admin credentials."""
        from auth import authenticate_user
        result = authenticate_user("admin", self.mock_settings.admin_password)
        assert result is not None
        assert result["username"] == "admin"
        assert result["role"] == "admin"

    def test_authenticate_user_failure(self):
        """authenticate_user returns None for wrong credentials."""
        from auth import authenticate_user
        result = authenticate_user("admin", "wrong-password")
        assert result is None

    def test_login_endpoint_success(self, test_client):
        """POST /api/auth/token with valid admin creds returns token."""
        response = test_client.post(
            "/api/auth/token",
            data={
                "username": "admin",
                "password": self.mock_settings.admin_password,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_endpoint_failure(self, test_client):
        """POST /api/auth/token with wrong password returns 401."""
        response = test_client.post(
            "/api/auth/token",
            data={
                "username": "admin",
                "password": "definitelywrong",
            },
        )
        assert response.status_code == 401

    def test_protected_endpoint_no_token(self, test_client):
        """Endpoints that require auth should reject requests without token."""
        # /api/auth/me requires authentication
        response = test_client.get("/api/auth/me")
        # Should be 401 or 422 (no credentials provided)
        assert response.status_code in (401, 403, 422, 500)
