"""Integration tests for Authentication API endpoints."""

import pytest
from starlette.testclient import TestClient
from src.backend.main import app
from src.backend.config import settings

client = TestClient(app)


def test_auth_login_success():
    payload = {
        "email": settings.admin_initial_email or "admin@unilog.com",
        "password": settings.admin_initial_password or "ChangeMeAdmin2026!"
    }
    res = client.post("/api/auth/login", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "token" in data
    assert data["token_type"] == "Bearer"
    assert data["user"]["email"] == payload["email"].lower().strip()
    assert data["user"]["role"] == "admin"


def test_auth_login_invalid_password():
    payload = {
        "email": settings.admin_initial_email or "admin@unilog.com",
        "password": "WrongPassword123!"
    }
    res = client.post("/api/auth/login", json=payload)
    assert res.status_code == 401
    assert "invalid" in res.json()["detail"].lower()


def test_auth_me_endpoint_with_valid_token():
    # Login first
    login_payload = {
        "email": settings.admin_initial_email or "admin@unilog.com",
        "password": settings.admin_initial_password or "ChangeMeAdmin2026!"
    }
    login_res = client.post("/api/auth/login", json=login_payload)
    token = login_res.json()["token"]

    # Call /api/auth/me
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    user_data = res.json()
    assert user_data["email"] == login_payload["email"].lower().strip()
    assert user_data["role"] == "admin"


def test_auth_me_endpoint_unauthorized():
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_auth_register_and_login_new_user():
    email = "new_specialist_test@unilog.com"
    register_payload = {
        "email": email,
        "password": "SecurePassword2026!",
        "name": "Jane Developer",
        "role": "specialist"
    }
    res = client.post("/api/auth/register", json=register_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["user"]["email"] == email
    assert data["user"]["name"] == "Jane Developer"
    assert "token" in data

    # Verify new user can login
    login_res = client.post("/api/auth/login", json={"email": email, "password": "SecurePassword2026!"})
    assert login_res.status_code == 200
    assert login_res.json()["user"]["name"] == "Jane Developer"


def test_auth_register_duplicate_email():
    payload = {
        "email": settings.admin_initial_email or "admin@unilog.com",
        "password": "AnyPassword123!",
        "name": "Duplicate User",
        "role": "viewer"
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]


def test_admin_list_users_rbac():
    # Login as admin
    admin_payload = {
        "email": settings.admin_initial_email or "admin@unilog.com",
        "password": settings.admin_initial_password or "ChangeMeAdmin2026!"
    }
    admin_token = client.post("/api/auth/login", json=admin_payload).json()["token"]
    res = client.get("/api/auth/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # Register a viewer and attempt to list users -> should be forbidden (403)
    viewer_email = "auditor_viewer@unilog.com"
    client.post("/api/auth/register", json={
        "email": viewer_email,
        "password": "ViewerPassword2026!",
        "name": "Elena Auditor",
        "role": "viewer"
    })
    viewer_token = client.post("/api/auth/login", json={"email": viewer_email, "password": "ViewerPassword2026!"}).json()["token"]
    res_forbidden = client.get("/api/auth/users", headers={"Authorization": f"Bearer {viewer_token}"})
    assert res_forbidden.status_code == 403
