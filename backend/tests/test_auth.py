"""Tests for authentication and JWT token management."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4

from app.core.jwt import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)


class TestAccessTokens:
    """Unit tests for JWT access token creation and validation."""

    def test_create_and_decode_access_token(self):
        user_id = str(uuid4())
        token = create_access_token({"sub": user_id})

        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "access"

    def test_decode_access_token_rejects_expired(self):
        token = create_access_token(
            {"sub": "user123"},
            expires_delta=timedelta(seconds=-1),
        )
        assert decode_access_token(token) is None

    def test_decode_access_token_rejects_invalid_token(self):
        assert decode_access_token("invalid.token.here") is None

    def test_decode_access_token_rejects_refresh_token(self):
        token, _ = create_refresh_token({"sub": "user123"})
        # Access token decoder should reject refresh tokens
        assert decode_access_token(token) is None


class TestRefreshTokens:
    """Unit tests for JWT refresh token creation and validation."""

    def test_create_and_decode_refresh_token(self):
        user_id = str(uuid4())
        token, expires = create_refresh_token({"sub": user_id})

        assert expires > datetime.now(timezone.utc)

        payload = decode_refresh_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert "jti" in payload  # Unique token ID for rotation

    def test_decode_refresh_token_rejects_expired(self):
        token, _ = create_refresh_token(
            {"sub": "user123"},
            expires_delta=timedelta(seconds=-1),
        )
        assert decode_refresh_token(token) is None

    def test_decode_refresh_token_rejects_invalid(self):
        assert decode_refresh_token("garbage") is None

    def test_decode_refresh_token_rejects_access_token(self):
        token = create_access_token({"sub": "user123"})
        assert decode_refresh_token(token) is None

    def test_refresh_tokens_have_unique_jti(self):
        token1, _ = create_refresh_token({"sub": "user123"})
        token2, _ = create_refresh_token({"sub": "user123"})

        payload1 = decode_refresh_token(token1)
        payload2 = decode_refresh_token(token2)

        assert payload1["jti"] != payload2["jti"]

    def test_custom_expiry_delta(self):
        token, expires = create_refresh_token(
            {"sub": "user123"},
            expires_delta=timedelta(hours=1),
        )
        # Should expire roughly 1 hour from now
        expected = datetime.now(timezone.utc) + timedelta(hours=1)
        assert abs((expires - expected).total_seconds()) < 5
