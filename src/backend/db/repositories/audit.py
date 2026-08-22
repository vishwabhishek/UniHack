"""
Immutable Audit Trail Repository.
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Dict, List, Optional, Any
from ..connection import get_db_connection


class AuditRepository:
    """Repository recording append-only, tamper-evident audit logs."""

    def record_action(
        self,
        user_email: str,
        role: str,
        action: str,
        entity_type: str,
        entity_id: str,
        user_id: Optional[str] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record an immutable audit entry."""
        now = time.time()
        audit_id = f"aud_{uuid.uuid4().hex[:12]}"
        before_json = json.dumps(before_state) if before_state else None
        after_json = json.dumps(after_state) if after_state else None

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO audit_logs (
                    id, user_id, user_email, role, action, entity_type, entity_id,
                    before_state_json, after_state_json, reason, request_id, ip_address, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    audit_id, user_id, user_email, role, action, entity_type, entity_id,
                    before_json, after_json, reason, request_id, ip_address, now
                ),
            )
            conn.commit()

        return {
            "id": audit_id,
            "user_email": user_email,
            "role": role,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "reason": reason,
            "request_id": request_id,
            "created_at": now,
        }

    def list_logs(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        user_email: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Query audit logs with optional filters."""
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params: List[Any] = []

        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)
        if entity_id:
            query += " AND entity_id = ?"
            params.append(entity_id)
        if user_email:
            query += " AND user_email = ?"
            params.append(user_email)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["before_state"] = json.loads(d["before_state_json"]) if d.get("before_state_json") else None
                d["after_state"] = json.loads(d["after_state_json"]) if d.get("after_state_json") else None
                results.append(d)
            return results

    def get_product_activity_timeline(self, product_id: str, mpn: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Aggregate a comprehensive chronological activity timeline for a product across:
        - Audit logs (promotions, edits, exports)
        - Review actions (field approvals, manual overrides)
        - Job events (retrieval, extraction, validation transitions)
        - Field evidence registrations
        """
        timeline: List[Dict[str, Any]] = []

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 1. Audit logs
            cursor.execute(
                """
                SELECT * FROM audit_logs
                WHERE entity_id LIKE ? OR entity_id LIKE ? OR (entity_type = 'product' AND entity_id = ?)
                ORDER BY created_at ASC;
                """,
                (f"{product_id}:%", f"{product_id}", product_id),
            )
            for r in cursor.fetchall():
                after_st = json.loads(r["after_state_json"]) if r["after_state_json"] else {}
                before_st = json.loads(r["before_state_json"]) if r["before_state_json"] else {}
                timeline.append({
                    "id": r["id"],
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(r["created_at"])),
                    "epoch_ts": r["created_at"],
                    "actor": r["user_email"],
                    "role": r["role"],
                    "event_type": "AUDIT_LOG",
                    "action": r["action"],
                    "field_name": r["entity_id"].split(":")[-1] if ":" in r["entity_id"] else None,
                    "old_value": before_st.get("value"),
                    "new_value": after_st.get("value"),
                    "reason": r["reason"],
                    "request_id": r["request_id"],
                })

            # 2. Review actions
            cursor.execute(
                """
                SELECT * FROM review_actions WHERE product_id = ? ORDER BY created_at ASC;
                """,
                (product_id,),
            )
            for r in cursor.fetchall():
                timeline.append({
                    "id": r["id"],
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(r["created_at"])),
                    "epoch_ts": r["created_at"],
                    "actor": r["user_email"],
                    "role": "reviewer",
                    "event_type": "REVIEW_ACTION",
                    "action": f"FIELD_{r['action_type'].upper()}",
                    "field_name": r["field_name"],
                    "old_value": r["old_value"],
                    "new_value": r["new_value"],
                    "reason": r["reason"],
                    "request_id": r["request_id"],
                })

            # 3. Job events (if MPN available)
            if mpn:
                cursor.execute(
                    """
                    SELECT * FROM job_events WHERE upper(mpn) = upper(?) ORDER BY created_at ASC;
                    """,
                    (mpn.strip(),),
                )
                for r in cursor.fetchall():
                    timeline.append({
                        "id": f"je_{r['id']}",
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(r["created_at"])),
                        "epoch_ts": r["created_at"],
                        "actor": "batch_job_runner",
                        "role": "pipeline",
                        "event_type": "JOB_EVENT",
                        "action": f"STAGE_{r['stage'].upper()}",
                        "field_name": None,
                        "old_value": None,
                        "new_value": r["stage_message"],
                        "reason": r["error_message"] or f"Duration: {r['duration_ms']:.1f}ms (Cached: {bool(r['is_cached'])})",
                        "request_id": r["job_id"],
                    })

            # 4. Field evidence records
            cursor.execute(
                """
                SELECT fe.*, ef.field_name, sr.url as source_url, sr.title as source_title
                FROM field_evidence fe
                JOIN enriched_fields ef ON fe.enriched_field_id = ef.id
                LEFT JOIN source_registry sr ON fe.source_id = sr.source_id
                WHERE fe.product_id = ?
                ORDER BY fe.created_at ASC;
                """,
                (product_id,),
            )
            for r in cursor.fetchall():
                timeline.append({
                    "id": r["id"],
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(r["created_at"])),
                    "epoch_ts": r["created_at"],
                    "actor": "evidence_extractor",
                    "role": "system",
                    "event_type": "EVIDENCE_INGESTED",
                    "action": "EVIDENCE_CITED",
                    "field_name": r["field_name"],
                    "old_value": None,
                    "new_value": r["evidence_excerpt"],
                    "reason": f"Page/Section: {r['page_or_section'] or 'General'} (Confidence: {r['confidence']:.2f})",
                    "source_url": r["source_url"],
                    "request_id": r["source_id"],
                })

        # Deduplicate & Sort by timestamp descending
        seen_keys = set()
        deduped = []
        for item in sorted(timeline, key=lambda x: x["epoch_ts"], reverse=True):
            key = (item["action"], item["field_name"], item["timestamp"], item["new_value"])
            if key not in seen_keys:
                seen_keys.add(key)
                deduped.append(item)

        return deduped


audit_repo = AuditRepository()

