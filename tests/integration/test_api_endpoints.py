"""
Comprehensive Integration Test Suite for UniHack FastAPI Backend Endpoints.
Validates all routes, state mutations, exports, playground sandbox, and benchmark analytics.
"""

import io
import pytest
import pandas as pd
from starlette.testclient import TestClient
from src.backend.main import app
from src.backend.state import catalog_state
from src.backend.config import settings
from src.pipeline.delivery_mapper import DeliveryMapper


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


class TestAPIEndpoints:
    """Test suite covering all FastAPI REST API routes."""

    def test_unauthenticated_request_blocked(self):
        """Verify that requests without JWT Bearer token are blocked with 401."""
        with TestClient(app) as raw_client:
            res = raw_client.get("/api/products")
            assert res.status_code == 401
            assert "Missing Bearer" in res.json()["detail"] or "unauthorized" in res.json()["detail"].lower()

    def test_health_check_endpoint(self, client: TestClient):
        """Verify /api/health returns healthy operational status without auth."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["total_records"] == 1000
        assert data["enriched"] >= 0
        assert data["hard_gates_compliant"] is True

    def test_catalog_stats_endpoint(self, client: TestClient):
        """Verify /api/stats returns complete catalog KPI metrics."""
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_items"] == 1000
        assert data["schema_columns_count"] == 252
        assert data["invoice_compliance_pct"] == 100.0
        assert data["mobile_compliance_pct"] == 100.0
        assert data["lov_compliance_pct"] == 100.0
        assert "status_counts" in data
        assert "dept_counts" in data
        assert "top_brands" in data

    def test_filter_options_endpoint(self, client: TestClient):
        """Verify /api/filters returns available filter facets."""
        response = client.get("/api/filters")
        assert response.status_code == 200
        data = response.json()
        assert "statuses" in data
        assert "departments" in data
        assert "brands" in data
        assert len(data["departments"]) > 0
        assert len(data["brands"]) > 0

    def test_get_products_pagination_and_sorting(self, client: TestClient):
        """Verify /api/products returns paginated list with correct total and sorting."""
        response = client.get("/api/products?page=1&limit=25&sort_by=row_id&sort_dir=asc")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1000
        assert data["page"] == 1
        assert data["limit"] == 25
        assert data["total_pages"] == 40
        assert len(data["items"]) == 25

        # Check structure of first item
        item = data["items"][0]
        assert "id" in item
        assert "mfg_part_number" in item
        assert "invoice_desc" in item
        assert "mobile_desc" in item
        assert "confidence_score" in item
        assert len(item["invoice_desc"]) <= 40
        assert item["invoice_desc"].isupper()
        assert 60 <= len(item["mobile_desc"]) <= 80

    def test_get_products_search(self, client: TestClient):
        """Verify search query across multiple fields."""
        response = client.get("/api/products?search=dishwasher")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0
        for item in data["items"]:
            haystack = f"{item['mfg_part_number']} {item['short_desc']} {item['classpath']}".lower()
            assert "dishwasher" in haystack

    def test_get_products_filter_status(self, client: TestClient):
        """Verify filtering by status."""
        response = client.get("/api/products?status=Enriched")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["status"] == "Enriched"

    def test_get_product_detail_by_id(self, client: TestClient):
        """Verify /api/products/{id} returns full 252-column detail."""
        response = client.get("/api/products/1")
        assert response.status_code == 200
        data = response.json()
        assert data["row_id"] == 1
        assert "mfg_part_number" in data
        assert "delivery_columns" in data
        assert len(data["delivery_columns"]) == 252
        assert "attributes" in data
        assert "dimensions" in data
        assert "confidence_breakdown" in data

    def test_get_product_detail_not_found(self, client: TestClient):
        """Verify 404 response for invalid product ID."""
        response = client.get("/api/products/999999")
        assert response.status_code == 404

    def test_playground_presets(self, client: TestClient):
        """Verify /api/playground/presets returns pre-configured samples."""
        response = client.get("/api/playground/presets")
        assert response.status_code == 200
        presets = response.json()
        assert len(presets) >= 5
        assert any("Dishwasher" in p["name"] for p in presets)

    def test_playground_transform_instant_execution(self, client: TestClient):
        """Verify /api/playground/transform executes in sub-second and returns all stages."""
        payload = {
            "mfg_part_num": "PDSH4816AF",
            "part_desc": "PDSH4816AF Dishwasher SS - Display Only",
            "part_manuf": "Appliance Dealers Cooperative (APPDE)"
        }
        response = client.post("/api/playground/transform", json=payload)
        assert response.status_code == 200
        result = response.json()

        assert "invoice_desc" in result
        assert len(result["invoice_desc"]) <= 40
        assert result["invoice_desc"].isupper()
        assert 60 <= len(result["mobile_desc"]) <= 80
        assert "stages" in result
        assert len(result["stages"]) == 6
        assert result["total_latency_ms"] < 1000.0  # sub-second response
        assert len(result["delivery_columns"]) == 252

    def test_review_queue_and_mutations(self, client: TestClient):
        """Verify HITL review queue, update, and approval workflow."""
        # 1. Fetch queue
        response = client.get("/api/review/queue")
        assert response.status_code == 200
        queue_data = response.json()
        assert "items" in queue_data
        assert "total" in queue_data

        # 2. Test updating product 1
        update_payload = {
            "invoice_desc": "DISHWASHER 24IN SS BUILT-IN",
            "mobile_desc": "Frigidaire 24 In. Built-In Dishwasher in Stainless Steel with Wash Cycles",
            "short_desc": "Frigidaire® Gallery 24 In. Built-In Dishwasher",
            "status": "Validated"
        }
        put_resp = client.put("/api/review/1", json=update_payload)
        assert put_resp.status_code == 200
        updated = put_resp.json()
        assert updated["invoice_desc"] == "DISHWASHER 24IN SS BUILT-IN"
        assert updated["status"] == "Validated"

        # 3. Test approving product 1 without resolution is blocked (400)
        unverified_approve_resp = client.post("/api/review/1/approve", json={"approved": True, "notes": "Blind approval attempt"})
        assert unverified_approve_resp.status_code == 400
        assert "Promotion blocked" in unverified_approve_resp.json()["detail"]

        # 4. Resolve high-risk fields and verify successful approval (200)
        field_review = client.get("/api/review/1/fields").json()
        for f in field_review["fields"]:
            if f["is_high_risk"] and not f["is_resolved"]:
                client.post("/api/review/1/field-action", json={
                    "field_name": f["field_name"],
                    "action": "approve",
                    "reason": "Verified in test"
                })

        approve_resp = client.post("/api/review/1/approve", json={"approved": True, "notes": "Approved by QA test"})
        assert approve_resp.status_code == 200
        approve_data = approve_resp.json()
        assert approve_data["success"] is True
        assert approve_data["status"] == "Validated"

    def test_benchmark_results_endpoint(self, client: TestClient):
        """Verify /api/benchmark/results returns full ground-truth evaluation."""
        response = client.get("/api/benchmark/results")
        assert response.status_code == 200
        data = response.json()
        assert "overall_scores" in data
        assert "hard_rule_gates" in data
        assert "column_metrics" in data
        assert len(data["column_metrics"]) == 252
        assert data["overall_scores"]["exact_match_rate"] >= 0.80

    def test_export_columns_endpoint(self, client: TestClient):
        """Verify /api/export/columns returns all 252 headers and categorized groups."""
        response = client.get("/api/export/columns")
        assert response.status_code == 200
        data = response.json()
        assert data["total_columns"] == 252
        assert len(data["headers"]) == 252
        assert "groups" in data

    def test_export_csv_endpoint(self, client: TestClient):
        """Verify /api/export/csv returns valid 252-column CSV download."""
        response = client.get("/api/export/csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

        content = response.text
        df = pd.read_csv(io.StringIO(content))
        assert len(df.columns) == 252
        assert len(df) == 1000
        assert df.columns.tolist() == DeliveryMapper.get_column_headers()

    def test_export_xlsx_endpoint(self, client: TestClient):
        """Verify /api/export/xlsx returns valid Excel workbook."""
        response = client.get("/api/export/xlsx")
        assert response.status_code == 200
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers.get("content-type", "")
        
        # Verify read with pandas
        df = pd.read_excel(io.BytesIO(response.content))
        assert len(df.columns) == 252
        assert len(df) == 1000
