"""
Unit and integration tests for official manufacturer evidence attribute enrichment,
LOV validation, UOM normalization, and verified-only description generation.
"""

import pytest
from fastapi.testclient import TestClient

from src.evidence.enrichment_service import EvidenceEnrichmentService
from src.backend.main import app
from src.backend.auth import user_store, create_access_token


@pytest.fixture
def enrichment_service():
    return EvidenceEnrichmentService()


@pytest.fixture
def auth_headers():
    admin = user_store.get_by_email("admin@unilog.com")
    if not admin:
        user_store._bootstrap_initial_admin()
        admin = user_store.get_by_email("admin@unilog.com")
    token = create_access_token(admin)
    return {"Authorization": f"Bearer {token}"}


class TestEvidenceAttributeEnrichment:
    """Test suite covering the 6-step evidence enrichment lifecycle."""

    def test_fitting_enrichment_copper_elbow(self, enrichment_service: EvidenceEnrichmentService):
        """Test Nibco 1/2 in copper 90 deg elbow evidence enrichment."""
        res = enrichment_service.enrich_product_attributes("NIB-607-1/2")
        assert res["status"] == "SUCCESS"
        assert res["brand"] == "NIBCO®"
        assert res["manufacturer"] == "NIBCO INC."
        
        attrs = res["enriched_attributes"]
        assert "Fitting Type" in attrs
        assert attrs["Fitting Type"]["normalized_value"] == "90 deg Elbow"
        assert attrs["Fitting Type"]["candidate_value"] == "90 deg Elbow"
        
        assert "Connection Type" in attrs
        assert attrs["Connection Type"]["normalized_value"] == "Sweat"
        
        assert "Material" in attrs
        assert attrs["Material"]["normalized_value"] == "Copper"
        
        assert "Nominal Size" in attrs
        assert attrs["Nominal Size"]["normalized_value"] == "1/2 in"
        
        assert "Pressure Rating" in attrs
        assert attrs["Pressure Rating"]["normalized_value"] == "300 psi"
        
        # Descriptions assembled only from verified fields
        descs = res["verified_descriptions"]
        assert "90 deg Elbow" in descs["short_desc"]
        assert "Copper" in descs["short_desc"]
        assert "300 psi" in descs["long_desc1"]
        assert len(descs["invoice_desc"]) <= 40
        assert descs["invoice_desc"].isupper()
        assert "90 ELB" in descs["invoice_desc"]
        assert "CU" in descs["invoice_desc"]

    def test_fitting_enrichment_push_coupling(self, enrichment_service: EvidenceEnrichmentService):
        """Test SharkBite 1/2 in push-to-connect brass coupling evidence enrichment."""
        res = enrichment_service.enrich_product_attributes("U008LFA")
        assert res["status"] == "SUCCESS"
        assert res["brand"] == "SHARKBITE®"
        
        attrs = res["enriched_attributes"]
        assert attrs["Fitting Type"]["normalized_value"] == "Coupling"
        assert attrs["Connection Type"]["normalized_value"] == "Push-to-Connect"
        # Candidate value Lead-Free Brass preserved separately from normalized Brass
        assert attrs["Material"]["candidate_value"] == "Lead-Free Brass"
        assert attrs["Material"]["normalized_value"] == "Brass"
        assert attrs["Nominal Size"]["normalized_value"] == "1/2 in"
        assert attrs["Pressure Rating"]["normalized_value"] == "200 psi"
        
        descs = res["verified_descriptions"]
        assert "Push-to-Connect" in descs["short_desc"]
        assert "Brass" in descs["short_desc"]
        assert "200 psi" in descs["long_desc1"]
        assert len(descs["invoice_desc"]) <= 40
        assert "CPLG BRS PUSH" in descs["invoice_desc"]

    def test_faucet_enrichment(self, enrichment_service: EvidenceEnrichmentService):
        """Test Moen Pulldown Faucet evidence enrichment."""
        res = enrichment_service.enrich_product_attributes("7594SRS")
        assert res["status"] == "SUCCESS"
        assert res["brand"] == "MOEN®"
        
        attrs = res["enriched_attributes"]
        assert attrs["Faucet Type"]["normalized_value"] == "Pull-Down Faucet"
        assert attrs["Color / Finish"]["normalized_value"] == "Spot Resist Stainless"
        assert attrs["Flow Rate"]["normalized_value"] == "1.5 gpm"
        assert attrs["Connection Type"]["normalized_value"] == "Compression"
        
        descs = res["verified_descriptions"]
        assert "Spot Resist Stainless" in descs["short_desc"]
        assert "Pull-Down Faucet" in descs["short_desc"]
        assert "1.5 gpm" in descs["long_desc1"]
        assert len(descs["invoice_desc"]) <= 40
        assert "FAUCET PULL-DWN" in descs["invoice_desc"]

    def test_provenance_evidence_records_lineage(self, enrichment_service: EvidenceEnrichmentService):
        """Verify that every field contains an EvidenceRecord with citations and source URL."""
        res = enrichment_service.enrich_product_attributes("NIB-607-1/2")
        evidence_map = res["field_evidence"]
        
        for field_name, ev_list in evidence_map.items():
            assert len(ev_list) >= 1
            ev = ev_list[0]
            assert ev.field_name == field_name
            assert ev.source_type == "manufacturer_page"
            assert "nibco.com" in (ev.source_url or "")
            assert ev.source_page_or_section != ""
            assert ev.evidence_excerpt != ""
            assert ev.confidence >= 0.95
            assert ev.verification_status in ["verified", "rejected"]

    def test_descriptions_do_not_hallucinate_unbacked_attributes(self, enrichment_service: EvidenceEnrichmentService):
        """Rule: Product titles and descriptions must NOT contain attributes lacking evidence."""
        # SHC1023 has no pressure rating in its evidence
        res = enrichment_service.enrich_product_attributes("SHC1023")
        descs = res["verified_descriptions"]
        
        # Verify no pressure rating is in short_desc or long_desc1
        assert "Pressure Rating" not in res["enriched_attributes"]
        assert "psi" not in descs["short_desc"].lower()
        assert "psi" not in descs["long_desc1"].lower()
        assert "psi" not in descs["invoice_desc"].lower()

    def test_rejection_of_unsupported_candidate(self, enrichment_service: EvidenceEnrichmentService):
        """Verify that candidates failing LOV validation are rejected with status 'rejected'."""
        is_valid, norm_val, dict_name = enrichment_service._validate_and_normalize_lov(
            field_name="Fitting Type",
            raw_val="CompletelyFakeWidgetFitting999",
            tentative_norm="CompletelyFakeWidgetFitting999"
        )
        assert is_valid is False
        assert norm_val == ""

    def test_fastapi_enrich_endpoint(self, auth_headers):
        """Verify POST /api/evidence/enrich/{mpn} endpoint."""
        client = TestClient(app)
        res = client.post("/api/evidence/enrich/NIB-607-1/2", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["mpn"] == "NIB-607-1/2"
        assert "Fitting Type" in data["enriched_attributes"]
        assert data["provenance_summary"]["verification_score"] >= 80.0
        assert "verified_descriptions" in data
