"""
SQLite Database Connection Manager with WAL Mode & Thread Isolation.
"""

from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from ..config import settings


class DatabaseConnectionManager:
    """Thread-safe connection provider for SQLite."""
    _instance: Optional[DatabaseConnectionManager] = None
    _lock = threading.Lock()

    def __new__(cls) -> DatabaseConnectionManager:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseConnectionManager, cls).__new__(cls)
                cls._instance._local = threading.local()
            return cls._instance

    @property
    def db_path(self) -> Path:
        env_path = os.getenv("DATABASE_PATH")
        if env_path:
            return Path(env_path)
        return settings.database_path

    def get_connection(self) -> sqlite3.Connection:
        """Get or create a thread-local SQLite connection with WAL mode."""
        db_file = self.db_path
        db_file.parent.mkdir(parents=True, exist_ok=True)

        if not hasattr(self._local, "connection") or self._local.connection is None:
            conn = sqlite3.connect(
                str(db_file),
                timeout=30.0,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                check_same_thread=False,
            )
            # Enable Foreign Keys & Write-Ahead Logging for high-throughput concurrency
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.row_factory = sqlite3.Row
            self._local.connection = conn

        return self._local.connection

    def close_thread_connection(self) -> None:
        """Close connection for current thread if open."""
        if hasattr(self._local, "connection") and self._local.connection is not None:
            try:
                self._local.connection.close()
            except Exception:
                pass
            self._local.connection = None


db_manager = DatabaseConnectionManager()


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Context manager yielding connection with automatic commit/rollback."""
    conn = db_manager.get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


@contextmanager
def get_db_cursor() -> Generator[sqlite3.Cursor, None, None]:
    """Context manager yielding a cursor inside an active transaction."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()
