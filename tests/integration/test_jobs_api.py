"""
Integration tests for Persistent Asynchronous Jobs API.
"""

import pytest
import time
from fastapi.testclient import TestClient

from src.backend.main import app
from src.backend.auth import User, create_access_token, user_store
from src.backend.db.repositories.jobs import job_repo


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_headers():
    admin = user_store.get_by_email("admin@unilog.com")
    token = create_access_token(admin)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def specialist_headers():
    spec = user_store.get_by_email("specialist@unilog.com")
    token = create_access_token(spec)
    return {"Authorization": f"Bearer {token}"}


def test_submit_and_query_enrichment_job(client, specialist_headers):
    """Verify job submission, progress querying, and event tracking."""
    # 1. Submit job
    res = client.post(
        "/api/jobs/enrichment",
        headers=specialist_headers,
        json={"max_concurrency": 2, "force_refresh": False}
    )
    assert res.status_code == 200
    job = res.json()
    job_id = job["job_id"]
    assert job["status"] in ("queued", "running", "completed")
    assert job["total_products"] >= 3

    # 2. Query status
    res_status = client.get(f"/api/jobs/{job_id}", headers=specialist_headers)
    assert res_status.status_code == 200
    assert res_status.json()["job_id"] == job_id

    # 3. Query events
    res_events = client.get(f"/api/jobs/{job_id}/events", headers=specialist_headers)
    assert res_events.status_code == 200
    assert "events" in res_events.json()

    # 4. List jobs
    res_list = client.get("/api/jobs", headers=specialist_headers)
    assert res_list.status_code == 200
    assert res_list.json()["total"] >= 1


def test_idempotency_key_deduplication(client, specialist_headers):
    """Verify that submitting with the same idempotency key returns the same job."""
    idemp_key = f"idemp_test_{int(time.time())}"

    # First call
    res1 = client.post(
        "/api/jobs/enrichment",
        headers=specialist_headers,
        json={"idempotency_key": idemp_key, "max_concurrency": 2}
    )
    assert res1.status_code == 200
    job1 = res1.json()

    # Second call with same idempotency key
    res2 = client.post(
        "/api/jobs/enrichment",
        headers=specialist_headers,
        json={"idempotency_key": idemp_key, "max_concurrency": 2}
    )
    assert res2.status_code == 200
    job2 = res2.json()

    assert job1["job_id"] == job2["job_id"]


def test_job_cancellation(client, specialist_headers):
    """Verify job cancellation endpoint."""
    res = client.post(
        "/api/jobs/enrichment",
        headers=specialist_headers,
        json={"max_concurrency": 1}
    )
    job_id = res.json()["job_id"]

    cancel_res = client.post(f"/api/jobs/{job_id}/cancel", headers=specialist_headers)
    assert cancel_res.status_code == 200
    assert "cancelled" in cancel_res.json()


def test_dangling_job_recovery_on_restart():
    """Verify recovery of dangling running jobs on system restart."""
    # Create artificial running job with unique ID
    dangling_id = f"job_dangling_{int(time.time() * 1000)}"
    job_repo.create_job(job_id=dangling_id, total_products=5, status="running")

    # Run recovery
    recovered_count = job_repo.recover_dangling_jobs()
    assert recovered_count >= 1

    recovered_job = job_repo.get_job_by_id(dangling_id)
    assert recovered_job["status"] == "failed"
    assert "interrupted by server restart" in recovered_job["error_message"]
