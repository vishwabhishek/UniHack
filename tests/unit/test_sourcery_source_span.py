"""
Unit tests for Sourcery-style source-span verification, grounding alignment,
refusal on hallucinated quotes, and Gemini document extraction schema.
"""

import pytest
from src.evidence.gemini_extractor import (
    ProposedFact,
    DocumentExtractionResponse,
    SourceSpanVerifier,
    GeminiExtractionAdapter,
)
from src.evidence.models import EvidenceChunk


@pytest.fixture
def sample_chunk():
    return EvidenceChunk(
        chunk_id="chk_sharkbite_u008lfa_01",
        source_id="src_u008lfa",
        mpn="U008LFA",
        brand="SharkBite®",
        manufacturer="Reliance Worldwide Corporation",
        section_title="Product Overview & Specifications",
        page_number=1,
        text_content=(
            "The SharkBite 1/2 in. Brass Push-to-Connect Straight Coupling is the easiest way to join copper, CPVC, or PEX pipe. "
            "Constructed of lead-free brass with corrosion-resistant finish. "
            "Rated for 200 psi maximum working pressure and 200 deg F."
        ),
        key_value_specs={
            "Fitting Type": "Straight Coupling",
            "Connection Type": "Push-to-Connect",
            "Material": "Lead-Free Brass",
            "Nominal Size": "1/2 in",
            "Pressure Rating": "200 psi",
        },
        chunk_hash="a1b2c3d4e5"
    )


def test_source_span_aligns_exact_quote(sample_chunk):
    """Verify that exact quote is aligned with precise character start and end offsets."""
    fact = ProposedFact(
        field_name="Material",
        raw_value="lead-free brass",
        exact_quote="Constructed of lead-free brass with corrosion-resistant finish.",
        chunk_id=sample_chunk.chunk_id,
        page_number=1
    )

    result = SourceSpanVerifier.align_and_verify(fact, sample_chunk.text_content)
    assert result.is_grounded is True
    assert result.start_char >= 0
    assert result.end_char > result.start_char
    assert result.alignment_score == 1.0
    assert sample_chunk.text_content[result.start_char:result.end_char] == fact.exact_quote


def test_source_span_rejects_hallucinated_quote(sample_chunk):
    """Sourcery rule: if the LLM invents a quote not in the document, refuse and mark ungrounded."""
    fact = ProposedFact(
        field_name="Voltage",
        raw_value="120 V",
        exact_quote="Operates on standard 120 V AC household power supply with 15 Amp breaker.",  # Not in chunk text!
        chunk_id=sample_chunk.chunk_id,
        page_number=1
    )

    result = SourceSpanVerifier.align_and_verify(fact, sample_chunk.text_content)
    assert result.is_grounded is False
    assert result.alignment_score == 0.0
    assert "hallucinated span" in result.rejection_reason.lower() or "not found" in result.rejection_reason.lower()


def test_source_span_rejects_value_not_in_quote(sample_chunk):
    """Sourcery rule: if the quote exists but does not support the claimed value, reject."""
    fact = ProposedFact(
        field_name="Pressure Rating",
        raw_value="600 psi",  # False claim
        exact_quote="Rated for 200 psi maximum working pressure and 200 deg F.",
        chunk_id=sample_chunk.chunk_id,
        page_number=1
    )

    result = SourceSpanVerifier.align_and_verify(fact, sample_chunk.text_content)
    assert result.is_grounded is False
    assert "does not appear" in result.rejection_reason.lower() or "not present" in result.rejection_reason.lower()


def test_gemini_adapter_deterministic_extraction(sample_chunk):
    """Verify GeminiExtractionAdapter extracts grounded facts in deterministic mode."""
    adapter = GeminiExtractionAdapter(api_key=None)  # Offline mode
    resp = adapter.extract_from_chunks(
        mpn="U008LFA",
        brand="SharkBite®",
        manufacturer="Reliance Worldwide Corporation",
        chunks=[sample_chunk]
    )

    assert isinstance(resp, DocumentExtractionResponse)
    assert resp.mpn == "U008LFA"
    assert len(resp.proposed_facts) >= 3

    # Check that material and connection type are extracted
    extracted_fields = {f.field_name: f for f in resp.proposed_facts}
    assert "Material" in extracted_fields
    assert "Connection Type" in extracted_fields

    # Verify that unmentioned fields (e.g. Voltage, Sound Level) are honestly refused
    assert "Voltage" in resp.unmentioned_fields or "Sound Level" in resp.unmentioned_fields
