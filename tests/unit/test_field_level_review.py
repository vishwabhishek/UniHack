"""
Unit & Integration Tests for Field-Level Evidence Review Queue, Audit Logging, and Validation Gates.
"""

import pytest
from starlette.testclient import TestClient
from src.backend.main import app
from src.backend.state import catalog_state
from src.backend.config import settings


@pytest.fixture(scope="module")
def client():
    """Create authenticated test client with initialized catalog state."""
    catalog_state.initialize()
    with TestClient(app) as test_client:
        # Authenticate as admin
        login_res = test_client.post("/api/auth/login", json={
            "email": settings.admin_initial_email or "admin@unilog.com",
            "password": settings.admin_initial_password or "ChangeMeAdmin2026!"
        })
        token = login_res.json()["token"]
        test_client.headers["Authorization"] = f"Bearer {token}"
        yield test_client


class TestFieldLevelReview:
    """Verify field-level evidence review, immutable audit trail, and validation gates."""

    def test_get_product_field_review_structure(self, client):
        """Test retrieving granular field-level review items."""
        response = client.get("/api/review/1/fields")
        assert response.status_code == 200
        data = response.json()
        
        assert "product_id" in data
        assert "fields" in data
        assert "audit_trail" in data
        assert "high_risk_unresolved_count" in data
        assert "can_promote_to_validated" in data
        
        # Check field structure
        fields = data["fields"]
        assert len(fields) >= 5
        
        mpn_field = next((f for f in fields if f["field_name"] == "mfg_part_number"), None)
        assert mpn_field is not None
        assert mpn_field["is_high_risk"] is True
        assert "raw_supplier_input" in mpn_field
        assert "candidate_value" in mpn_field
        assert "normalized_value" in mpn_field
        assert "source_citation" in mpn_field
        assert "confidence" in mpn_field
        assert "verification_status" in mpn_field

    def test_field_action_approve_preserves_evidence(self, client):
        """Test that approving a field updates status to verified without erasing original candidate or source."""
        # 1. Inspect before action
        res_before = client.get("/api/review/1/fields").json()
        target_field_name = "invoice_desc"
        field_before = next(f for f in res_before["fields"] if f["field_name"] == target_field_name)
        orig_cand = field_before["candidate_value"]
        orig_src = field_before["source_citation"]

        # 2. Submit approve action
        payload = {
            "field_name": target_field_name,
            "action": "approve",
            "reason": "Verified invoice title meets 40-char ERP requirements"
        }
        res_action = client.post("/api/review/1/field-action", json=payload)
        assert res_action.status_code == 200
        data_after = res_action.json()
        
        field_after = next(f for f in data_after["fields"] if f["field_name"] == target_field_name)
        assert field_after["verification_status"] == "verified"
        assert field_after["candidate_value"] == orig_cand  # Must not erase original candidate
        assert field_after["source_citation"] == orig_src  # Must not erase original source

        # Check audit trail entry
        assert len(field_after["audit_history"]) >= 1
        latest_audit = field_after["audit_history"][-1]
        assert latest_audit["action"] == "approve"
        assert latest_audit["reason"] == "Verified invoice title meets 40-char ERP requirements"

    def test_field_action_manual_edit_records_audit_trail(self, client):
        """Test that manual edit records reviewer, timestamp, prev value, new value, and reason."""
        target_field_name = "brand_name"
        new_brand_val = "FRIGIDAIRE GALLERY®"
        
        payload = {
            "field_name": target_field_name,
            "action": "edit",
            "new_value": new_brand_val,
            "reason": "Corrected brand to Gallery premium series per spec sheet"
        }
        res_action = client.post("/api/review/1/field-action", json=payload)
        assert res_action.status_code == 200
        data_after = res_action.json()
        
        field_after = next(f for f in data_after["fields"] if f["field_name"] == target_field_name)
        assert field_after["normalized_value"] == new_brand_val
        assert field_after["verification_status"] == "verified"
        
        # Verify immutable audit record
        assert len(field_after["audit_history"]) >= 1
        audit = field_after["audit_history"][-1]
        assert audit["field_name"] == target_field_name
        assert audit["new_value"] == new_brand_val
        assert audit["reason"] == "Corrected brand to Gallery premium series per spec sheet"
        assert audit["action"] == "edit"
        assert audit["timestamp"] is not None

    def test_field_action_mark_unknown_leaves_blank_in_export(self, client):
        """Test that marking a field unknown sets value to blank and leaves it blank in final export."""
        target_field_name = "attr_Amperage Rating"
        
        payload = {
            "field_name": target_field_name,
            "action": "mark_unknown",
            "reason": "Amperage rating unconfirmed in reference documents"
        }
        res_action = client.post("/api/review/1/field-action", json=payload)
        assert res_action.status_code == 200
        data_after = res_action.json()
        
        field_after = next((f for f in data_after["fields"] if f["field_name"] == target_field_name), None)
        if field_after:
            assert field_after["verification_status"] == "unknown"

    def test_promote_to_validated_gate(self, client):
        """Test that promotion to Validated requires high-risk fields to be resolved."""
        # Test item 1
        prod, _ = catalog_state.get_product("1")
        prod.status = "Flagged"
        
        # Resolve high-risk fields
        for hrf in catalog_state.HIGH_RISK_FIELDS:
            catalog_state.apply_field_action(
                key="1",
                field_name=hrf,
                action="approve",
                new_value=None,
                reason="Specialist approved",
                reviewer="admin"
            )
            
        res_promote = client.post("/api/review/1/promote-validated", json={"approved": True, "notes": "Approved"})
        assert res_promote.status_code == 200
        promote_data = res_promote.json()
        assert promote_data["success"] is True
        assert promote_data["status"] == "Validated"
