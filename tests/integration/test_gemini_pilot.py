"""
End-to-End Pilot Test Suite for Gemini Evidence Extraction & Verification.

Covers the 3 pilot domains:
1. Fitting: U008LFA (SharkBite® Push-to-Connect Coupling)
2. Appliance: PDSH4816AF (Frigidaire® Gallery Built-In Dishwasher)
3. Abrasive: DCB518ASTS06G (Diablo® Sanding Belt 6-Pack)

Guarantees:
- Gemini disabled fallback works seamlessly
- Invalid citations and hallucinated quotes are rejected
- Source excerpt mismatches are rejected
- Products lacking official evidence cannot be approved
- Non-fabricated verified-only descriptions
- Optional live integration tests when GEMINI_ENABLED=true and GEMINI_API_KEY is configured
"""

import os
import pytest
from typing import Dict, Any

from src.evidence.models import EvidenceChunk
from src.evidence.providers.base import (
    BaseEvidenceExtractionProvider,
    ExtractionRequest,
    ExtractionResult,
    GeminiExtractedFact,
    GeminiExtractionOutput,
)
from src.evidence.providers.gemini import GeminiEvidenceExtractionProvider
from src.evidence.extractor import EvidenceAttributeExtractor
from src.evidence.enrichment_service import EvidenceEnrichmentService
from src.evidence.registry import EvidenceRegistryManager


@pytest.fixture
def registry():
    return EvidenceRegistryManager()


@pytest.fixture
def enrichment_service(registry):
    return EvidenceEnrichmentService(registry)


# ============================================================================
# 1. Pilot Product Verification Tests (Fitting, Appliance, Abrasive)
# ============================================================================

def test_pilot_product_1_fitting_verification(enrichment_service):
    """Verify Pilot Product 1 (Fitting: U008LFA)."""
    res = enrichment_service.enrich_product_attributes("U008LFA")
    assert res["status"] == "SUCCESS"
    attrs = res["enriched_attributes"]

    # Factual attributes backed by registered SharkBite spec sheet
    assert "Material" in attrs
    assert attrs["Material"]["status"] in ("verified", "candidate")
    assert attrs["Material"]["normalized_value"] == "Brass"

    assert "Connection Type" in attrs
    assert attrs["Connection Type"]["normalized_value"] == "Push-to-Connect"

    assert "Fitting Type" in attrs
    assert attrs["Fitting Type"]["normalized_value"] == "Coupling"

    # Descriptions must not contain unverified appliance specs
    desc = res["verified_descriptions"]
    assert "120 V" not in desc["short_desc"]
    assert "dBA" not in desc["short_desc"]
    assert "U008LFA" in desc["short_desc"]


def test_pilot_product_2_appliance_verification(enrichment_service):
    """Verify Pilot Product 2 (Appliance: PDSH4816AF)."""
    res = enrichment_service.enrich_product_attributes("PDSH4816AF")
    assert res["status"] == "SUCCESS"
    attrs = res["enriched_attributes"]

    assert "Voltage" in attrs
    assert attrs["Voltage"]["normalized_value"] == "120 V"

    assert "Sound Level" in attrs
    assert attrs["Sound Level"]["normalized_value"] == "47 dBA"

    assert "Mounting Type" in attrs
    assert attrs["Mounting Type"]["normalized_value"] == "Built-in"

    # Verified descriptions assembled strictly from verified evidence
    desc = res["verified_descriptions"]
    assert "PDSH4816AF" in desc["short_desc"]
    assert "47 dBA" in desc["short_desc"] or "120 V" in desc["short_desc"] or "Built-in" in desc["short_desc"]


def test_pilot_product_3_abrasive_verification(enrichment_service):
    """Verify Pilot Product 3 (Abrasive: DCB518ASTS06G)."""
    res = enrichment_service.enrich_product_attributes("DCB518ASTS06G")
    assert res["status"] == "SUCCESS"
    attrs = res["enriched_attributes"]

    assert "Material" in attrs
    assert attrs["Material"]["normalized_value"] == "Zirconia Alumina"

    desc = res["verified_descriptions"]
    assert "DCB518ASTS06G" in desc["short_desc"]
    # Ensure no fabricated appliance specs
    assert "120 V" not in desc["short_desc"]
    assert "dBA" not in desc["short_desc"]


# ============================================================================
# 2. Strict Governance, Refusal & Rejection Tests
# ============================================================================

def test_gemini_disabled_fallback_works():
    """Verify that when Gemini is disabled, pipeline falls back safely to deterministic rules."""
    provider = GeminiEvidenceExtractionProvider(enabled=False)
    assert provider.enabled is False

    req = ExtractionRequest(
        mpn="U008LFA",
        brand_candidate="SHARKBITE®",
        manufacturer_candidate="Reliance Worldwide Corporation",
        requested_fields=["Material", "Pressure Rating"],
    )
    result = provider.extract(req)
    assert result.status == "AI_EXTRACTION_UNAVAILABLE"
    assert result.ai_extraction_unavailable is True

    # Extractor uses deterministic fallback
    extractor = EvidenceAttributeExtractor(provider=provider)
    candidates = extractor.extract_candidates_for_mpn("U008LFA")
    assert len(candidates) >= 3
    for c in candidates:
        assert c.extraction_method == "deterministic_rule"


def test_invalid_chunk_citation_rejected(registry):
    """Verify that proposing a non-existent chunk ID is rejected with 0.0 confidence."""
    provider = GeminiEvidenceExtractionProvider(enabled=False)
    chunks = registry.load_chunks_for_entry(registry.get_entries_by_mpn("U008LFA")[0])

    output = GeminiExtractionOutput(
        mpn="U008LFA",
        facts=[
            GeminiExtractedFact(
                field_name="Material",
                raw_value="Cast Iron",
                evidence_chunk_id="chk_invalid_fake_chunk_9999",  # Does NOT exist
                evidence_excerpt="Material: Cast Iron",
                confidence=0.95,
            )
        ]
    )

    req = ExtractionRequest(mpn="U008LFA", source_chunks=chunks)
    verified_facts, _ = provider._post_verify_gemini_output(output, req)
    assert len(verified_facts) == 0


def test_source_excerpt_mismatch_rejected(registry):
    """Verify that an excerpt not physically present in the chunk is rejected as a hallucination."""
    provider = GeminiEvidenceExtractionProvider(enabled=False)
    chunks = registry.load_chunks_for_entry(registry.get_entries_by_mpn("U008LFA")[0])

    output = GeminiExtractionOutput(
        mpn="U008LFA",
        facts=[
            GeminiExtractedFact(
                field_name="Material",
                raw_value="Titanium",
                evidence_chunk_id=chunks[0].chunk_id,
                evidence_excerpt="Forged from high-grade aerospace titanium alloy.",  # Not in chunk!
                confidence=0.95,
            )
        ]
    )

    req = ExtractionRequest(mpn="U008LFA", source_chunks=chunks)
    verified_facts, _ = provider._post_verify_gemini_output(output, req)
    assert len(verified_facts) == 0


def test_product_with_missing_official_evidence_cannot_be_approved(enrichment_service):
    """Verify that an unbacked product with zero registered evidence returns NO_EVIDENCE_FOUND."""
    res = enrichment_service.enrich_product_attributes("NONEXISTENT_MPN_XYZ_999")
    assert res["status"] == "NO_EVIDENCE_FOUND"
    assert res.get("provenance_summary") is None
    assert len(res["enriched_attributes"]) == 0
    assert res["verified_descriptions"] == {}


# ============================================================================
# 3. Optional Live Integration Tests (Runs only when configured)
# ============================================================================

IS_LIVE_GEMINI_CONFIGURED = (
    os.getenv("GEMINI_ENABLED", "false").lower() in ("true", "1", "yes")
    and bool(os.getenv("GEMINI_API_KEY", "").strip())
)

@pytest.mark.skipif(
    not IS_LIVE_GEMINI_CONFIGURED,
    reason="Live Gemini pilot test skipped. Set GEMINI_ENABLED=true and GEMINI_API_KEY to execute."
)
def test_live_gemini_pilot_fitting(registry):
    """Live Gemini pilot test on Fitting (U008LFA)."""
    provider = GeminiEvidenceExtractionProvider(
        api_key=os.getenv("GEMINI_API_KEY"),
        enabled=True,
    )
    chunks = registry.load_chunks_for_entry(registry.get_entries_by_mpn("U008LFA")[0])
    req = ExtractionRequest(
        mpn="U008LFA",
        brand_candidate="SHARKBITE®",
        manufacturer_candidate="Reliance Worldwide Corporation",
        requested_fields=["Fitting Type", "Connection Type", "Material", "Nominal Size", "Pressure Rating"],
        lov_subset={
            "Fitting Type": ["Coupling", "90 deg Elbow", "Straight Tee"],
            "Material": ["Brass", "Copper", "Stainless Steel"],
        },
        source_chunks=chunks,
    )
    result = provider.extract(req)
    assert result.status == "SUCCESS"
    assert len(result.facts) >= 2


@pytest.mark.skipif(
    not IS_LIVE_GEMINI_CONFIGURED,
    reason="Live Gemini pilot test skipped. Set GEMINI_ENABLED=true and GEMINI_API_KEY to execute."
)
def test_live_gemini_pilot_appliance(registry):
    """Live Gemini pilot test on Appliance (PDSH4816AF)."""
    provider = GeminiEvidenceExtractionProvider(
        api_key=os.getenv("GEMINI_API_KEY"),
        enabled=True,
    )
    chunks = registry.load_chunks_for_entry(registry.get_entries_by_mpn("PDSH4816AF")[0])
    req = ExtractionRequest(
        mpn="PDSH4816AF",
        brand_candidate="FRIGIDAIRE®",
        manufacturer_candidate="Electrolux Home Products, Inc.",
        requested_fields=["Voltage", "Amps", "Sound Level", "Mounting Type", "Wash Cycles"],
        source_chunks=chunks,
    )
    result = provider.extract(req)
    assert result.status == "SUCCESS"
    assert len(result.facts) >= 2


@pytest.mark.skipif(
    not IS_LIVE_GEMINI_CONFIGURED,
    reason="Live Gemini pilot test skipped. Set GEMINI_ENABLED=true and GEMINI_API_KEY to execute."
)
def test_live_gemini_pilot_abrasive(registry):
    """Live Gemini pilot test on Abrasive (DCB518ASTS06G)."""
    provider = GeminiEvidenceExtractionProvider(
        api_key=os.getenv("GEMINI_API_KEY"),
        enabled=True,
    )
    chunks = registry.load_chunks_for_entry(registry.get_entries_by_mpn("DCB518ASTS06G")[0])
    req = ExtractionRequest(
        mpn="DCB518ASTS06G",
        brand_candidate="DIABLO®",
        manufacturer_candidate="Freud America, Inc.",
        requested_fields=["Material", "Belt Width", "Belt Length", "Grit"],
        source_chunks=chunks,
    )
    result = provider.extract(req)
    assert result.status == "SUCCESS"
    assert len(result.facts) >= 1
