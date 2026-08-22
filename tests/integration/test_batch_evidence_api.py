"""
Integration tests for FastAPI Batch Evidence-Enrichment and Cache Management endpoints.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient

from src.backend.main import app
from src.backend.auth import User, user_store, create_access_token

client = TestClient(app)


@pytest.fixture
def auth_headers():
    user = user_store.get_by_email("admin@unilog.com")
    assert user is not None
    admin_token = create_access_token(user)
    return {"Authorization": f"Bearer {admin_token}"}


def test_get_cache_stats_endpoint(auth_headers):
    """Verify that /api/evidence/cache/stats returns valid cache metrics."""
    res = client.get("/api/evidence/cache/stats", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_entries" in data
    assert "hits" in data
    assert "misses" in data
    assert "tokens_saved_estimate" in data
    assert "cost_saved_usd_estimate" in data


def test_clear_cache_endpoint(auth_headers):
    """Verify that /api/evidence/cache/clear wipes cache and resets stats."""
    res = client.post("/api/evidence/cache/clear", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "wiped successfully" in data["message"]
    assert data["stats"]["total_entries"] == 0


def test_start_and_poll_batch_job_endpoint(auth_headers):
    """Verify starting a batch job and querying its real-time status."""
    payload = {
        "mpns": ["U008LFA", "SHXM4AY55N"],
        "max_concurrency": 2,
        "force_refresh": False,
    }
    start_res = client.post("/api/evidence/batch/start", json=payload, headers=auth_headers)
    assert start_res.status_code == 200
    job_data = start_res.json()
    assert "job_id" in job_data
    job_id = job_data["job_id"]
    assert job_data["status"] in ("PENDING", "RUNNING", "COMPLETED")
    assert job_data["evidence_backed_products"] == 2

    # Poll status
    status_res = client.get(f"/api/evidence/batch/status/{job_id}", headers=auth_headers)
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["job_id"] == job_id
    assert "product_states" in status_data

    # Query latest endpoint
    latest_res = client.get("/api/evidence/batch/latest", headers=auth_headers)
    assert latest_res.status_code == 200
    latest_data = latest_res.json()
    assert latest_data is not None
    assert latest_data["job_id"] == job_id


def test_cancel_batch_job_endpoint(auth_headers):
    """Verify cancellation endpoint on active job."""
    payload = {"mpns": ["U008LFA"], "max_concurrency": 1}
    start_res = client.post("/api/evidence/batch/start", json=payload, headers=auth_headers)
    job_id = start_res.json()["job_id"]

    cancel_res = client.post(f"/api/evidence/batch/cancel/{job_id}", headers=auth_headers)
    assert cancel_res.status_code == 200
    cancel_data = cancel_res.json()
    assert "cancelled successfully" in cancel_data["message"]
