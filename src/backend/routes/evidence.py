"""
FastAPI Routes for Official Manufacturer Evidence Ingestion, Search, and Candidate Lineage.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query, Depends

from ..auth import User, get_current_user, require_roles

from ...evidence.models import (
    SourceRegistryEntry,
    SourceRegistrationRequest,
    SourceRegistrationResponse,
    EvidenceQueryResponse,
    ExtractedCandidate
)
from ...evidence.registry import EvidenceRegistryManager
from ...evidence.search_engine import EvidenceSearchEngine
from ...evidence.extractor import EvidenceAttributeExtractor

router = APIRouter(prefix="/api/evidence", tags=["Evidence Ingestion"])
registry_manager = EvidenceRegistryManager()
search_engine = EvidenceSearchEngine(registry_manager)
extractor = EvidenceAttributeExtractor(registry_manager)


@router.get("/registry", response_model=List[SourceRegistryEntry])
def get_source_registry(current_user: User = Depends(get_current_user)):
    """Retrieve all registered official manufacturer evidence sources with hashes and statuses."""
    return registry_manager.load_registry()


class SupersedeSourceRequest(BaseModel):
    new_source_id: str
    reason: Optional[str] = "Superseded by newer manufacturer source"


class RejectSourceRequest(BaseModel):
    reason: str


class MarkStaleRequest(BaseModel):
    reason: Optional[str] = "Marked stale by specialist"


@router.post("/register", response_model=SourceRegistrationResponse)
def register_manufacturer_evidence(
    req: SourceRegistrationRequest,
    current_user: User = Depends(require_roles(["admin", "specialist"]))
):
    """
    Register and ingest an official manufacturer product specification page or PDF.
    Enforces strict manufacturer-only domain whitelist and SHA256 integrity verification.
    """
    res = registry_manager.register_source(req)
    if not res.success and "UNTRUSTED_SOURCE" in res.validation_flags:
        raise HTTPException(
            status_code=400,
            detail=f"Registration rejected: {res.message}"
        )
    return res


@router.post("/source/{source_id}/mark-stale")
def mark_source_stale(
    source_id: str,
    payload: Optional[MarkStaleRequest] = None,
    current_user: User = Depends(require_roles(["admin", "specialist"]))
):
    """Mark an evidence source as stale and invalidate its extraction cache."""
    reason = payload.reason if payload else "Marked stale by specialist"
    success = registry_manager.mark_source_stale(source_id, reason=reason)
    if not success:
        raise HTTPException(status_code=404, detail=f"Evidence source '{source_id}' not found.")
    return {"status": "success", "source_id": source_id, "source_status": "STALE", "message": f"Source marked stale: {reason}"}


@router.post("/source/{source_id}/supersede")
def supersede_source(
    source_id: str,
    payload: SupersedeSourceRequest,
    current_user: User = Depends(require_roles(["admin", "specialist"]))
):
    """Supersede an evidence source with a newer registered source."""
    success = registry_manager.supersede_source(source_id, new_source_id=payload.new_source_id, reason=payload.reason)
    if not success:
        raise HTTPException(status_code=404, detail=f"Evidence source '{source_id}' not found.")
    return {
        "status": "success",
        "source_id": source_id,
        "superseded_by": payload.new_source_id,
        "source_status": "SUPERSEDED",
        "message": f"Source superseded by {payload.new_source_id}: {payload.reason}"
    }


@router.post("/source/{source_id}/reject")
def reject_source(
    source_id: str,
    payload: RejectSourceRequest,
    current_user: User = Depends(require_roles(["admin", "specialist"]))
):
    """Reject an evidence source and invalidate its extraction cache."""
    success = registry_manager.reject_source(source_id, reason=payload.reason)
    if not success:
        raise HTTPException(status_code=404, detail=f"Evidence source '{source_id}' not found.")
    return {"status": "success", "source_id": source_id, "source_status": "REJECTED_UNTRUSTED", "message": f"Source rejected: {payload.reason}"}


@router.post("/source/{source_id}/re-ingest", response_model=SourceRegistrationResponse)
def reingest_source(
    source_id: str,
    current_user: User = Depends(require_roles(["admin", "specialist"]))
):
    """Re-acquire and re-parse an evidence source by URL."""
    res = registry_manager.reingest_source(source_id)
    if not res.success:
        raise HTTPException(status_code=400, detail=f"Re-ingestion failed: {res.message}")
    return res


@router.get("/source/{source_id}/history")
def get_source_history(
    source_id: str,
    current_user: User = Depends(get_current_user)
):
    """Retrieve retrieval metadata and revision history for an evidence source."""
    entry = registry_manager.get_entry(source_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Evidence source '{source_id}' not found.")
    return {
        "source_id": entry.source_id,
        "mpn": entry.mpn,
        "brand": entry.brand,
        "manufacturer": entry.manufacturer,
        "url": entry.url,
        "status": entry.source_status,
        "superseded_by": entry.superseded_by,
        "file_hash": entry.file_hash,
        "chunks_count": entry.chunks_count,
        "retrieved_at": entry.retrieved_at,
        "retrieval_metadata": entry.retrieval_metadata,
        "error_message": entry.error_message,
    }



@router.get("/query", response_model=EvidenceQueryResponse)
def query_evidence(
    mpn: Optional[str] = Query(None, description="Target Manufacturer Part Number"),
    keyword: Optional[str] = Query(None, description="Search keyword across text and specifications"),
    current_user: User = Depends(get_current_user)) -> EvidenceQueryResponse:
    """Search discrete official evidence chunks and extracted candidates."""
    if keyword:
        chunks = search_engine.search_by_keyword(keyword, mpn=mpn)
    elif mpn:
        chunks = search_engine.search_by_mpn(mpn)
    else:
        chunks = registry_manager.get_all_active_chunks()

    candidates = []
    if mpn:
        candidates = extractor.extract_candidates_for_mpn(mpn)

    return EvidenceQueryResponse(
        mpn=mpn or "ALL",
        total_chunks=len(chunks),
        chunks=chunks,
        candidates=candidates
    )


@router.get("/candidates/{mpn:path}", response_model=List[ExtractedCandidate])
def get_extracted_candidates(
    mpn: str,
    current_user: User = Depends(get_current_user)
):
    """Retrieve extracted candidate attributes and source citations for a specific MPN."""
    candidates = extractor.extract_candidates_for_mpn(mpn)
    return candidates


@router.api_route("/enrich/{mpn:path}", methods=["GET", "POST"])
def enrich_from_evidence(
    mpn: str,
    current_user: User = Depends(get_current_user)
):
    """
    Perform 6-step official manufacturer evidence enrichment lifecycle for an MPN.
    Validates candidates against category LOVs, normalizes UOM, records evidence lineage,
    and returns verified-only product descriptions.
    """
    from ...evidence.enrichment_service import EvidenceEnrichmentService
    service = EvidenceEnrichmentService(registry_manager)
    res = service.enrich_product_attributes(mpn)
    if res.get("status") == "NO_EVIDENCE_FOUND":
        raise HTTPException(status_code=404, detail=res.get("message"))
    return res


# ============================================================================
# BATCH EVIDENCE-ENRICHMENT JOB & CACHE MANAGEMENT ENDPOINTS
# ============================================================================

from pydantic import BaseModel, Field
from ...evidence.batch_orchestrator import (
    default_batch_manager,
    BatchReport,
    BatchEnrichmentJobManager,
)
from ...evidence.cache import default_extraction_cache


class BatchStartRequest(BaseModel):
    """Payload to trigger a batch evidence enrichment run."""
    mpns: Optional[List[str]] = Field(None, description="Optional list of specific MPNs to enrich. If omitted, enqueues all active registered sources.")
    max_concurrency: int = Field(3, ge=1, le=10, description="Maximum concurrent async enrichment workers")
    force_refresh: bool = Field(False, description="If true, bypasses persistent cache and forces re-extraction")


@router.post("/batch/start", response_model=BatchReport)
async def start_batch_enrichment(
    req: BatchStartRequest = BatchStartRequest(),
    current_user: User = Depends(require_roles(["admin", "specialist", "reviewer"]))
):
    """
    Start a background batch evidence-enrichment job for registered manufacturer sources.
    Uses bounded concurrency and persistent 5-factor caching.
    """
    report = await default_batch_manager.start_batch_job(
        mpns=req.mpns,
        max_concurrency=req.max_concurrency,
        force_refresh=req.force_refresh,
    )
    return report


@router.get("/batch/latest", response_model=Optional[BatchReport])
def get_latest_batch_job(current_user: User = Depends(get_current_user)):
    """Retrieve the most recent batch enrichment report and progress status."""
    report = default_batch_manager.get_latest_report()
    return report


@router.get("/batch/status/{job_id}", response_model=BatchReport)
def get_batch_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Retrieve real-time per-product states and aggregate metrics for a specific batch job."""
    report = default_batch_manager.get_job(job_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Batch job '{job_id}' not found.")
    return report


@router.post("/batch/cancel/{job_id}")
def cancel_batch_job(
    job_id: str,
    current_user: User = Depends(require_roles(["admin", "specialist"]))
):
    """Cancel an active batch enrichment job."""
    success = default_batch_manager.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Batch job '{job_id}' not found.")
    return {"message": f"Job {job_id} cancelled successfully", "job_id": job_id}


@router.get("/cache/stats")
def get_cache_statistics(current_user: User = Depends(get_current_user)):
    """Retrieve persistent Gemini extraction cache statistics, hit rates, and estimated cost savings."""
    return default_extraction_cache.get_stats()


@router.post("/cache/clear")
def clear_extraction_cache(
    current_user: User = Depends(require_roles(["admin", "specialist"]))
):
    """Clear all persistent extraction cache entries."""
    default_extraction_cache.clear()
    return {"message": "Persistent extraction cache wiped successfully", "stats": default_extraction_cache.get_stats()}
