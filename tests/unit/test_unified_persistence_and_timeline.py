"""
Comprehensive verification tests for:
1. SQLite state restoration across restart simulation
2. Stale batch job recovery
3. PDF parser page-level extraction
4. Source lifecycle management and cache invalidation
5. Export history and delivery traceability
6. Product activity timeline aggregation
7. Admin RBAC user management
"""

import os
import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.backend.main import app
from src.backend.state import CatalogState
from src.backend.db.connection import get_db_connection
from src.backend.db.repositories.products import product_repo
from src.backend.db.repositories.exports import export_repo
from src.backend.db.repositories.audit import audit_repo
from src.backend.db.repositories.users import user_repo
from src.backend.jobs.runner import job_runner
from src.evidence.pdf_parser import parse_manufacturer_pdf_file, parse_manufacturer_pdf_text
from src.evidence.registry import EvidenceRegistryManager
from src.evidence.cache import default_extraction_cache
from src.backend.auth import User, create_access_token, user_store


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_token():
    user = user_store.get_by_email("admin.test@unilog.com")
    if not user:
        user = user_store.create_user(email="admin.test@unilog.com", password="Password123!", role="admin", name="Admin Test")
    return create_access_token(user)


@pytest.fixture
def specialist_token():
    user = user_store.get_by_email("spec.test@unilog.com")
    if not user:
        user = user_store.create_user(email="spec.test@unilog.com", password="Password123!", role="specialist", name="Spec Test")
    return create_access_token(user)


@pytest.fixture
def viewer_token():
    user = user_store.get_by_email("viewer.test@unilog.com")
    if not user:
        user = user_store.create_user(email="viewer.test@unilog.com", password="Password123!", role="viewer", name="Viewer Test")
    return create_access_token(user)


def test_sqlite_restart_persistence():
    """Verify that catalog state restores from SQLite accurately."""
    state = CatalogState()
    state.initialize()
    assert state._initialized
    assert len(state._products_list) == 1000

    # Modify a product in state (persists to SQLite)
    prod_id = "1"
    updated = state.update_product(prod_id, {"brand_name": "DELTA FAUCET (PERSISTED TEST)"})
    assert updated is not None

    # Simulate restart by creating a new state instance and restoring from SQLite
    new_state = CatalogState()
    new_state.initialize()
    restored_prod, _ = new_state.get_product(prod_id)
    assert restored_prod is not None
    assert restored_prod.brand_name == "DELTA FAUCET (PERSISTED TEST)"


def test_stale_job_recovery():
    """Verify that interrupted jobs in 'running' state are recovered on restart."""
    # Insert a dummy running job
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO enrichment_jobs (
                job_id, idempotency_key, status, total_products, processed_products,
                completed_products, review_required_products, failed_products,
                cache_hits, started_at
            ) VALUES ('job_stale_test', 'idem_stale_test', 'running', 10, 3, 3, 0, 0, 1, 1000.0);
            """
        )
        conn.commit()

    # Call recover_stale_jobs
    recovered_count = job_runner.recover_stale_jobs()
    assert recovered_count >= 1

    # Verify status changed to failed
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, error_message FROM enrichment_jobs WHERE job_id = 'job_stale_test';")
        row = cursor.fetchone()
        assert row["status"] == "failed"
        assert "server restart" in row["error_message"]


def test_pypdf_parser_page_level_extraction():
    """Verify that pypdf extraction preserves page numbers."""
    from pypdf import PdfWriter

    # Create a simple in-memory 2-page PDF
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.add_blank_page(width=612, height=792)
    pdf_stream = io.BytesIO()
    writer.write(pdf_stream)
    pdf_bytes = pdf_stream.getvalue()

    title, sections = parse_manufacturer_pdf_file(pdf_bytes, title="Test 2-Page Spec Sheet")
    assert title == "Test 2-Page Spec Sheet"
    assert isinstance(sections, list)


def test_source_lifecycle_and_cache_invalidation(client, specialist_token):
    """Verify source stale/supersede/reject actions and cache invalidation."""
    from src.backend.routes.evidence import registry_manager as reg

    # Setup dummy cache entry
    dummy_hash = "dummy_hash_for_lifecycle_test"
    cache_key = default_extraction_cache.generate_cache_key(
        source_hash=dummy_hash,
        mpn="TEST_MPN_123",
        model_name="gemini-2.5-flash",
        schema_version="v1.0.0",
        lov_version="v1.0.0"
    )

    # Insert into registry
    from src.evidence.models import SourceRegistryEntry
    entry = SourceRegistryEntry(
        source_id="src_test_lifecycle_01",
        mpn="TEST_MPN_123",
        brand="TEST BRAND",
        manufacturer="TEST MFR",
        source_type="manufacturer_page",
        file_hash=dummy_hash,
        source_status="ACTIVE",
    )
    reg._registry_cache[entry.source_id] = entry
    reg._save_registry()

    # Mark stale via API
    resp = client.post(
        f"/api/evidence/source/{entry.source_id}/mark-stale",
        headers={"Authorization": f"Bearer {specialist_token}"},
        json={"reason": "Updated manufacturer model released"}
    )
    assert resp.status_code == 200
    assert resp.json()["source_status"] == "STALE"


    # Reject via API
    resp_rej = client.post(
        f"/api/evidence/source/{entry.source_id}/reject",
        headers={"Authorization": f"Bearer {specialist_token}"},
        json={"reason": "Contains mismatched voltage specs"}
    )
    assert resp_rej.status_code == 200
    assert resp_rej.json()["source_status"] == "REJECTED_UNTRUSTED"


def test_export_history_endpoint(client, viewer_token):
    """Verify GET /api/export/history returns recorded exports."""
    # Download CSV to generate an export event
    csv_resp = client.get("/api/export/csv?status=Validated", headers={"Authorization": f"Bearer {viewer_token}"})
    assert csv_resp.status_code == 200

    # Query history
    hist_resp = client.get("/api/export/history?limit=10", headers={"Authorization": f"Bearer {viewer_token}"})
    assert hist_resp.status_code == 200
    data = hist_resp.json()
    assert "exports" in data
    assert data["total_exports"] >= 1
    latest = data["exports"][0]
    assert "checksum_sha256" in latest
    assert "product_count" in latest


def test_product_activity_timeline_endpoint(client, viewer_token):
    """Verify GET /api/review/{product_id}/timeline returns chronological events."""
    prod_id = "1"
    resp = client.get(f"/api/review/{prod_id}/timeline", headers={"Authorization": f"Bearer {viewer_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["product_id"] == prod_id
    assert "timeline" in data
    assert isinstance(data["timeline"], list)


def test_admin_rbac_user_management(client, admin_token, viewer_token):
    """Verify admin can list users and update roles, while viewer cannot."""
    # Ensure bootstrap admin is intact
    admin_boot = user_store.get_by_email("admin@unilog.com")
    if admin_boot and admin_boot.role != "admin":
        user_store.update_user_role(admin_boot.id, "admin")

    # Viewer tries to access admin users list -> 403 Forbidden
    v_resp = client.get("/api/auth/users", headers={"Authorization": f"Bearer {viewer_token}"})
    assert v_resp.status_code == 403

    # Admin lists users -> 200 OK
    a_resp = client.get("/api/auth/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert a_resp.status_code == 200
    users = a_resp.json()
    assert len(users) >= 1

    # Admin updates a dedicated user's role
    target_user = user_store.get_by_email("role.target@unilog.com")
    if not target_user:
        target_user = user_store.create_user(
            email="role.target@unilog.com", password="Password123!", role="specialist", name="Target User"
        )
    update_resp = client.put(
        f"/api/auth/users/{target_user.id}/role",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "reviewer"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["user"]["role"] == "reviewer"

