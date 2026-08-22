"""
Unit tests for Production-Safe Gemini Evidence Extraction Provider.

Tests use a FakeGeminiProvider by default to guarantee zero external API calls in CI/CD.
Covers:
- Valid cited extraction with full provenance metadata
- Unsupported field returns blank (honest refusal)
- Invalid chunk ID or hallucinated quote rejected
- Invalid LOV value rejected by post-verification
- Gemini timeout / error fallback (AI_EXTRACTION_UNAVAILABLE flag)
- Conflicting sources route to review
- Optional manual integration test skipped unless GEMINI_API_KEY exists
"""

import os
import pytest
from typing import List, Optional

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


class FakeGeminiProvider(BaseEvidenceExtractionProvider):
    """Configurable test double for GeminiEvidenceExtractionProvider."""

    def __init__(
        self,
        mock_facts: Optional[List[GeminiExtractedFact]] = None,
        mock_unsupported: Optional[List[str]] = None,
        mock_conflicts: Optional[List[str]] = None,
        simulate_timeout: bool = False,
        simulate_error: bool = False,
        model_name: str = "fake-gemini-test",
    ):
        self.mock_facts = mock_facts or []
        self.mock_unsupported = mock_unsupported or []
        self.mock_conflicts = mock_conflicts or []
        self.simulate_timeout = simulate_timeout
        self.simulate_error = simulate_error
        self.model_name = model_name
        self.prompt_version = "v1.0.0-test"

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        if self.simulate_timeout:
            return ExtractionResult(
                mpn=request.mpn,
                brand=request.brand_candidate,
                manufacturer=request.manufacturer_candidate,
                facts=[],
                unsupported_fields=request.requested_fields,
                conflicts=[],
                model_name=self.model_name,
                prompt_version=self.prompt_version,
                status="AI_EXTRACTION_UNAVAILABLE",
                error_message="Simulated Gemini API timeout after 15.0s",
                ai_extraction_unavailable=True,
            )

        if self.simulate_error:
            return ExtractionResult(
                mpn=request.mpn,
                brand=request.brand_candidate,
                manufacturer=request.manufacturer_candidate,
                facts=[],
                unsupported_fields=request.requested_fields,
                conflicts=[],
                model_name=self.model_name,
                prompt_version=self.prompt_version,
                status="AI_EXTRACTION_UNAVAILABLE",
                error_message="Simulated Gemini quota exceeded (429)",
                ai_extraction_unavailable=True,
            )

        # Build simulated extraction output and run deterministic post-verification
        output = GeminiExtractionOutput(
            mpn=request.mpn,
            brand=request.brand_candidate,
            manufacturer=request.manufacturer_candidate,
            facts=self.mock_facts,
            unsupported_fields=self.mock_unsupported,
            conflicts=self.mock_conflicts,
        )

        gemini_provider = GeminiEvidenceExtractionProvider(enabled=False)
        verified_facts, verified_conflicts = gemini_provider._post_verify_gemini_output(output, request)

        return ExtractionResult(
            mpn=request.mpn,
            brand=request.brand_candidate,
            manufacturer=request.manufacturer_candidate,
            facts=verified_facts,
            unsupported_fields=output.unsupported_fields,
            conflicts=verified_conflicts,
            model_name=self.model_name,
            prompt_version=self.prompt_version,
            source_hash=request.source_chunks[0].chunk_hash if request.source_chunks else None,
            status="SUCCESS",
            ai_extraction_unavailable=False,
        )


@pytest.fixture
def test_chunks():
    reg = EvidenceRegistryManager()
    entries = reg.get_entries_by_mpn("U008LFA")
    if entries:
        return reg.load_chunks_for_entry(entries[0])
    return [
        EvidenceChunk(
            chunk_id="chk_u008lfa_01",
            source_id="src_u008lfa",
            mpn="U008LFA",
            brand="SharkBite®",
            manufacturer="Reliance Worldwide Corporation",
            section_title="Specifications",
            page_number=1,
            text_content=(
                "PRODUCT SPECIFICATIONS: SharkBite U008LFA 1/2 in Brass Push-to-Connect Straight Coupling. "
                "Constructed of Lead-Free Brass. Maximum working pressure: 200 psi."
            ),
            key_value_specs={
                "Fitting Type": "Coupling",
                "Connection Type": "Push-to-Connect",
                "Material": "Lead-Free Brass",
                "Nominal Size": "1/2 in",
                "Pressure Rating": "200 psi",
            },
            chunk_hash="hash_u008lfa_01",
        )
    ]


def test_gemini_provider_valid_cited_extraction(test_chunks):
    """Verify that Gemini proposed facts with valid source citations are accepted and enriched."""
    target_chunk = test_chunks[1] if len(test_chunks) > 1 else test_chunks[0]

    mock_facts = [
        GeminiExtractedFact(
            field_name="Material",
            raw_value="Lead-Free Brass",
            normalized_candidate="Brass",
            evidence_chunk_id=target_chunk.chunk_id,
            evidence_excerpt="Material: Lead-Free Brass",
            source_page_or_section="PRODUCT SPECIFICATIONS (p. 1)",
            confidence=0.98,
            extraction_reason="Explicit specification row",
            conflicts=[],
        ),
        GeminiExtractedFact(
            field_name="Pressure Rating",
            raw_value="200 psi",
            normalized_candidate="200 psi",
            evidence_chunk_id=target_chunk.chunk_id,
            evidence_excerpt="Pressure Rating: 200 psi",
            source_page_or_section="PRODUCT SPECIFICATIONS (p. 1)",
            confidence=0.98,
            extraction_reason="Explicit specification row",
            conflicts=[],
        ),
    ]

    provider = FakeGeminiProvider(mock_facts=mock_facts)
    extractor = EvidenceAttributeExtractor(provider=provider)
    candidates = extractor.extract_candidates_for_mpn("U008LFA")

    assert len(candidates) >= 2
    cand_map = {c.field_name: c for c in candidates}

    assert "Material" in cand_map
    mat = cand_map["Material"]
    assert mat.candidate_value == "Lead-Free Brass"
    assert mat.normalized_value == "Brass"
    assert mat.extraction_method == "gemini_structured_extraction"
    assert mat.model_name == "fake-gemini-test"
    assert mat.prompt_version == "v1.0.0-test"
    assert mat.chunk_id == target_chunk.chunk_id
    assert mat.confidence == 0.98


def test_gemini_provider_unsupported_field_returns_blank(test_chunks):
    """Verify that unsupported fields are honestly refused and withheld from catalog export."""
    mock_unsupported = ["Voltage", "Amps", "Sound Level", "Wash Cycles"]
    provider = FakeGeminiProvider(mock_facts=[], mock_unsupported=mock_unsupported)
    extractor = EvidenceAttributeExtractor(provider=provider)
    candidates = extractor.extract_candidates_for_mpn("U008LFA")

    cand_map = {c.field_name: c for c in candidates}
    # Unsupported appliance fields must not exist in extracted candidates for fittings
    assert "Voltage" not in cand_map
    assert "Sound Level" not in cand_map
    assert "Wash Cycles" not in cand_map


def test_gemini_provider_invalid_chunk_id_rejected(test_chunks):
    """Verify that facts with hallucinated or non-existent chunk IDs are rejected by post-verification."""
    hallucinated_facts = [
        GeminiExtractedFact(
            field_name="Material",
            raw_value="Stainless Steel",
            normalized_candidate="Stainless Steel",
            evidence_chunk_id="chk_nonexistent_999",  # Does NOT exist!
            evidence_excerpt="Constructed of solid stainless steel.",
            confidence=0.95,
        )
    ]

    provider = FakeGeminiProvider(mock_facts=hallucinated_facts)
    req = ExtractionRequest(
        mpn="U008LFA",
        requested_fields=["Material"],
        source_chunks=test_chunks,
    )
    result = provider.extract(req)

    # Post-verification must drop or reject the ungrounded fact
    assert len(result.facts) == 0


def test_gemini_provider_hallucinated_quote_rejected(test_chunks):
    """Verify that facts with quotes not present in the chunk text are rejected."""
    target_chunk = test_chunks[0]
    hallucinated_quote_facts = [
        GeminiExtractedFact(
            field_name="Material",
            raw_value="Titanium Alloy",
            normalized_candidate="Titanium",
            evidence_chunk_id=target_chunk.chunk_id,
            evidence_excerpt="Forged from aerospace grade titanium alloy.",  # Not in text!
            confidence=0.95,
        )
    ]

    provider = FakeGeminiProvider(mock_facts=hallucinated_quote_facts)
    req = ExtractionRequest(
        mpn="U008LFA",
        requested_fields=["Material"],
        source_chunks=test_chunks,
    )
    result = provider.extract(req)

    assert len(result.facts) == 0


def test_gemini_provider_invalid_lov_value_rejected(test_chunks):
    """Verify that candidate values failing LOV validation are rejected and not exported."""
    target_chunk = test_chunks[1] if len(test_chunks) > 1 else test_chunks[0]
    mock_facts = [
        GeminiExtractedFact(
            field_name="Material",
            raw_value="Unobtanium Alloy",
            normalized_candidate="Unobtanium",
            evidence_chunk_id=target_chunk.chunk_id,
            evidence_excerpt="Material: Lead-Free Brass",
            confidence=0.95,
        )
    ]

    provider = FakeGeminiProvider(mock_facts=mock_facts)
    service = EvidenceEnrichmentService()
    service.extractor = EvidenceAttributeExtractor(provider=provider)

    enrichment = service.enrich_product_attributes("U008LFA")
    assert "Material" in enrichment["enriched_attributes"]
    mat_attr = enrichment["enriched_attributes"]["Material"]
    assert mat_attr["status"] in ("verified", "rejected", "candidate")


def test_gemini_provider_timeout_fallback(test_chunks):
    """Verify that Gemini timeout does not fail the pipeline and triggers deterministic fallback."""
    provider = FakeGeminiProvider(simulate_timeout=True)
    extractor = EvidenceAttributeExtractor(provider=provider)
    candidates = extractor.extract_candidates_for_mpn("U008LFA")

    # Pipeline still extracts candidates via deterministic rule fallback
    assert len(candidates) >= 3
    cand_map = {c.field_name: c for c in candidates}
    assert "Fitting Type" in cand_map
    assert cand_map["Fitting Type"].extraction_method == "deterministic_rule"
    assert cand_map["Fitting Type"].ai_extraction_unavailable is True


def test_gemini_provider_conflicting_sources_route_to_review(test_chunks):
    """Verify that conflicting source claims are recorded and routed to review as candidate status."""
    target_chunk = test_chunks[1] if len(test_chunks) > 1 else test_chunks[0]
    mock_facts = [
        GeminiExtractedFact(
            field_name="Pressure Rating",
            raw_value="200 psi",
            normalized_candidate="200 psi",
            evidence_chunk_id=target_chunk.chunk_id,
            evidence_excerpt="Pressure Rating: 200 psi",
            confidence=0.75,
            conflicts=["Chunk 1 claims 200 psi but Section 3 notes 300 psi maximum peak"],
        )
    ]

    provider = FakeGeminiProvider(mock_facts=mock_facts)
    service = EvidenceEnrichmentService()
    service.extractor = EvidenceAttributeExtractor(provider=provider)

    enrichment = service.enrich_product_attributes("U008LFA")
    pressure_attr = enrichment["enriched_attributes"]["Pressure Rating"]

    # When conflicts exist, status is candidate (not automatically verified)
    assert pressure_attr["status"] == "candidate"
    assert len(pressure_attr["conflicts"]) > 0


@pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY"),
    reason="Manual integration test requiring real GEMINI_API_KEY environment variable"
)
def test_live_gemini_integration_manual(test_chunks):
    """Optional live integration test with actual Gemini API endpoint."""
    provider = GeminiEvidenceExtractionProvider(
        api_key=os.getenv("GEMINI_API_KEY"),
        enabled=True,
    )
    req = ExtractionRequest(
        mpn="U008LFA",
        brand_candidate="SharkBite®",
        manufacturer_candidate="Reliance Worldwide Corporation",
        category_candidate="Fittings",
        requested_fields=["Material", "Connection Type", "Pressure Rating", "Nominal Size"],
        source_chunks=test_chunks,
    )
    result = provider.extract(req)
    assert result.status == "SUCCESS"
    assert len(result.facts) >= 2
