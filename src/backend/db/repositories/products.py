"""
Product and Raw Supplier Input Repository.
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Dict, List, Optional, Any, Tuple
from ..connection import get_db_connection


class ProductRepository:
    """Repository managing catalog products, raw inputs, enriched fields, and status transitions."""

    def get_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?;", (product_id,))
            row = cursor.fetchone()
            if not row:
                return None
            prod = dict(row)
            prod["data_conflicts"] = json.loads(prod["data_conflicts_json"] or "[]")
            
            # Fetch raw supplier input
            cursor.execute("SELECT * FROM raw_supplier_inputs WHERE product_id = ?;", (product_id,))
            raw = cursor.fetchone()
            prod["raw_input"] = dict(raw) if raw else None

            # Fetch enriched fields
            cursor.execute("SELECT * FROM enriched_fields WHERE product_id = ?;", (product_id,))
            fields = cursor.fetchall()
            prod["enriched_fields"] = [dict(f) for f in fields]

            return prod

    def get_by_mpn(self, mpn: str) -> Optional[Dict[str, Any]]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM products WHERE upper(mfg_part_num) = upper(?);", (mpn.strip(),))
            row = cursor.fetchone()
            return self.get_by_id(row["id"]) if row else None

    def upsert_product(
        self,
        product_id: str,
        mfg_part_num: str,
        canonical_mpn: str,
        status: str,
        brand: Optional[str] = None,
        manufacturer: Optional[str] = None,
        classpath: Optional[str] = None,
        unspsc: Optional[str] = None,
        invoice_desc: Optional[str] = None,
        mobile_desc: Optional[str] = None,
        short_desc: Optional[str] = None,
        long_desc: Optional[str] = None,
        marketing_desc: Optional[str] = None,
        confidence: float = 0.0,
        data_conflicts: Optional[List[str]] = None,
        review_required: bool = False,
    ) -> None:
        now = time.time()
        conflicts_json = json.dumps(data_conflicts or [])
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO products (
                    id, mfg_part_num, canonical_mpn, status, brand, manufacturer,
                    classpath, unspsc, invoice_desc, mobile_desc, short_desc, long_desc,
                    marketing_desc, confidence, data_conflicts_json, review_required, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    mfg_part_num = excluded.mfg_part_num,
                    canonical_mpn = excluded.canonical_mpn,
                    status = excluded.status,
                    brand = excluded.brand,
                    manufacturer = excluded.manufacturer,
                    classpath = excluded.classpath,
                    unspsc = excluded.unspsc,
                    invoice_desc = excluded.invoice_desc,
                    mobile_desc = excluded.mobile_desc,
                    short_desc = excluded.short_desc,
                    long_desc = excluded.long_desc,
                    marketing_desc = excluded.marketing_desc,
                    confidence = excluded.confidence,
                    data_conflicts_json = excluded.data_conflicts_json,
                    review_required = excluded.review_required,
                    updated_at = excluded.updated_at;
                """,
                (
                    product_id, mfg_part_num, canonical_mpn, status, brand, manufacturer,
                    classpath, unspsc, invoice_desc, mobile_desc, short_desc, long_desc,
                    marketing_desc, confidence, conflicts_json, 1 if review_required else 0, now, now
                ),
            )
            conn.commit()

    def upsert_raw_supplier_input(
        self,
        product_id: str,
        row_id: int,
        raw_mfg_part_num: str,
        raw_part_desc: str,
        e1_brand: Optional[str] = None,
        unilog_brand: Optional[str] = None,
        dib_brand: Optional[str] = None,
        part_manuf: Optional[str] = None,
    ) -> None:
        now = time.time()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO raw_supplier_inputs (
                    product_id, row_id, raw_mfg_part_num, raw_part_desc,
                    e1_brand, unilog_brand, dib_brand, part_manuf, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(product_id) DO UPDATE SET
                    row_id = excluded.row_id,
                    raw_mfg_part_num = excluded.raw_mfg_part_num,
                    raw_part_desc = excluded.raw_part_desc,
                    e1_brand = excluded.e1_brand,
                    unilog_brand = excluded.unilog_brand,
                    dib_brand = excluded.dib_brand,
                    part_manuf = excluded.part_manuf;
                """,
                (product_id, row_id, raw_mfg_part_num, raw_part_desc, e1_brand, unilog_brand, dib_brand, part_manuf, now),
            )
            conn.commit()

    def upsert_enriched_field(
        self,
        product_id: str,
        field_name: str,
        candidate_value: Optional[str],
        normalized_value: Optional[str],
        status: str,
        confidence: float = 0.0,
        dictionary_path: Optional[str] = None,
        is_approved: bool = False,
        updated_by: Optional[str] = None,
    ) -> str:
        now = time.time()
        field_id = f"fld_{uuid.uuid4().hex[:12]}"
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO enriched_fields (
                    id, product_id, field_name, candidate_value, normalized_value,
                    status, confidence, dictionary_path, is_approved, updated_by, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(product_id, field_name) DO UPDATE SET
                    candidate_value = excluded.candidate_value,
                    normalized_value = excluded.normalized_value,
                    status = excluded.status,
                    confidence = excluded.confidence,
                    dictionary_path = excluded.dictionary_path,
                    is_approved = excluded.is_approved,
                    updated_by = excluded.updated_by,
                    updated_at = excluded.updated_at;
                """,
                (
                    field_id, product_id, field_name, candidate_value, normalized_value,
                    status, confidence, dictionary_path, 1 if is_approved else 0, updated_by, now
                ),
            )
            conn.commit()
            
            cursor.execute("SELECT id FROM enriched_fields WHERE product_id = ? AND field_name = ?;", (product_id, field_name))
            row = cursor.fetchone()
            return row["id"] if row else field_id

    def list_products(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
        min_confidence: Optional[float] = None,
        max_confidence: Optional[float] = None,
        review_required_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        query = "SELECT * FROM products WHERE 1=1"
        count_query = "SELECT COUNT(*) as total FROM products WHERE 1=1"
        params: List[Any] = []

        if status and status != "ALL":
            query += " AND status = ?"
            count_query += " AND status = ?"
            params.append(status.lower())

        if review_required_only:
            query += " AND review_required = 1"
            count_query += " AND review_required = 1"

        if min_confidence is not None:
            query += " AND confidence >= ?"
            count_query += " AND confidence >= ?"
            params.append(min_confidence)

        if max_confidence is not None:
            query += " AND confidence <= ?"
            count_query += " AND confidence <= ?"
            params.append(max_confidence)

        if search:
            q_like = f"%{search.strip()}%"
            query += " AND (mfg_part_num LIKE ? OR brand LIKE ? OR manufacturer LIKE ? OR invoice_desc LIKE ? OR short_desc LIKE ?)"
            count_query += " AND (mfg_part_num LIKE ? OR brand LIKE ? OR manufacturer LIKE ? OR invoice_desc LIKE ? OR short_desc LIKE ?)"
            params.extend([q_like, q_like, q_like, q_like, q_like])

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(count_query, tuple(params))
            total = cursor.fetchone()["total"]

            query += " ORDER BY created_at ASC LIMIT ? OFFSET ?;"
            page_params = list(params)
            page_params.extend([limit, offset])

            cursor.execute(query, tuple(page_params))
            rows = [dict(r) for r in cursor.fetchall()]
            for r in rows:
                r["data_conflicts"] = json.loads(r["data_conflicts_json"] or "[]")
            return rows, total

    def count_products(self) -> int:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM products;")
            row = cursor.fetchone()
            return row["total"] if row else 0

    def load_all_products_with_fields(self) -> List[Dict[str, Any]]:
        """Load all products along with raw supplier inputs, enriched fields, and review actions."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products ORDER BY rowid ASC;")
            product_rows = [dict(r) for r in cursor.fetchall()]

            if not product_rows:
                return []

            # Fetch all raw inputs
            cursor.execute("SELECT * FROM raw_supplier_inputs;")
            raw_map = {r["product_id"]: dict(r) for r in cursor.fetchall()}

            # Fetch all enriched fields
            cursor.execute("SELECT * FROM enriched_fields ORDER BY rowid ASC;")
            fields_rows = cursor.fetchall()
            fields_map: Dict[str, List[Dict[str, Any]]] = {}
            for f in fields_rows:
                pid = f["product_id"]
                if pid not in fields_map:
                    fields_map[pid] = []
                fields_map[pid].append(dict(f))

            for prod in product_rows:
                pid = prod["id"]
                prod["data_conflicts"] = json.loads(prod["data_conflicts_json"] or "[]")
                prod["raw_input"] = raw_map.get(pid)
                prod["enriched_fields"] = fields_map.get(pid, [])

            return product_rows


product_repo = ProductRepository()

