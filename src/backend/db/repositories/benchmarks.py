"""
Ground-Truth Benchmark Runs Repository.
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Dict, List, Optional, Any
from ..connection import get_db_connection


class BenchmarkRepository:
    """Repository recording ground truth evaluation and quality audits."""

    def record_run(
        self,
        total_products: int,
        passed_count: int,
        failed_count: int,
        exact_match_rate: float,
        lov_adherence_rate: float,
        summary_metrics: Dict[str, Any],
        executed_by: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = time.time()
        rid = run_id or f"bmk_{uuid.uuid4().hex[:12]}"
        metrics_json = json.dumps(summary_metrics)

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO benchmark_runs (
                    run_id, total_products, passed_count, failed_count,
                    exact_match_rate, lov_adherence_rate, summary_metrics_json, executed_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    rid, total_products, passed_count, failed_count,
                    exact_match_rate, lov_adherence_rate, metrics_json, executed_by, now
                ),
            )
            conn.commit()

        return self.get_run_by_id(rid)

    def get_run_by_id(self, run_id: str) -> Optional[Dict[str, Any]]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM benchmark_runs WHERE run_id = ?;", (run_id,))
            row = cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d["summary_metrics"] = json.loads(d["summary_metrics_json"])
            return d

    def get_latest_run(self) -> Optional[Dict[str, Any]]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM benchmark_runs ORDER BY created_at DESC LIMIT 1;")
            row = cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            d["summary_metrics"] = json.loads(d["summary_metrics_json"])
            return d


benchmark_repo = BenchmarkRepository()
