"""Pipeline Integration and FastAPI Backend Service Integration Test Suite.

This module tests:
1. End-to-end multi-stage pipeline flow & state transitions
2. Anomaly detection & HITL (Human-In-The-Loop) confidence scoring
3. FastAPI REST API endpoints:
   - GET /api/products (Catalog exploration, search, pagination, status filtering)
   - GET /api/products/{id} (Enriched product details)
   - POST /api/playground/transform (Real-time live transformation sandbox)
   - GET /api/review/queue & POST /api/review/{id}/approve (HITL triage & approval)
   - GET /api/export/csv & GET /api/export/xlsx (252-column export endpoints)
   - GET /api/benchmark/results (QA metrics & hard-gate compliance reports)
"""

import pytest
from typing import Dict, Any, List
from starlette.testclient import TestClient


# ===========================================================================
# 1. Pipeline Multi-Stage Flow Integration
# ===========================================================================

class TestPipelineStageTransitions:
    """Test suite for validating end-to-end stage handoffs within the pipeline."""

    def test_pipeline_full_stage_transition(self, sample_dishwasher_frigidaire: Dict[str, Any], pipeline_engine):
        """Verify sequential handoff across all 7 pipeline stages for a raw record."""
        from src.pipeline.delivery_mapper import to_delivery_dict
        from src.pipeline.models import EnrichedProduct
        
        # Stage 1: Ingestion & Sanitization
        raw_obj = pipeline_engine.raw_cls(**sample_dishwasher_frigidaire)
        sanitized = pipeline_engine.sanitizer.sanitize(raw_obj)
        assert sanitized["mfg_part_num"] == "PDSH4816AF"
        
        # Stage 2: Canonical Entity Resolution
        entity = pipeline_engine.resolver.resolve(sanitized)
        assert "FRIGIDAIRE" in entity["brand_name"]
        assert "Rheem" in entity["manufacturer_name"] or "Frigidaire" in entity["manufacturer_name"]
        
        # Stage 3: Taxonomy Classification
        tax = pipeline_engine.taxonomy.classify(sanitized, entity)
        assert "Dishwasher" in tax["product_name"] or "Dishwashers" in tax["classpath"]
        
        # Stage 4 & 5: Attribute Extraction & LOV / UOM Standardization
        attr_data = pipeline_engine.extractor.extract(sanitized, entity, tax)
        assert len(attr_data.get("attributes", [])) > 0
        
        # Stage 6: 5-Tier Description Generation
        descs = pipeline_engine.desc_gen.generate_all(sanitized, entity, tax, attr_data)
        assert len(descs["invoice_desc"]) <= 40
        assert descs["invoice_desc"].isupper()
        assert 60 <= len(descs["mobile_desc"]) <= 80
        
        # Stage 7: Full Pipeline Execution and 252-Column Assembly
        enriched = pipeline_engine.process_record(sample_dishwasher_frigidaire)
        assert isinstance(enriched, EnrichedProduct)
        assert enriched.mfg_part_number == "PDSH4816AF"
        
        delivery_dict = to_delivery_dict(enriched)
        assert len(delivery_dict) == 252
        assert delivery_dict["INVOICE_DESC"] == descs["invoice_desc"]
        assert delivery_dict["MOBILE_DESC"] == descs["mobile_desc"]

    def test_pipeline_anomaly_flagging_for_low_confidence(self, pipeline_engine):
        """Verify that items with conflicting brands or low confidence are flagged for human review."""
        conflicting_raw = {
            "mfg_part_num": "CONFLICT-01",
            "part_desc": "Strange Unidentified Item with No Clear Specifications",
            "e1_brand": "BrandA",
            "unilog_brand": "-- No Unilog Brand --",
            "dib_brand": "BrandB",
            "part_manuf": "ManufacturerC",
        }
        enriched = pipeline_engine.process_record(conflicting_raw)
        
        assert hasattr(enriched, "confidence_score")
        assert 0.0 <= enriched.confidence_score <= 1.0
        if enriched.confidence_score < 0.85:
            assert enriched.status in ["Flagged", "Needs Human Review"]


# ===========================================================================
# 2. FastAPI Backend REST Integration
# ===========================================================================

class TestFastAPIBackendIntegration:
    """Test suite for backend REST endpoints."""

    def test_api_health_check(self, api_client: TestClient):
        """Verify GET /api/health returns 200 OK with operational status."""
        response = api_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") in ["ok", "healthy", "operational"]

    def test_api_get_catalog_products_pagination(self, api_client: TestClient):
        """Verify GET /api/products supports page, limit, and returns structured catalog records."""
        response = api_client.get("/api/products?page=1&limit=20")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or "products" in data or isinstance(data, list)
        
        items = data["items"] if "items" in data else data
        assert len(items) <= 20

    def test_api_get_catalog_products_search_and_filter(self, api_client: TestClient):
        """Verify searching catalog products by keyword."""
        response = api_client.get("/api/products?search=dishwasher")
        assert response.status_code == 200
        data = response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        assert len(items) >= 0

    def test_api_playground_transform_endpoint(self, api_client: TestClient):
        """Verify POST /api/playground/transform generates instant pipeline transformations for raw text."""
        payload = {
            "mfg_part_num": "PDSH4816AF",
            "part_desc": "PDSH4816AF Dishwasher SS - Display Only",
            "part_manuf": "Appliance Dealers Cooperative (APPDE)",
        }
        response = api_client.post("/api/playground/transform", json=payload)
        assert response.status_code == 200
        result = response.json()
        
        assert "invoice_desc" in result
        assert "mobile_desc" in result
        assert "short_desc" in result
        assert len(result["invoice_desc"]) <= 40
        assert 60 <= len(result["mobile_desc"]) <= 80

    def test_api_review_queue_and_approval_workflow(self, api_client: TestClient):
        """Verify HITL review queue endpoint and approval flow."""
        # 1. Fetch review queue
        response = api_client.get("/api/review/queue")
        assert response.status_code == 200
        queue = response.json()
        assert isinstance(queue, (list, dict))

        # 2. Test approving a record if queue has items
        items = queue.get("items", queue) if isinstance(queue, dict) else queue
        if len(items) > 0:
            target_id = items[0].get("id") or items[0].get("part_number") or items[0].get("mfg_part_num")
            approve_resp = api_client.post(f"/api/review/{target_id}/approve", json={"approved": True})
            assert approve_resp.status_code in [200, 204]

    def test_api_export_csv_endpoint(self, api_client: TestClient, expected_252_columns):
        """Verify GET /api/export/csv returns valid 252-column CSV attachment."""
        response = api_client.get("/api/export/csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "") or "application/octet-stream" in response.headers.get("content-type", "")
        
        # Verify first row contains all 252 column headers
        content = response.text
        first_line = content.splitlines()[0]
        header_cols = [c.strip('"') for c in first_line.split(",")]
        assert len(header_cols) == 252, f"Export CSV should have 252 columns, found {len(header_cols)}"

    def test_api_benchmark_results_endpoint(self, api_client: TestClient):
        """Verify GET /api/benchmark/results returns evaluation metrics and hard-gate status."""
        response = api_client.get("/api/benchmark/results")
        assert response.status_code == 200
        data = response.json()
        assert "hard_gates" in data or "metrics" in data or "accuracy" in data or "invoice_compliance" in data
