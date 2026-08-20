"""Unit tests for PBKDF2 password hashing and RFC 7519 JWT token generation."""

import time
import pytest
from fastapi import HTTPException
from src.backend.auth import (
    User,
    create_access_token,
    decode_access_token,
    hash_password,
    user_store,
    verify_password,
)
from src.backend.config import settings


def test_password_hashing_and_verification():
    raw_pwd = "MySecretPassword2026!"
    hashed = hash_password(raw_pwd)
    assert hashed.startswith("pbkdf2:sha256:100000$")
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False
    assert verify_password("", hashed) is False


def test_jwt_token_generation_and_decoding():
    user = User(
        id="usr_test123",
        email="test@unilog.com",
        name="Test User",
        password_hash=hash_password("DummyPass123!"),
        role="specialist",
    )
    token = create_access_token(user, expires_in=3600)
    assert isinstance(token, str)
    parts = token.split(".")
    assert len(parts) == 3

    payload = decode_access_token(token)
    assert payload["sub"] == "usr_test123"
    assert payload["email"] == "test@unilog.com"
    assert payload["role"] == "specialist"
    assert payload["name"] == "Test User"
    assert payload["exp"] > time.time()


def test_jwt_token_expired():
    user = User(
        id="usr_expired",
        email="expired@unilog.com",
        name="Expired User",
        password_hash="hash",
        role="viewer",
    )
    token = create_access_token(user, expires_in=-10)
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(token)
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


def test_jwt_token_tampered_signature():
    user = User(
        id="usr_valid",
        email="valid@unilog.com",
        name="Valid User",
        password_hash="hash",
        role="admin",
    )
    token = create_access_token(user)
    parts = token.split(".")
    tampered_token = f"{parts[0]}.{parts[1]}.tamperedSig123"
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(tampered_token)
    assert exc_info.value.status_code == 401
    assert "signature" in exc_info.value.detail.lower()


def test_user_store_admin_bootstrap():
    if settings.admin_initial_email and settings.admin_initial_password:
        admin = user_store.get_by_email(settings.admin_initial_email)
        assert admin is not None
        assert admin.role == "admin"
        assert verify_password(settings.admin_initial_password, admin.password_hash) is True
