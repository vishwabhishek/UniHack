"""
Review Actions and Human-In-The-Loop Curation Repository.
"""

from __future__ import annotations

import time
import uuid
from typing import Dict, List, Optional, Any
from ..connection import get_db_connection


class ReviewRepository:
    """Repository tracking field-level human curate and approval actions."""

    def record_review_action(
        self,
        product_id: str,
        field_name: str,
        action_type: str,
        user_email: str,
        user_id: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = time.time()
        action_id = f"rev_{uuid.uuid4().hex[:12]}"
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO review_actions (
                    id, product_id, field_name, action_type, old_value, new_value,
                    user_id, user_email, reason, request_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    action_id, product_id, field_name, action_type, old_value, new_value,
                    user_id, user_email, reason, request_id, now
                ),
            )
            conn.commit()
        return {
            "id": action_id,
            "product_id": product_id,
            "field_name": field_name,
            "action_type": action_type,
            "old_value": old_value,
            "new_value": new_value,
            "user_email": user_email,
            "reason": reason,
            "created_at": now,
        }

    def list_actions_for_product(self, product_id: str) -> List[Dict[str, Any]]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM review_actions WHERE product_id = ? ORDER BY created_at DESC;",
                (product_id,),
            )
            return [dict(r) for r in cursor.fetchall()]


review_repo = ReviewRepository()
