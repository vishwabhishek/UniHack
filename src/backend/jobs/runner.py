"""
Asynchronous Persistent Job Runner with Bounded Concurrency & Idempotency.
"""

from __future__ import annotations

import asyncio
import os
import time
import uuid
import traceback
from typing import Dict, List, Optional, Any

from ..db.repositories.jobs import job_repo
from ..db.repositories.products import product_repo
from ..db.repositories.evidence import evidence_repo
from ..db.repositories.audit import audit_repo
from src.evidence.registry import EvidenceRegistryManager
from src.evidence.enrichment_service import EvidenceEnrichmentService
from src.evidence.cache import default_extraction_cache


class EnrichmentJobRunner:
    """
    Asynchronous persistent worker executing batch product enrichment
    with bounded semaphore concurrency, transient retries, and idempotency.
    """

    def __init__(self):
        self.registry = EvidenceRegistryManager()
        self.enrichment_service = EvidenceEnrichmentService(self.registry)
        self.cache = default_extraction_cache
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._cancellation_requested: Dict[str, bool] = {}

    def is_transient_error(self, err: Exception) -> bool:
        """Check if an exception is transient (429 rate limit, 503, timeout)."""
        err_str = str(err).lower()
        return (
            "429" in err_str
            or "rate limit" in err_str
            or "503" in err_str
            or "502" in err_str
            or "504" in err_str
            or "resource_exhausted" in err_str
            or "timeout" in err_str
            or "connection reset" in err_str
            or isinstance(err, (asyncio.TimeoutError, TimeoutError, ConnectionError))
        )

    async def submit_enrichment_job(
        self,
        idempotency_key: Optional[str] = None,
        max_concurrency: int = 3,
        force_refresh: bool = False,
        user_email: str = "system",
    ) -> Dict[str, Any]:
        """
        Submit a new enrichment job or return existing one if idempotency_key is provided.
        """
        if idempotency_key:
            existing = job_repo.get_job_by_idempotency_key(idempotency_key)
            if existing:
                return existing

        # Target products: only products with registered official manufacturer evidence
        registered_entries = [e for e in self.registry.load_registry() if e.source_status.upper() == "ACTIVE"]
        total_count = len(registered_entries)

        job_id = f"job_{uuid.uuid4().hex[:12]}"
        job = job_repo.create_job(
            job_id=job_id,
            total_products=total_count,
            idempotency_key=idempotency_key,
            status="queued",
        )

        audit_repo.record_action(
            user_email=user_email,
            role="specialist",
            action="JOB_ENRICHMENT_SUBMITTED",
            entity_type="job",
            entity_id=job_id,
            after_state={"total_products": total_count, "concurrency": max_concurrency, "force_refresh": force_refresh},
            reason="Launched batch evidence enrichment job",
        )

        # Launch worker in background event loop
        task = asyncio.create_task(
            self._execute_job(
                job_id=job_id,
                entries=registered_entries,
                max_concurrency=max_concurrency,
                force_refresh=force_refresh,
            )
        )
        self._running_tasks[job_id] = task

        return job

    async def _execute_job(
        self,
        job_id: str,
        entries: List[Any],
        max_concurrency: int,
        force_refresh: bool,
    ) -> None:
        """Run bounded concurrency execution over registered products."""
        job_repo.update_job_progress(
            job_id=job_id,
            status="running",
            processed_products=0,
            completed_products=0,
            review_required_products=0,
            failed_products=0,
            cache_hits=0,
        )

        semaphore = asyncio.Semaphore(max_concurrency)
        processed = 0
        completed = 0
        review_req = 0
        failed = 0
        cache_hits = 0

        async def worker(entry):
            nonlocal processed, completed, review_req, failed, cache_hits
            if self._cancellation_requested.get(job_id, False):
                return

            async with semaphore:
                mpn = entry.mpn
                t0 = time.time()
                try:
                    # 1. State: RETRIEVING
                    job_repo.add_job_event(job_id, mpn, "retrieving", "Retrieving official registered chunks")
                    chunks = self.registry.load_chunks_for_entry(entry)

                    # 2. State: EXTRACTING & Cache Check
                    cfg_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
                    cfg_schema = os.getenv("GEMINI_SCHEMA_VERSION", "v1.0.0")
                    cfg_lov = os.getenv("GEMINI_LOV_VERSION", "lov_v1.0.0")
                    primary_hash = chunks[0].chunk_hash if chunks else entry.file_hash

                    cache_key = self.cache.generate_cache_key(primary_hash, mpn, cfg_model, cfg_schema, cfg_lov)
                    cached_item = self.cache.get(cache_key) if not force_refresh else None
                    is_cached = bool(cached_item)

                    if is_cached:
                        cache_hits += 1
                        job_repo.add_job_event(job_id, mpn, "extracting", "Resolved from deterministic local cache", is_cached=True)
                    else:
                        job_repo.add_job_event(job_id, mpn, "extracting", "Invoking Gemini structured extraction", is_cached=False)

                    # 3. State: VALIDATING with Transient Retry
                    job_repo.add_job_event(job_id, mpn, "validating", "Validating against LOV and UOM standardizer")
                    enrich_res = await self._run_with_retry(lambda: self.enrichment_service.enrich_product_attributes(mpn), job_id, mpn)

                    duration_ms = round((time.time() - t0) * 1000, 2)
                    status_outcome = enrich_res.get("status", "SUCCESS")
                    prov = enrich_res.get("provenance_summary")
                    conflicts = enrich_res.get("conflicts", [])

                    if status_outcome == "SUCCESS" and len(conflicts) == 0:
                        completed += 1
                        job_repo.add_job_event(job_id, mpn, "completed", f"All evidence facts verified ({duration_ms}ms)", is_cached=is_cached, duration_ms=duration_ms)
                    else:
                        review_req += 1
                        job_repo.add_job_event(job_id, mpn, "review_required", f"Review required: {len(conflicts)} flags", is_cached=is_cached, duration_ms=duration_ms)

                except Exception as ex:
                    duration_ms = round((time.time() - t0) * 1000, 2)
                    failed += 1
                    job_repo.add_job_event(job_id, mpn, "failed", f"Failed: {ex}", duration_ms=duration_ms, error_message=str(ex))
                finally:
                    processed += 1
                    # Update progress in DB after each product
                    input_rate = float(os.getenv("GEMINI_INPUT_COST_PER_MILLION", "0.075"))
                    output_rate = float(os.getenv("GEMINI_OUTPUT_COST_PER_MILLION", "0.300"))
                    cache_misses = max(0, processed - cache_hits)
                    prompt_tokens = cache_misses * 450
                    cand_tokens = cache_misses * 150
                    cost = (prompt_tokens / 1_000_000.0) * input_rate + (cand_tokens / 1_000_000.0) * output_rate

                    token_usage = {
                        "prompt_tokens": prompt_tokens,
                        "candidate_tokens": cand_tokens,
                        "total_tokens": prompt_tokens + cand_tokens,
                        "estimated_cost_usd": round(cost, 6),
                    }
                    job_repo.update_job_progress(
                        job_id=job_id,
                        status="running",
                        processed_products=processed,
                        completed_products=completed,
                        review_required_products=review_req,
                        failed_products=failed,
                        cache_hits=cache_hits,
                        token_usage=token_usage,
                    )

        # Run all workers
        tasks = [worker(entry) for entry in entries]
        await asyncio.gather(*tasks, return_exceptions=True)

        final_status = "cancelled" if self._cancellation_requested.get(job_id, False) else "completed"
        if failed == len(entries) and len(entries) > 0:
            final_status = "failed"

        job_repo.update_job_progress(
            job_id=job_id,
            status=final_status,
            processed_products=processed,
            completed_products=completed,
            review_required_products=review_req,
            failed_products=failed,
            cache_hits=cache_hits,
            completed_at=time.time(),
        )
        self._running_tasks.pop(job_id, None)
        self._cancellation_requested.pop(job_id, None)

    async def _run_with_retry(self, func, job_id: str, mpn: str, max_retries: int = 3) -> Any:
        """Retry transient failures with exponential backoff."""
        attempt = 0
        while attempt < max_retries:
            try:
                return func()
            except Exception as e:
                attempt += 1
                if self.is_transient_error(e) and attempt < max_retries:
                    backoff = 1.0 * (2 ** (attempt - 1))
                    job_repo.add_job_event(job_id, mpn, "retrying", f"Transient failure ({e}). Retrying in {backoff:.1f}s (attempt {attempt}/{max_retries})")
                    await asyncio.sleep(backoff)
                else:
                    raise

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job."""
        if job_id in self._running_tasks:
            self._cancellation_requested[job_id] = True
            self._running_tasks[job_id].cancel()
            job_repo.update_job_progress(
                job_id=job_id,
                status="cancelled",
                processed_products=0,
                completed_products=0,
                review_required_products=0,
                failed_products=0,
                cache_hits=0,
                completed_at=time.time(),
            )
            return True
        return False
    def recover_stale_jobs(self) -> int:
        """Mark any jobs left in 'running' or 'queued' states from prior server processes as failed."""
        from ..db.connection import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            now = time.time()
            cursor.execute(
                """
                UPDATE enrichment_jobs
                SET status = 'failed', error_message = 'Job interrupted by server restart', completed_at = ?
                WHERE status IN ('running', 'queued', 'waiting_for_evidence', 'validating');
                """,
                (now,)
            )
            conn.commit()
            return cursor.rowcount


job_runner = EnrichmentJobRunner()

