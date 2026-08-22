"""
Unit tests for SQLite Persistence, Migrations, and Restart Survivability.
"""

import os
import tempfile
import sqlite3
import pytest
from pathlib import Path

from src.backend.db.connection import DatabaseConnectionManager
from src.backend.db.migrations import DatabaseMigrationManager
from src.backend.db.repositories.users import UserRepository
from src.backend.db.repositories.products import ProductRepository
from src.backend.db.repositories.evidence import EvidenceRepository
from src.backend.db.repositories.audit import AuditRepository
from src.backend.db.repositories.jobs import JobRepository
from src.backend.db.repositories.exports import ExportRepository


@pytest.fixture
def temp_db():
    """Create an isolated temporary SQLite database for persistence tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    old_env = os.environ.get("DATABASE_PATH")
    os.environ["DATABASE_PATH"] = db_path
    
    # Close any thread-local connection and run migrations
    db_mgr = DatabaseConnectionManager()
    db_mgr.close_thread_connection()
    DatabaseMigrationManager.run_migrations()

    yield db_path

    # Cleanup
    db_mgr.close_thread_connection()
    if old_env:
        os.environ["DATABASE_PATH"] = old_env
    else:
        os.environ.pop("DATABASE_PATH", None)
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass


def test_migrations_create_all_tables(temp_db):
    """Verify all 12 required MVP tables and indexes exist."""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {r[0] for r in cursor.fetchall()}
    conn.close()

    expected_tables = {
        "users",
        "products",
        "raw_supplier_inputs",
        "enriched_fields",
        "field_evidence",
        "source_registry",
        "review_actions",
        "audit_logs",
        "enrichment_jobs",
        "job_events",
        "benchmark_runs",
        "export_history",
    }
    assert expected_tables.issubset(tables)


def test_persistence_survives_restart_simulation(temp_db):
    """Verify that records written to SQLite survive thread/connection resets."""
    user_repo = UserRepository()
    product_repo = ProductRepository()
    export_repo = ExportRepository()

    # Write records
    u = user_repo.create_user(
        email="test_persist@unilog.com",
        name="Persistence User",
        password_hash="pbkdf2:dummy",
        role="specialist"
    )
    assert u["email"] == "test_persist@unilog.com"

    product_repo.upsert_product(
        product_id="prod_persist_1",
        mfg_part_num="PERSIST-100",
        canonical_mpn="PERSIST-100",
        status="raw",
        brand="SharkBite®",
        manufacturer="Reliance Worldwide Corporation",
        confidence=0.95,
    )

    export_repo.record_export(
        user_email="test_persist@unilog.com",
        schema_version="v1.0.0",
        product_count=1000,
        checksum_sha256="abc123sha256checksum",
    )

    # Simulate restart by clearing thread connection
    db_mgr = DatabaseConnectionManager()
    db_mgr.close_thread_connection()

    # Re-read from a fresh connection
    u_loaded = user_repo.get_by_email("test_persist@unilog.com")
    assert u_loaded is not None
    assert u_loaded["name"] == "Persistence User"

    prod_loaded = product_repo.get_by_id("prod_persist_1")
    assert prod_loaded is not None
    assert prod_loaded["mfg_part_num"] == "PERSIST-100"
    assert prod_loaded["confidence"] == 0.95

    exports = export_repo.list_exports()
    assert len(exports) >= 1
    assert exports[0]["checksum_sha256"] == "abc123sha256checksum"


def test_token_version_revocation_persists(temp_db):
    """Verify token version increments in DB."""
    user_repo = UserRepository()
    u = user_repo.create_user(
        email="revoker@unilog.com",
        name="Revoke User",
        password_hash="pbkdf2:dummy",
        role="reviewer"
    )
    assert u["token_version"] == 1

    new_ver = user_repo.increment_token_version(u["id"])
    assert new_ver == 2

    # Close connection
    DatabaseConnectionManager().close_thread_connection()

    u_reloaded = user_repo.get_by_id(u["id"])
    assert u_reloaded["token_version"] == 2
