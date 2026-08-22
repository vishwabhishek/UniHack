"""
User Repository for SQLite Persistence.
"""

from __future__ import annotations

import time
import uuid
from typing import Dict, List, Optional, Any
from ..connection import get_db_connection


class UserRepository:
    """Repository managing user credentials, roles, and token versioning."""

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE lower(email) = lower(?);", (email.strip(),))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?;", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_user(
        self,
        email: str,
        name: str,
        password_hash: str,
        role: str,
        avatar_color: str = "from-cyan-500 to-blue-600",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        now = time.time()
        uid = user_id or str(uuid.uuid4())
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (id, email, name, password_hash, role, avatar_color, token_version, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, 1, ?, ?);
                """,
                (uid, email.strip().lower(), name.strip(), password_hash, role, avatar_color, now, now),
            )
            conn.commit()
            return self.get_by_id(uid)

    def increment_token_version(self, user_id: str) -> int:
        """Increment token version to revoke all active JWT tokens for user."""
        now = time.time()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET token_version = token_version + 1, updated_at = ? WHERE id = ?;",
                (now, user_id),
            )
            conn.commit()
            cursor.execute("SELECT token_version FROM users WHERE id = ?;", (user_id,))
            row = cursor.fetchone()
            return row["token_version"] if row else 1

    def update_role(self, user_id: str, new_role: str) -> Optional[Dict[str, Any]]:
        """Update a user's RBAC role and increment token version to force session refresh."""
        now = time.time()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET role = ?, token_version = token_version + 1, updated_at = ? WHERE id = ?;",
                (new_role.strip().lower(), now, user_id),
            )
            conn.commit()
            return self.get_by_id(user_id)

    def list_users(self) -> List[Dict[str, Any]]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, email, name, role, avatar_color, token_version, is_active, created_at, updated_at FROM users ORDER BY created_at ASC;")
            return [dict(r) for r in cursor.fetchall()]


user_repo = UserRepository()
