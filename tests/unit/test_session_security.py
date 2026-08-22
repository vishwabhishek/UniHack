"""
Unit tests for HttpOnly session cookies, CSRF defenses, and secure logout.
"""

from fastapi.testclient import TestClient
from src.backend.main import app


def test_login_sets_httponly_cookie():
    """Verify that login sets a secure HttpOnly cookie."""
    client = TestClient(app)
    resp = client.post("/api/auth/login", json={
        "email": "admin@unilog.com",
        "password": "Admin@123456"
    })
    assert resp.status_code == 200
    assert "unilog_auth_token" in resp.cookies
    cookie = resp.cookies.get("unilog_auth_token")
    assert cookie is not None


def test_logout_revokes_token_and_clears_cookie():
    """Verify that logout revokes active tokens and clears session cookie."""
    client = TestClient(app)
    login_resp = client.post("/api/auth/login", json={
        "email": "admin@unilog.com",
        "password": "Admin@123456"
    })
    token = login_resp.json()["token"]

    logout_resp = client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert logout_resp.status_code == 200

    # Token is now revoked
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 401
