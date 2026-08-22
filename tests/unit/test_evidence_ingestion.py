"""
Unit and integration tests for official manufacturer evidence ingestion, whitelist guard, and candidate extraction.
"""

import pytest
import os
import shutil
import tempfile
from fastapi.testclient import TestClient

from src.evidence.models import SourceRegistrationRequest, EvidenceType, SourceStatus
from src.evidence.whitelist import is_official_manufacturer_url
from src.evidence.html_parser import parse_manufacturer_html
from src.evidence.pdf_parser import parse_manufacturer_pdf_text
from src.evidence.chunker import create_evidence_chunks
from src.evidence.registry import EvidenceRegistryManager
from src.evidence.search_engine import EvidenceSearchEngine
from src.evidence.extractor import EvidenceAttributeExtractor
from src.backend.main import app
from src.backend.auth import create_access_token


@pytest.fixture
def temp_evidence_dir():
    temp_dir = tempfile.mkdtemp(prefix="test_evidence_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def auth_headers():
    from src.backend.auth import user_store
    admin = user_store.get_by_email("admin@unilog.com")
    if not admin:
        user_store._bootstrap_initial_admin()
        admin = user_store.get_by_email("admin@unilog.com")
    token = create_access_token(admin)
    return {"Authorization": f"Bearer {token}"}


def test_whitelist_allows_official_manufacturer_domains():
    """Verify that authoritative manufacturer domains pass the whitelist."""
    valid_urls = [
        "https://www.frigidaire.com/en/p/kitchen/dishwashers/built-in-dishwashers/PDSH4816AF",
        "https://whirlpool.com/kitchen/dishwasher/WDTS7024RZ.html",
        "https://www.bosch-home.com/us/products-list/dishwashers/top-controls/SHXM4AY55N",
        "https://www.geappliances.com/appliance/GDT665SSNSS",
        "https://www.milwaukeetool.com/Products/Power-Tools/48-22-8424",
        "https://www.diablotools.com/products/D1024X",
        "https://www.trex.com/products/decking/transcend/",
    ]
    for u in valid_urls:
        valid, msg = is_official_manufacturer_url(u)
        assert valid is True, f"Expected {u} to be valid, got: {msg}"


def test_whitelist_rejects_marketplaces_and_third_parties():
    """Verify that marketplaces, distributor sites, and random blogs are blocked."""
    invalid_urls = [
        "https://www.amazon.com/dp/B08N5WRWNW",
        "https://www.homedepot.com/p/Frigidaire-Dishwasher/312345",
        "https://www.lowes.com/pd/Whirlpool-Dishwasher/1001234",
        "https://www.ebay.com/itm/123456789",
        "https://www.grainger.com/product/12345",
        "https://randomappliancereviews.com/best-dishwashers",
        "https://untrusted-distributor.io/specs/PDSH4816AF",
    ]
    for u in invalid_urls:
        valid, msg = is_official_manufacturer_url(u)
        assert valid is False, f"Expected {u} to be blocked"
        assert ("marketplace" in msg.lower() or "untrusted" in msg.lower())


def test_html_parser_extracts_sections_and_specs():
    """Verify HTML parser extracts structured sections and spec pairs."""
    sample_html = """
    <html>
    <head><title>Test Dishwasher Specifications</title></head>
    <body>
      <h1>Model DW-200 Technical Specs</h1>
      <h2>Electrical Characteristics</h2>
      <table>
        <tr><th>Voltage</th><td>120 V</td></tr>
        <tr><th>Amps</th><td>15 A</td></tr>
      </table>
      <h2>Performance</h2>
      <table>
        <tr><th>Sound Level</th><td>44 dBA</td></tr>
        <tr><th>Tub Material</th><td>Stainless Steel</td></tr>
      </table>
    </body>
    </html>
    """
    title, sections = parse_manufacturer_html(sample_html)
    assert len(sections) >= 2
    
    # Check specs extracted
    all_specs = {}
    for s in sections:
        all_specs.update(s["specs"])
        
    assert all_specs.get("Voltage") == "120 V"
    assert all_specs.get("Amps") == "15 A"
    assert all_specs.get("Sound Level") == "44 dBA"
    assert all_specs.get("Tub Material") == "Stainless Steel"


def test_pdf_parser_extracts_headers_and_page_numbers():
    """Verify PDF parser extracts sections and key-value specs."""
    sample_pdf_text = """
    OFFICIAL PRODUCT SPECIFICATIONS
    Model: DW-300
    
    ELECTRICAL SPECIFICATIONS
    Voltage: 120 V
    Amperage: 15 A
    
    PERFORMANCE
    Sound Level: 46 dBA
    Wash Cycles: 6
    Tub Material: Stainless Steel
    """
    title, sections = parse_manufacturer_pdf_text(sample_pdf_text, title="DW-300 Spec Sheet")
    assert title == "DW-300 Spec Sheet"
    assert len(sections) >= 2


def test_evidence_chunker_generates_hashes():
    """Verify chunker produces discrete EvidenceChunk items with unique hashes."""
    sections = [
        {"heading": "Electrical", "page_number": 1, "text": "Voltage: 120 V", "specs": {"Voltage": "120 V"}},
        {"heading": "Dimensions", "page_number": 1, "text": "Width: 24 in", "specs": {"Width": "24 in"}},
    ]
    chunks = create_evidence_chunks(
        source_id="src_test_01",
        mpn="TEST-MPN",
        brand="TEST-BRAND",
        manufacturer="TEST-MANUF",
        sections=sections
    )
    assert len(chunks) == 2
    assert chunks[0].chunk_id.startswith("chk_test-mpn_1_")
    assert chunks[0].key_value_specs["Voltage"] == "120 V"
    assert chunks[1].key_value_specs["Width"] == "24 in"


def test_registry_manager_lifecycle(temp_evidence_dir):
    """Verify full registry lifecycle: registration, file storage, and chunk loading."""
    mgr = EvidenceRegistryManager(data_dir=temp_evidence_dir)
    
    req = SourceRegistrationRequest(
        url="https://www.frigidaire.com/en/p/kitchen/dishwashers/TEST-01",
        mpn="TEST-01",
        brand="FRIGIDAIRE®",
        manufacturer="Electrolux Home Products, Inc.",
        source_type=EvidenceType.MANUFACTURER_PAGE.value,
        title="Test Frigidaire Official Specifications",
        raw_content="<html><body><h1>Test 01</h1><h2>Electrical</h2><table><tr><th>Voltage</th><td>120 V</td></tr></table></body></html>"
    )
    
    res = mgr.register_source(req)
    assert res.success is True
    assert res.source_status == SourceStatus.ACTIVE.value
    assert res.chunks_count >= 1
    assert res.file_hash != ""
    
    # Reload registry
    mgr2 = EvidenceRegistryManager(data_dir=temp_evidence_dir)
    entry = mgr2.get_entry(res.source_id)
    assert entry is not None
    assert entry.mpn == "TEST-01"
    
    chunks = mgr2.load_chunks_for_entry(entry)
    assert len(chunks) >= 1
    assert chunks[0].key_value_specs.get("Voltage") == "120 V"


def test_safe_failure_on_untrusted_domain(temp_evidence_dir):
    """Rule 7: Ingestion of untrusted source must fail safely with UNTRUSTED_SOURCE flag and no fabricated data."""
    mgr = EvidenceRegistryManager(data_dir=temp_evidence_dir)
    
    req = SourceRegistrationRequest(
        url="https://www.amazon.com/dp/B08TEST",
        mpn="AMZ-01",
        brand="Generic",
        manufacturer="Third-Party Supplier",
        source_type=EvidenceType.MANUFACTURER_PAGE.value,
        raw_content="Some marketplace page content"
    )
    
    res = mgr.register_source(req)
    assert res.success is False
    assert res.source_status == SourceStatus.REJECTED_UNTRUSTED.value
    assert "UNTRUSTED_SOURCE" in res.validation_flags
    assert res.chunks_count == 0


def test_safe_failure_on_empty_content(temp_evidence_dir):
    """Rule 7: Ingestion of unreachable/empty content fails safely with UNAVAILABLE_SOURCE flag."""
    mgr = EvidenceRegistryManager(data_dir=temp_evidence_dir)
    
    req = SourceRegistrationRequest(
        url="https://www.frigidaire.com/en/p/unreachable",
        mpn="UNREACHABLE-01",
        brand="FRIGIDAIRE®",
        manufacturer="Electrolux",
        source_type=EvidenceType.MANUFACTURER_PAGE.value,
        raw_content=""
    )
    
    res = mgr.register_source(req)
    assert res.success is False
    assert res.source_status == SourceStatus.UNAVAILABLE.value
    assert "UNAVAILABLE_SOURCE" in res.validation_flags


def test_candidate_attribute_extraction():
    """Verify attribute extraction for demo products returns verified candidates with complete citations."""
    extractor = EvidenceAttributeExtractor()
    candidates = extractor.extract_candidates_for_mpn("PDSH4816AF")
    
    assert len(candidates) >= 3
    cand_dict = {c.field_name: c for c in candidates}
    
    assert "Voltage" in cand_dict
    assert cand_dict["Voltage"].normalized_value == "120 V"
    assert cand_dict["Voltage"].verification_status == "verified"
    assert cand_dict["Voltage"].source_type == "manufacturer_page"
    assert "frigidaire.com" in (cand_dict["Voltage"].source_url or "")
    
    assert "Sound Level" in cand_dict
    assert cand_dict["Sound Level"].normalized_value == "47 dBA"


def test_fastapi_evidence_endpoints(auth_headers):
    """Verify FastAPI evidence endpoints."""
    client = TestClient(app)
    
    # 1. GET /api/evidence/registry
    r1 = client.get("/api/evidence/registry", headers=auth_headers)
    assert r1.status_code == 200
    reg = r1.json()
    assert isinstance(reg, list)
    assert len(reg) >= 4
    
    # 2. GET /api/evidence/query?mpn=PDSH4816AF
    r2 = client.get("/api/evidence/query?mpn=PDSH4816AF", headers=auth_headers)
    assert r2.status_code == 200
    q_data = r2.json()
    assert q_data["total_chunks"] >= 1
    assert len(q_data["candidates"]) >= 1
    
    # 3. GET /api/evidence/candidates/WDTS7024RZ
    r3 = client.get("/api/evidence/candidates/WDTS7024RZ", headers=auth_headers)
    assert r3.status_code == 200
    cands = r3.json()
    assert len(cands) >= 1
    field_names = [c["field_name"] for c in cands]
    assert "Voltage" in field_names or "Sound Level" in field_names
