"""
Enrichment Jobs & Lifecycle Events Repository.
"""

from __future__ import annotations

import json
import time
from typing import Dict, List, Optional, Any
from ..connection import get_db_connection


class JobRepository:
    """Repository managing asynchronous enrichment jobs, state machine, and granular event logs."""

    def create_job(
        self,
        job_id: str,
        total_products: int,
        idempotency_key: Optional[str] = None,
        status: str = "queued",
    ) -> Dict[str, Any]:
        now = time.time()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO enrichment_jobs (
                    job_id, idempotency_key, status, total_products,
                    processed_products, completed_products, review_required_products,
                    failed_products, cache_hits, token_usage_json, started_at
                ) VALUES (?, ?, ?, ?, 0, 0, 0, 0, 0, '{}', ?);
                """,
                (job_id, idempotency_key, status, total_products, now),
            )
            conn.commit()
        return self.get_job_by_id(job_id)

    def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM enrichment_jobs WHERE job_id = ?;", (job_id,))
            row = cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d["token_usage"] = json.loads(d["token_usage_json"] or "{}")
            return d

    def get_job_by_idempotency_key(self, key: str) -> Optional[Dict[str, Any]]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM enrichment_jobs WHERE idempotency_key = ?;", (key.strip(),))
            row = cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d["token_usage"] = json.loads(d["token_usage_json"] or "{}")
            return d

    def update_job_progress(
        self,
        job_id: str,
        status: str,
        processed_products: int,
        completed_products: int,
        review_required_products: int,
        failed_products: int,
        cache_hits: int,
        token_usage: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        completed_at: Optional[float] = None,
    ) -> None:
        token_json = json.dumps(token_usage or {})
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE enrichment_jobs SET
                    status = ?,
                    processed_products = ?,
                    completed_products = ?,
                    review_required_products = ?,
                    failed_products = ?,
                    cache_hits = ?,
                    token_usage_json = ?,
                    error_message = ?,
                    completed_at = ?
                WHERE job_id = ?;
                """,
                (
                    status, processed_products, completed_products,
                    review_required_products, failed_products, cache_hits,
                    token_json, error_message, completed_at, job_id
                ),
            )
            conn.commit()

    def add_job_event(
        self,
        job_id: str,
        mpn: str,
        stage: str,
        stage_message: Optional[str] = None,
        is_cached: bool = False,
        duration_ms: float = 0.0,
        error_message: Optional[str] = None,
    ) -> None:
        now = time.time()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO job_events (
                    job_id, mpn, stage, stage_message, is_cached, duration_ms, error_message, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (job_id, mpn, stage, stage_message, 1 if is_cached else 0, duration_ms, error_message, now),
            )
            conn.commit()

    def list_job_events(self, job_id: str) -> List[Dict[str, Any]]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM job_events WHERE job_id = ? ORDER BY id ASC;",
                (job_id,),
            )
            return [dict(r) for r in cursor.fetchall()]

    def list_jobs(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM enrichment_jobs ORDER BY started_at DESC LIMIT ? OFFSET ?;",
                (limit, offset),
            )
            rows = cursor.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["token_usage"] = json.loads(d["token_usage_json"] or "{}")
                results.append(d)
            return results

    def recover_dangling_jobs(self) -> int:
        """Mark interrupted jobs as failed on system boot."""
        now = time.time()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE enrichment_jobs
                SET status = 'failed',
                    error_message = 'Job interrupted by server restart',
                    completed_at = ?
                WHERE status IN ('queued', 'running', 'validating', 'waiting_for_evidence');
                """,
                (now,),
            )
            count = cursor.rowcount
            conn.commit()
            return count


job_repo = JobRepository()
