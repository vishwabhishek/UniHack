"""
Unit tests for review queue approval integrity and high-risk field enforcement.
"""

import pytest
from fastapi.testclient import TestClient
from src.backend.main import app
from src.backend.state import catalog_state


@pytest.fixture
def client():
    return TestClient(app)


def test_approve_route_enforces_high_risk_field_validation(client):
    """Verify that calling /api/review/{id}/approve routes through promote_to_validated and rejects unresolved products."""
    admin_login = client.post("/api/auth/login", json={
        "email": "admin@unilog.com",
        "password": "Admin@123456"
    })
    token = admin_login.json()["token"]

    # Pick a product in the review queue
    review_queue = client.get("/api/review/queue", headers={"Authorization": f"Bearer {token}"}).json()
    if not review_queue["items"]:
        pytest.skip("No items in review queue")

    item = review_queue["items"][0]
    prod_id = item["id"]

    # Check field review
    field_rev = client.get(f"/api/review/{prod_id}/fields", headers={"Authorization": f"Bearer {token}"}).json()
    
    if field_rev["high_risk_unresolved_count"] > 0:
        # Attempt to approve unresolved item directly via /approve
        resp = client.post(
            f"/api/review/{prod_id}/approve",
            headers={"Authorization": f"Bearer {token}"},
            json={"approved": True, "notes": "Attempting unverified approval"}
        )
        assert resp.status_code == 400
        assert "Promotion blocked" in resp.json()["detail"]
        assert "Unresolved high-risk fields" in resp.json()["detail"]
