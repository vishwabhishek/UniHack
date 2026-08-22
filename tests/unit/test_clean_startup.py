"""
Unit tests verifying clean backend startup and health probes.
"""

from fastapi.testclient import TestClient
from src.backend.main import app


def test_system_health_probes():
    """Verify that /api/health, /api/ready, and /api/version return healthy status."""
    client = TestClient(app)

    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "healthy"

    ready_resp = client.get("/api/ready")
    assert ready_resp.status_code == 200
    assert ready_resp.json()["database"] == "healthy"

    version_resp = client.get("/api/version")
    assert version_resp.status_code == 200
    assert "version" in version_resp.json()
