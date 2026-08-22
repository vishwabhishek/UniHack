"""
Unit tests for RBAC, Privilege Escalation Prevention, and Admin Role Management.
"""

import pytest
from fastapi.testclient import TestClient
from src.backend.main import app
from src.backend.auth import user_store, hash_password
from src.backend.db.repositories.users import user_repo


@pytest.fixture
def client():
    return TestClient(app)


def test_public_registration_blocks_admin_and_reviewer_privilege_escalation(client):
    """Verify that public registration rejects requests claiming 'admin' or 'reviewer' roles."""
    # Attempt admin registration
    resp = client.post("/api/auth/register", json={
        "email": "attacker_admin@test.com",
        "password": "StrongPassword123!",
        "name": "Attacker Admin",
        "role": "admin"
    })
    assert resp.status_code == 400
    assert "Self-registration cannot grant elevated role 'admin'" in resp.json()["detail"]

    # Attempt reviewer registration
    resp_rev = client.post("/api/auth/register", json={
        "email": "attacker_reviewer@test.com",
        "password": "StrongPassword123!",
        "name": "Attacker Reviewer",
        "role": "reviewer"
    })
    assert resp_rev.status_code == 400
    assert "Self-registration cannot grant elevated role 'reviewer'" in resp_rev.json()["detail"]


def test_public_registration_forces_viewer_or_specialist(client):
    """Verify that standard self-registration assigns viewer or specialist role."""
    import uuid
    email = f"valid_user_viewer_{uuid.uuid4().hex[:6]}@test.com"
    resp = client.post("/api/auth/register", json={
        "email": email,
        "password": "StrongPassword123!",
        "name": "Normal User"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"]["role"] == "viewer"
    assert "token" in data


def test_admin_only_role_update_endpoint(client):
    """Verify that only admins can update user roles via PUT /api/auth/users/{user_id}/role."""
    # 1. Login as Admin
    admin_login = client.post("/api/auth/login", json={
        "email": "admin@unilog.com",
        "password": "Admin@123456"
    })
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["token"]

    # 2. Register a dedicated test user
    import uuid
    test_user_email = f"promo_user_{uuid.uuid4().hex[:6]}@test.com"
    test_user_pwd = "SpecialistPassword2026!"
    reg_resp = client.post("/api/auth/register", json={
        "email": test_user_email,
        "password": test_user_pwd,
        "name": "Promo User"
    })
    assert reg_resp.status_code == 201
    user_token = reg_resp.json()["token"]
    user_id = reg_resp.json()["user"]["id"]

    # 3. Non-admin attempting to change role is rejected (403)
    forbidden_resp = client.put(
        f"/api/auth/users/{user_id}/role",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"role": "admin"}
    )
    assert forbidden_resp.status_code == 403

    # 4. Admin successfully promotes test user to reviewer
    success_resp = client.put(
        f"/api/auth/users/{user_id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "reviewer"}
    )
    assert success_resp.status_code == 200
    assert success_resp.json()["user"]["role"] == "reviewer"

    # 5. Old test user token is now revoked due to token_version increment
    stale_resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert stale_resp.status_code == 401
    assert "Session has been revoked" in stale_resp.json()["detail"]
