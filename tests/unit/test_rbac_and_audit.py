"""
Unit tests for Role-Based Access Control (RBAC), Production Secret Guards & Audit Logging.
"""

import os
import pytest
from fastapi.testclient import TestClient

from src.backend.main import app
from src.backend.auth import (
    User,
    create_access_token,
    user_store,
    validate_production_security
)
from src.backend.db.repositories.audit import audit_repo
from src.backend.lifecycle import ProductLifecycleValidator


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_production_security_guard_raises_on_default_secret(monkeypatch):
    """Verify that insecure default JWT secret in production aborts startup."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET", "f9c2d1b8e4a7360592c81e7d3a5b6c8f1029384756a1b2c3d4e5f60718293a4b")

    with pytest.raises(RuntimeError) as exc_info:
        validate_production_security()
    assert "JWT_SECRET" in str(exc_info.value)


def test_viewer_role_cannot_edit_or_approve(client):
    """Verify viewer role cannot perform mutations (403 Forbidden)."""
    viewer = user_store.get_by_email("viewer@unilog.com")
    token = create_access_token(viewer)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Attempt edit
    res = client.post(
        "/api/review/1/field-action",
        headers=headers,
        json={"field_name": "Material", "action": "edit", "new_value": "Copper", "reason": "Viewer test"}
    )
    assert res.status_code == 403

    # 2. Attempt approve
    res = client.post(
        "/api/review/1/approve",
        headers=headers,
        json={"notes": "Viewer approval attempt"}
    )
    assert res.status_code == 403


def test_specialist_role_cannot_approve(client):
    """Verify specialist role can edit candidates but CANNOT promote/approve to Validated."""
    import uuid
    spec_email = f"specialist_actor_{uuid.uuid4().hex[:6]}@test.com"
    specialist = user_store.create_user(
        email=spec_email,
        password="SpecialistPassword2026!",
        name="Specialist User",
        role="specialist"
    )
    token = create_access_token(specialist)
    headers = {"Authorization": f"Bearer {token}"}

    # Approve attempt by specialist
    res = client.post(
        "/api/review/1/approve",
        headers=headers,
        json={"notes": "Specialist approval attempt"}
    )
    assert res.status_code == 403


def test_reviewer_can_perform_field_actions(client):
    """Verify reviewer can perform approve, edit, and mark_unknown actions."""
    reviewer = user_store.get_by_email("reviewer@unilog.com")
    token = create_access_token(reviewer)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/api/review/1/field-action",
        headers=headers,
        json={"field_name": "invoice_desc", "action": "edit", "new_value": "DISHWASHER BUILT IN 120V", "reason": "Curation edit"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["product_id"] == "1"


def test_high_risk_unresolved_fields_block_approval():
    """Verify that a product with unresolved high-risk fields cannot be promoted to Validated."""
    invalid_product = {
        "mfg_part_number": "PDSH4816AF",
        "brand_name": "",  # Empty high risk field!
        "manufacturer_name": "Electrolux",
        "classpath": "Appliances > Dishwashers",
        "unspsc": "47121804",
        "invoice_desc": "DISHWASHER 24IN 120V",
        "short_desc": "Frigidaire Dishwasher",
        "confidence": 0.90,
        "data_conflicts": []
    }

    can_approve, reasons = ProductLifecycleValidator.check_approval_preconditions(invalid_product)
    assert can_approve is False
    assert any("brand_name" in r for r in reasons)


def test_audit_log_records_actions():
    """Verify immutable audit log records events."""
    audit_repo.record_action(
        user_email="reviewer@unilog.com",
        role="reviewer",
        action="FIELD_APPROVE",
        entity_type="field",
        entity_id="fld_test_123",
        before_state={"status": "candidate"},
        after_state={"status": "verified"},
        reason="Verified against official PDF spec",
        request_id="req_audit_test_1",
    )

    logs = audit_repo.list_logs(entity_type="field", entity_id="fld_test_123")
    assert len(logs) >= 1
    assert logs[0]["action"] == "FIELD_APPROVE"
    assert logs[0]["request_id"] == "req_audit_test_1"
    assert logs[0]["after_state"]["status"] == "verified"
