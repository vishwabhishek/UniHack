"""
Export History and Delivery Audit Repository.
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Dict, List, Optional, Any
from ..connection import get_db_connection


class ExportRepository:
    """Repository tracking all 252-column export generations with cryptographic hashes."""

    def record_export(
        self,
        user_email: str,
        schema_version: str,
        product_count: int,
        checksum_sha256: str,
        user_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        file_path: Optional[str] = None,
        export_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = time.time()
        eid = export_id or f"exp_{uuid.uuid4().hex[:12]}"
        filters_json = json.dumps(filters or {})

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO export_history (
                    export_id, user_id, user_email, filters_json,
                    schema_version, product_count, checksum_sha256, file_path, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    eid, user_id, user_email, filters_json,
                    schema_version, product_count, checksum_sha256, file_path, now
                ),
            )
            conn.commit()

        return {
            "export_id": eid,
            "user_email": user_email,
            "schema_version": schema_version,
            "product_count": product_count,
            "checksum_sha256": checksum_sha256,
            "file_path": file_path,
            "created_at": now,
        }

    def list_exports(self, limit: int = 50) -> List[Dict[str, Any]]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM export_history ORDER BY created_at DESC LIMIT ?;", (limit,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["filters"] = json.loads(d["filters_json"] or "{}")
                results.append(d)
            return results


export_repo = ExportRepository()
