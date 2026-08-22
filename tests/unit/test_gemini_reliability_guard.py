"""
Unit tests for Gemini evidence reliability: MPN verification and token budgeting.
"""

from src.evidence.models import EvidenceChunk
from src.evidence.providers.base import ExtractionRequest, GeminiExtractionOutput, GeminiExtractedFact
from src.evidence.providers.gemini import GeminiEvidenceExtractionProvider


def test_gemini_rejects_citation_from_mismatched_mpn():
    """Verify that citations pointing to chunks belonging to a different product MPN are rejected."""
    provider = GeminiEvidenceExtractionProvider(enabled=False)

    chunk_different_mpn = EvidenceChunk(
        chunk_id="chunk_diff_mpn_1",
        source_id="src_1",
        mpn="DIFFERENT_MPN_123",
        brand="SharkBite",
        manufacturer="SharkBite",
        text_content="Pressure rating is 200 psi for model DIFFERENT_MPN_123.",
        section_title="Specifications",
        page_number=1,
        chunk_hash="hash_diff_1"
    )

    request = ExtractionRequest(
        mpn="TARGET_MPN_999",
        brand_candidate="SharkBite",
        manufacturer_candidate="SharkBite",
        source_chunks=[chunk_different_mpn],
        requested_fields=["Pressure Rating"],
        lov_subset={},
        uom_rules={}
    )

    output = GeminiExtractionOutput(
        mpn="TARGET_MPN_999",
        facts=[
            GeminiExtractedFact(
                field_name="Pressure Rating",
                raw_value="200 psi",
                normalized_candidate="200 psi",
                evidence_chunk_id="chunk_diff_mpn_1",
                evidence_excerpt="Pressure rating is 200 psi",
                confidence=0.95
            )
        ],
        unsupported_fields=[],
        conflicts=[]
    )

    verified_facts, conflicts = provider._post_verify_gemini_output(output, request)
    assert len(verified_facts) == 0  # Must be rejected because chunk MPN != target MPN


def test_gemini_select_relevant_chunks_token_budget():
    """Verify that chunk selector prioritizes relevant chunks and respects character/token budget."""
    provider = GeminiEvidenceExtractionProvider(enabled=False)

    chunks = [
        EvidenceChunk(
            chunk_id=f"chunk_{i}",
            source_id="src_1",
            mpn="MPN_TARGET",
            brand="SharkBite",
            manufacturer="SharkBite",
            text_content=f"Chunk {i}: " + ("General marketing filler text. " * 50),
            section_title="Marketing",
            page_number=i,
            chunk_hash=f"hash_{i}"
        )
        for i in range(10)
    ]
    # Insert high-relevance spec chunk at the end
    chunks.append(
        EvidenceChunk(
            chunk_id="spec_chunk",
            source_id="src_1",
            mpn="MPN_TARGET",
            brand="SharkBite",
            manufacturer="SharkBite",
            text_content="Specifications for MPN_TARGET: Voltage 120 V, Amperage 15 A, 200 psi.",
            section_title="Technical Specifications",
            page_number=11,
            chunk_hash="hash_spec"
        )
    )

    selected = provider._select_relevant_chunks(chunks, mpn="MPN_TARGET", max_char_budget=4000)
    selected_ids = [c.chunk_id for c in selected]
    assert "spec_chunk" in selected_ids
    total_len = sum(len(c.text_content) for c in selected)
    assert total_len <= 5000  # Stays within bounded budget
