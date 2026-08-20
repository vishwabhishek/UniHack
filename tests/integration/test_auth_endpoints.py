"""Integration tests for Authentication API endpoints."""

import pytest
from starlette.testclient import TestClient
from src.backend.main import app

client = TestClient(app)


def test_auth_demo_accounts_endpoint():
    res = client.get("/api/auth/demo-accounts")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 4
    roles = [d["role"] for d in data]
    assert "admin" in roles
    assert "specialist" in roles
    assert "reviewer" in roles
    assert "viewer" in roles


def test_auth_login_success():
    payload = {
        "email": "admin@unilog.com",
        "password": "Admin2026!"
    }
    res = client.post("/api/auth/login", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "token" in data
    assert data["token_type"] == "Bearer"
    assert data["user"]["email"] == "admin@unilog.com"
    assert data["user"]["role"] == "admin"


def test_auth_login_invalid_password():
    payload = {
        "email": "admin@unilog.com",
        "password": "WrongPassword123!"
    }
    res = client.post("/api/auth/login", json=payload)
    assert res.status_code == 401
    assert "invalid" in res.json()["detail"].lower()


def test_auth_me_endpoint_with_valid_token():
    # Login first
    login_res = client.post("/api/auth/login", json={"email": "specialist@unilog.com", "password": "Specialist2026!"})
    token = login_res.json()["token"]

    # Call /api/auth/me
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    user_data = res.json()
    assert user_data["email"] == "specialist@unilog.com"
    assert user_data["role"] == "specialist"


def test_auth_me_endpoint_unauthorized():
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_auth_register_and_login_new_user():
    email = "newuser_test@unilog.com"
    register_payload = {
        "email": email,
        "password": "NewUserPassword123!",
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
    login_res = client.post("/api/auth/login", json={"email": email, "password": "NewUserPassword123!"})
    assert login_res.status_code == 200
    assert login_res.json()["user"]["name"] == "Jane Developer"


def test_auth_register_duplicate_email():
    payload = {
        "email": "admin@unilog.com",
        "password": "AnyPassword123!",
        "name": "Duplicate User",
        "role": "viewer"
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]


def test_admin_list_users_rbac():
    # Login as admin
    admin_token = client.post("/api/auth/login", json={"email": "admin@unilog.com", "password": "Admin2026!"}).json()["token"]
    res = client.get("/api/auth/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    assert len(res.json()) >= 4

    # Login as viewer and attempt to list users -> should be forbidden (403)
    viewer_token = client.post("/api/auth/login", json={"email": "viewer@unilog.com", "password": "Viewer2026!"}).json()["token"]
    res_forbidden = client.get("/api/auth/users", headers={"Authorization": f"Bearer {viewer_token}"})
    assert res_forbidden.status_code == 403
