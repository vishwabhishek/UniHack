"""
Unit tests for Batch Evidence-Enrichment Job Orchestrator, Persistent Caching, and State Machine.
"""

import os
import pytest
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from src.evidence.cache import GeminiExtractionCache
from src.evidence.batch_orchestrator import (
    BatchEnrichmentJobManager,
    ProductStatus,
    BatchJobStatus,
    ProductJobState,
    BatchReport,
)
from src.evidence.providers.base import (
    ExtractionRequest,
    ExtractionResult,
    GeminiExtractedFact,
)
from src.evidence.models import EvidenceChunk, SourceRegistryEntry
from src.evidence.registry import EvidenceRegistryManager


@pytest.fixture
def temp_cache():
    with TemporaryDirectory() as tmpdir:
        cache_file = Path(tmpdir) / "test_cache.json"
        cache = GeminiExtractionCache(cache_file_path=cache_file)
        yield cache


@pytest.fixture
def sample_extraction_result():
    return ExtractionResult(
        mpn="U008LFA",
        brand="SharkBite®",
        manufacturer="Reliance Worldwide Corporation",
        facts=[
            GeminiExtractedFact(
                field_name="Material",
                raw_value="Lead-Free Brass",
                normalized_candidate="Brass",
                evidence_chunk_id="chk_u008lfa_01",
                evidence_excerpt="Constructed of Lead-Free Brass.",
                confidence=0.98,
            )
        ],
        unsupported_fields=["Voltage"],
        conflicts=[],
        model_name="gemini-2.5-flash",
        prompt_version="v1.0.0",
        source_hash="hash_abc123",
        status="SUCCESS",
    )


def test_cache_key_generation_deterministic(temp_cache):
    """Verify that cache key is completely deterministic and varies with any input factor."""
    k1 = temp_cache.generate_cache_key(
        source_hash="hash_123",
        mpn="U008LFA",
        model_name="gemini-2.5-flash",
        schema_version="v1.0.0",
        lov_version="lov_v1",
    )
    k2 = temp_cache.generate_cache_key(
        source_hash="hash_123",
        mpn="U008LFA",
        model_name="gemini-2.5-flash",
        schema_version="v1.0.0",
        lov_version="lov_v1",
    )
    assert k1 == k2

    # Changing LOV version must yield different key
    k3 = temp_cache.generate_cache_key(
        source_hash="hash_123",
        mpn="U008LFA",
        model_name="gemini-2.5-flash",
        schema_version="v1.0.0",
        lov_version="lov_v2",
    )
    assert k1 != k3


def test_cache_hit_prevents_duplicate_call(temp_cache, sample_extraction_result):
    """Verify that cache hit returns cached ExtractionResult and increments hit stats."""
    cache_key = temp_cache.generate_cache_key("hash_abc123", "U008LFA", "gemini-2.5-flash", "v1.0.0", "lov_v1")

    # Initial get -> Miss
    assert temp_cache.get(cache_key) is None

    # Set cache
    temp_cache.set(
        cache_key=cache_key,
        mpn="U008LFA",
        source_hash="hash_abc123",
        model_name="gemini-2.5-flash",
        schema_version="v1.0.0",
        lov_version="lov_v1",
        result=sample_extraction_result,
        estimated_prompt_tokens=500,
        estimated_candidate_tokens=200,
    )

    # Second get -> Hit
    cached = temp_cache.get(cache_key)
    assert cached is not None
    assert cached.mpn == "U008LFA"
    assert len(cached.facts) == 1
    assert cached.facts[0].raw_value == "Lead-Free Brass"

    # Stats check
    stats = temp_cache.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["total_entries"] == 1
    assert stats["tokens_saved_estimate"] == 700


@pytest.mark.asyncio
async def test_batch_orchestrator_only_enqueues_registered_products(temp_cache):
    """Verify that batch enrichment processes only products with registered official manufacturer evidence."""
    manager = BatchEnrichmentJobManager(cache=temp_cache)
    report = await manager.start_batch_job(max_concurrency=2)

    assert report.job_id.startswith("batch_")
    assert report.evidence_backed_products > 0
    # Must only contain registered MPNs
    for mpn in report.product_states.keys():
        entries = manager.registry.get_entries_by_mpn(mpn)
        assert len(entries) > 0
        assert entries[0].source_status == "ACTIVE"


@pytest.mark.asyncio
async def test_batch_state_machine_and_report_metrics(temp_cache):
    """Verify that products transition through stages and produce accurate aggregate report metrics."""
    manager = BatchEnrichmentJobManager(cache=temp_cache)
    # Run batch on 2 specific registered products
    target_mpns = ["U008LFA", "SHXM4AY55N"]
    report = await manager.start_batch_job(mpns=target_mpns, max_concurrency=2)

    # Wait for batch completion
    for _ in range(50):
        if report.status in (BatchJobStatus.COMPLETED, BatchJobStatus.FAILED):
            break
        await asyncio.sleep(0.1)

    assert report.status == BatchJobStatus.COMPLETED
    assert report.processed_products == 2
    assert report.completed_products + report.review_required_products == 2
    assert report.verified_fields > 0
    assert report.token_usage["total_tokens"] >= 0

    # Verify per-product states
    for mpn, state in report.product_states.items():
        assert state.status in (ProductStatus.COMPLETED, ProductStatus.REVIEW_REQUIRED)
        assert state.duration_ms > 0
        assert state.started_at is not None
        assert state.completed_at is not None


@pytest.mark.asyncio
async def test_batch_transient_retry_mechanism(temp_cache):
    """Verify transient error retry backoff in batch worker."""
    manager = BatchEnrichmentJobManager(cache=temp_cache)
    p_state = ProductJobState(mpn="TEST_MPN", brand="Test", manufacturer="Test")

    call_count = 0

    def flaky_service():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RuntimeError("429 ResourceExhausted: rate limit exceeded")
        return {"enriched_attributes": {}, "provenance_summary": {"verified_fields_count": 1}}

    res = await manager._retry_transient_failures(flaky_service, p_state, max_retries=3)
    assert res is not None
    assert call_count == 3
    assert p_state.retry_count == 2


@pytest.mark.asyncio
async def test_batch_cancel_job(temp_cache):
    """Verify that job cancellation halts processing gracefully."""
    manager = BatchEnrichmentJobManager(cache=temp_cache)
    report = await manager.start_batch_job(max_concurrency=1)
    
    success = manager.cancel_job(report.job_id)
    assert success is True
    assert manager.cancellation_flags[report.job_id] is True
