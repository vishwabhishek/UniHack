"""
Unit and integration tests for the field-level provenance and evidence model.

Validates:
1. Field-level EvidenceRecord data structures and enum constraints.
2. Multi-record evidence support per field.
3. Raw input facts explicitly marked source_type=supplier_input.
4. Dictionary-normalized values include dictionary_identity.
5. Formatting rules alone do not confer verification_status=verified (kept as candidate).
6. Missing evidence is explicitly flagged as missing_evidence.
7. ProductProvenanceSummary computes accurate counters and verification score.
8. Backward compatibility of field_provenance dictionary.
"""

import pytest
from src.pipeline.models import (
    RawProduct,
    EnrichedProduct,
    EvidenceRecord,
    ProductProvenanceSummary,
    SourceType,
    ExtractionMethod,
    VerificationStatus
)
from src.pipeline.engine import EnrichmentEngine


@pytest.fixture
def engine():
    return EnrichmentEngine()


def test_evidence_record_structure_and_types():
    """Verify EvidenceRecord instantiation and attribute serialization."""
    rec = EvidenceRecord(
        field_name="brand_name",
        candidate_value="FRIGIDAIRE",
        normalized_value="FRIGIDAIRE®",
        source_url=None,
        source_type=SourceType.REFERENCE_DICTIONARY.value,
        source_title="UniCat Brand Master Index",
        source_page_or_section="Master Brand Registry",
        evidence_excerpt="Matched canonical alias in master dictionary",
        extraction_method=ExtractionMethod.DETERMINISTIC_RULE.value,
        confidence=0.98,
        verification_status=VerificationStatus.VERIFIED.value,
        dictionary_identity="UniCat_Manufacturer_and_Brand_List.json"
    )
    
    assert rec.field_name == "brand_name"
    assert rec.candidate_value == "FRIGIDAIRE"
    assert rec.normalized_value == "FRIGIDAIRE®"
    assert rec.source_type == "reference_dictionary"
    assert rec.source_title == "UniCat Brand Master Index"
    assert rec.extraction_method == "deterministic_rule"
    assert rec.verification_status == "verified"
    assert rec.dictionary_identity == "UniCat_Manufacturer_and_Brand_List.json"
    assert rec.confidence == 0.98
    assert rec.retrieved_at is not None


def test_multiple_evidence_records_per_field(engine):
    """Verify that fields like brand_name accumulate multiple evidence records (supplier input + dictionary)."""
    raw = RawProduct(
        mfg_part_num="DW-100",
        part_desc="24 in Built-In Dishwasher 120 V",
        part_manuf="Frigidaire (FRIG)",
        row_id=1
    )
    enriched = engine.process_item(raw)
    
    assert "brand_name" in enriched.field_evidence
    brand_records = enriched.field_evidence["brand_name"]
    assert len(brand_records) >= 2
    
    # First record: Raw supplier input observation
    rec1 = brand_records[0]
    assert rec1.source_type == SourceType.SUPPLIER_INPUT.value
    assert rec1.verification_status == VerificationStatus.CANDIDATE.value
    assert rec1.source_title == "Distributor Input Feed"
    
    # Second record: Canonical reference dictionary lookup
    rec2 = brand_records[1]
    assert rec2.source_type == SourceType.REFERENCE_DICTIONARY.value
    assert rec2.dictionary_identity == "UniCat_Manufacturer_and_Brand_List.json"
    assert rec2.verification_status == VerificationStatus.VERIFIED.value


def test_raw_input_facts_marked_supplier_input(engine):
    """Verify raw input extractions have source_type=supplier_input."""
    raw = RawProduct(
        mfg_part_num="VALVE-99",
        part_desc="Industrial Stainless Steel Ball Valve 1/2 in",
        part_manuf="Acme Flow Controls",
        row_id=2
    )
    enriched = engine.process_item(raw)
    
    mpn_ev = enriched.field_evidence["mfg_part_number"][0]
    assert mpn_ev.source_type == "supplier_input"
    assert mpn_ev.source_title == "Distributor Input Feed"


def test_rule_generated_fields_remain_candidate_status(engine):
    """Verify formatting formulas do not confer verified status (Rule 6)."""
    raw = RawProduct(
        mfg_part_num="DW-100",
        part_desc="24 in Built-In Dishwasher 120 V 15 A",
        part_manuf="Frigidaire",
        row_id=3
    )
    enriched = engine.process_item(raw)
    
    # INVOICE_DESC & MOBILE_DESC are rule-synthesized -> status must be 'candidate'
    invoice_ev = enriched.field_evidence["invoice_desc"][0]
    assert invoice_ev.verification_status == VerificationStatus.CANDIDATE.value
    assert invoice_ev.source_type == SourceType.SUPPLIER_INPUT.value
    
    mobile_ev = enriched.field_evidence["mobile_desc"][0]
    assert mobile_ev.verification_status == VerificationStatus.CANDIDATE.value


def test_unproven_fields_marked_missing_evidence(engine):
    """Verify unproven or blank fields are marked with missing_evidence status."""
    raw = RawProduct(
        mfg_part_num="VALVE-01",
        part_desc="Ball Valve 1/2 in",
        part_manuf="Acme",
        row_id=4
    )
    enriched = engine.process_item(raw)
    
    coo_ev = enriched.field_evidence["country_of_origin"][0]
    assert coo_ev.verification_status == VerificationStatus.MISSING_EVIDENCE.value
    assert coo_ev.normalized_value == ""
    
    img_ev = enriched.field_evidence["product_image"][0]
    assert img_ev.verification_status == VerificationStatus.MISSING_EVIDENCE.value


def test_product_provenance_summary_calculations(engine):
    """Verify ProductProvenanceSummary computes accurate counters and verification score."""
    raw = RawProduct(
        mfg_part_num="PDSH4816AF",
        part_desc="Built-In Dishwasher 24 in 120 V",
        part_manuf="Frigidaire",
        row_id=5
    )
    enriched = engine.process_item(raw)
    
    summary = enriched.provenance_summary
    assert summary is not None
    assert summary.total_fields_tracked > 0
    assert summary.verified_fields_count > 0
    assert summary.candidate_fields_count > 0
    assert summary.missing_evidence_count > 0
    assert 0.0 <= summary.verification_score <= 1.0
    assert "reference_dictionary" in summary.primary_sources_breakdown
    assert "supplier_input" in summary.primary_sources_breakdown


def test_backward_compatibility_field_provenance(engine):
    """Verify legacy field_provenance dictionary is preserved for existing consumers."""
    raw = RawProduct(
        mfg_part_num="COMPAT-01",
        part_desc="Industrial Cutting Blade 10 in",
        part_manuf="Diablo",
        row_id=6
    )
    enriched = engine.process_item(raw)
    
    assert "mfg_part_number" in enriched.field_provenance
    assert "brand_name" in enriched.field_provenance
    assert enriched.field_provenance["brand_name"].field_name == "brand_name"
