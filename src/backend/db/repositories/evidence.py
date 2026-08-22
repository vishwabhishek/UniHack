"""
Source Registry and Field Evidence Repository.
"""

from __future__ import annotations

import time
import uuid
from typing import Dict, List, Optional, Any
from ..connection import get_db_connection


class EvidenceRepository:
    """Repository managing official manufacturer source documents and discrete chunk evidence."""

    def upsert_source_registry_entry(
        self,
        source_id: str,
        mpn: str,
        brand: str,
        manufacturer: str,
        source_type: str,
        file_hash: str,
        url: Optional[str] = None,
        file_path: Optional[str] = None,
        title: Optional[str] = None,
        chunks_count: int = 0,
        status: str = "active",
        retrieved_at: Optional[str] = None,
        parser_version: str = "v1.0.0",
    ) -> None:
        now = time.time()
        retrieved = retrieved_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO source_registry (
                    source_id, mpn, brand, manufacturer, source_type,
                    url, file_path, file_hash, title, chunks_count, status,
                    retrieved_at, parser_version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    mpn = excluded.mpn,
                    brand = excluded.brand,
                    manufacturer = excluded.manufacturer,
                    source_type = excluded.source_type,
                    url = excluded.url,
                    file_path = excluded.file_path,
                    file_hash = excluded.file_hash,
                    title = excluded.title,
                    chunks_count = excluded.chunks_count,
                    status = excluded.status,
                    retrieved_at = excluded.retrieved_at,
                    parser_version = excluded.parser_version,
                    updated_at = excluded.updated_at;
                """,
                (
                    source_id, mpn.strip().upper(), brand, manufacturer, source_type,
                    url, file_path, file_hash, title, chunks_count, status,
                    retrieved, parser_version, now, now
                ),
            )
            conn.commit()

    def get_source_by_mpn(self, mpn: str) -> List[Dict[str, Any]]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM source_registry WHERE upper(mpn) = upper(?);", (mpn.strip(),))
            return [dict(r) for r in cursor.fetchall()]

    def get_source_by_id(self, source_id: str) -> Optional[Dict[str, Any]]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM source_registry WHERE source_id = ?;", (source_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_source_status(
        self,
        source_id: str,
        status: str,
        superseded_by: Optional[str] = None,
    ) -> bool:
        now = time.time()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE source_registry
                SET status = ?, superseded_by = COALESCE(?, superseded_by), updated_at = ?
                WHERE source_id = ?;
                """,
                (status, superseded_by, now, source_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def list_sources(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute("SELECT * FROM source_registry WHERE status = ? ORDER BY created_at DESC;", (status,))
            else:
                cursor.execute("SELECT * FROM source_registry ORDER BY created_at DESC;")
            return [dict(r) for r in cursor.fetchall()]

    def add_field_evidence(
        self,
        enriched_field_id: str,
        product_id: str,
        evidence_excerpt: str,
        source_id: Optional[str] = None,
        chunk_id: Optional[str] = None,
        page_or_section: Optional[str] = None,
        confidence: float = 0.0,
        start_char: Optional[int] = None,
        end_char: Optional[int] = None,
    ) -> str:
        now = time.time()
        ev_id = f"fev_{uuid.uuid4().hex[:12]}"
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO field_evidence (
                    id, enriched_field_id, product_id, source_id, chunk_id,
                    evidence_excerpt, page_or_section, confidence, start_char, end_char, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    ev_id, enriched_field_id, product_id, source_id, chunk_id,
                    evidence_excerpt, page_or_section, confidence, start_char, end_char, now
                ),
            )
            conn.commit()
            return ev_id

    def get_field_evidence(self, product_id: str) -> List[Dict[str, Any]]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT fe.*, ef.field_name, ef.candidate_value, ef.normalized_value, ef.status as field_status
                FROM field_evidence fe
                JOIN enriched_fields ef ON fe.enriched_field_id = ef.id
                WHERE fe.product_id = ?
                ORDER BY fe.created_at ASC;
                """,
                (product_id,),
            )
            return [dict(r) for r in cursor.fetchall()]


evidence_repo = EvidenceRepository()

