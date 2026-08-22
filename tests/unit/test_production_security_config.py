"""
Unit tests for production configuration validation and demo account suppression.
"""

import os
import pytest
from src.backend.auth import validate_production_security, UserStore
from src.backend.db.repositories.users import user_repo


def test_production_security_rejects_weak_or_default_jwt_secret(monkeypatch):
    """Verify that validate_production_security raises an exception if JWT_SECRET is weak or default."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET", "dev-insecure-secret-key-change-in-production")
    monkeypatch.setenv("ADMIN_INITIAL_EMAIL", "admin@prod-enterprise.com")
    monkeypatch.setenv("ADMIN_INITIAL_PASSWORD", "SuperSecurePassword123!")

    with pytest.raises(RuntimeError) as exc:
        validate_production_security()
    assert "Insecure, default, or weak JWT_SECRET detected" in str(exc.value)


def test_production_security_requires_strong_admin_credentials(monkeypatch):
    """Verify that validate_production_security raises an exception if production admin credentials are default or missing."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET", "a" * 32)
    monkeypatch.setenv("ADMIN_INITIAL_EMAIL", "")
    monkeypatch.setenv("ADMIN_INITIAL_PASSWORD", "Admin@123456")

    with pytest.raises(RuntimeError) as exc:
        validate_production_security()
    assert "Insecure or missing ADMIN_INITIAL_EMAIL / ADMIN_INITIAL_PASSWORD" in str(exc.value)


def test_production_security_passes_with_valid_config(monkeypatch):
    """Verify that valid strong production credentials pass validation without error."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET", "super_strong_production_secret_key_2026_xyz_789")
    monkeypatch.setenv("ADMIN_INITIAL_EMAIL", "ciso-admin@enterprise.unilog.com")
    monkeypatch.setenv("ADMIN_INITIAL_PASSWORD", "SuperSecureProductionPassword2026!")

    validate_production_security()  # Should not raise
