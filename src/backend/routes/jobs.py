"""
Asynchronous Persistent Jobs API Routes.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from ..auth import require_specialist, require_viewer, User
from ..db.repositories.jobs import job_repo
from ..jobs.runner import job_runner

router = APIRouter(prefix="/api/jobs", tags=["Enrichment Jobs"])


class EnrichmentJobRequest(BaseModel):
    idempotency_key: Optional[str] = Field(None, description="Client-provided idempotency key")
    max_concurrency: int = Field(3, ge=1, le=10, description="Bounded concurrent workers")
    force_refresh: bool = Field(False, description="Bypass deterministic extraction cache")


@router.post("/enrichment", summary="Submit Asynchronous Batch Enrichment Job")
async def submit_enrichment_job(
    req: EnrichmentJobRequest,
    current_user: User = Depends(require_specialist),
):
    """
    Launch or deduplicate a background batch evidence enrichment job.
    Requires specialist, reviewer, or admin role.
    """
    job = await job_runner.submit_enrichment_job(
        idempotency_key=req.idempotency_key,
        max_concurrency=req.max_concurrency,
        force_refresh=req.force_refresh,
        user_email=current_user.email,
    )
    return job


@router.get("/{job_id}", summary="Get Job Details & Real-Time Progress")
def get_job(
    job_id: str,
    current_user: User = Depends(require_viewer),
):
    """Retrieve current state and progress counts for a persistent job."""
    job = job_repo.get_job_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enrichment job '{job_id}' not found.",
        )
    return job


@router.get("/{job_id}/events", summary="Get Granular Job Lifecycle Events")
def get_job_events(
    job_id: str,
    current_user: User = Depends(require_viewer),
):
    """Retrieve chronological per-product lifecycle transitions for a job."""
    job = job_repo.get_job_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enrichment job '{job_id}' not found.",
        )
    events = job_repo.list_job_events(job_id)
    return {"job_id": job_id, "events_count": len(events), "events": events}


@router.post("/{job_id}/cancel", summary="Cancel Running Job")
def cancel_job(
    job_id: str,
    current_user: User = Depends(require_specialist),
):
    """Request graceful cancellation of a running background enrichment job."""
    job = job_repo.get_job_by_id(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enrichment job '{job_id}' not found.",
        )
    cancelled = job_runner.cancel_job(job_id)
    return {
        "job_id": job_id,
        "cancelled": cancelled,
        "message": "Cancellation request acknowledged." if cancelled else "Job is not currently active in worker.",
    }


@router.get("", summary="List Historical & Active Enrichment Jobs")
def list_jobs(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_viewer),
):
    """List historical batch enrichment jobs with token and cost metadata."""
    jobs = job_repo.list_jobs(limit=limit, offset=offset)
    return {"total": len(jobs), "jobs": jobs}
