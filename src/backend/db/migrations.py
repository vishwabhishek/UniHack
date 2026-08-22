"""
Database Schema Initialization & Non-Destructive Migration Engine.
"""

from __future__ import annotations

import logging
from typing import List
from .connection import get_db_connection

logger = logging.getLogger("unilog.db.migrations")


SCHEMA_STATEMENTS: List[str] = [
    # 1. Users Table
    """
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('viewer', 'specialist', 'reviewer', 'admin')),
        avatar_color TEXT DEFAULT 'from-cyan-500 to-blue-600',
        token_version INTEGER DEFAULT 1,
        is_active INTEGER DEFAULT 1,
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",

    # 2. Products Table
    """
    CREATE TABLE IF NOT EXISTS products (
        id TEXT PRIMARY KEY,
        mfg_part_num TEXT UNIQUE NOT NULL,
        canonical_mpn TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('raw', 'enriched', 'review_required', 'validated', 'rejected', 'exported')),
        brand TEXT,
        manufacturer TEXT,
        classpath TEXT,
        unspsc TEXT,
        invoice_desc TEXT,
        mobile_desc TEXT,
        short_desc TEXT,
        long_desc TEXT,
        marketing_desc TEXT,
        confidence REAL DEFAULT 0.0,
        data_conflicts_json TEXT DEFAULT '[]',
        review_required INTEGER DEFAULT 0,
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_products_mpn ON products(mfg_part_num);",
    "CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);",
    "CREATE INDEX IF NOT EXISTS idx_products_confidence ON products(confidence);",

    # 3. Raw Supplier Inputs Table
    """
    CREATE TABLE IF NOT EXISTS raw_supplier_inputs (
        product_id TEXT PRIMARY KEY REFERENCES products(id) ON DELETE CASCADE,
        row_id INTEGER NOT NULL,
        raw_mfg_part_num TEXT NOT NULL,
        raw_part_desc TEXT NOT NULL,
        e1_brand TEXT,
        unilog_brand TEXT,
        dib_brand TEXT,
        part_manuf TEXT,
        created_at REAL NOT NULL
    );
    """,

    # 4. Enriched Fields Table
    """
    CREATE TABLE IF NOT EXISTS enriched_fields (
        id TEXT PRIMARY KEY,
        product_id TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
        field_name TEXT NOT NULL,
        candidate_value TEXT,
        normalized_value TEXT,
        status TEXT NOT NULL CHECK(status IN ('raw', 'candidate', 'verified', 'rejected', 'missing_evidence', 'unknown')),
        confidence REAL DEFAULT 0.0,
        dictionary_path TEXT,
        is_approved INTEGER DEFAULT 0,
        updated_by TEXT,
        updated_at REAL NOT NULL,
        UNIQUE(product_id, field_name)
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_enriched_fields_prod ON enriched_fields(product_id);",
    "CREATE INDEX IF NOT EXISTS idx_enriched_fields_status ON enriched_fields(status);",

    # 5. Field Evidence Records Table
    """
    CREATE TABLE IF NOT EXISTS field_evidence (
        id TEXT PRIMARY KEY,
        enriched_field_id TEXT NOT NULL REFERENCES enriched_fields(id) ON DELETE CASCADE,
        product_id TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
        source_id TEXT,
        chunk_id TEXT,
        evidence_excerpt TEXT NOT NULL,
        page_or_section TEXT,
        confidence REAL DEFAULT 0.0,
        start_char INTEGER,
        end_char INTEGER,
        created_at REAL NOT NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_field_ev_field ON field_evidence(enriched_field_id);",
    "CREATE INDEX IF NOT EXISTS idx_field_ev_prod ON field_evidence(product_id);",

    # 6. Source Registry Table
    """
    CREATE TABLE IF NOT EXISTS source_registry (
        source_id TEXT PRIMARY KEY,
        mpn TEXT NOT NULL,
        brand TEXT NOT NULL,
        manufacturer TEXT NOT NULL,
        source_type TEXT NOT NULL,
        url TEXT,
        file_path TEXT,
        file_hash TEXT NOT NULL,
        title TEXT,
        chunks_count INTEGER DEFAULT 0,
        status TEXT NOT NULL CHECK(status IN ('active', 'unavailable', 'rejected_untrusted', 'stale', 'superseded')),
        retrieved_at TEXT NOT NULL,
        parser_version TEXT DEFAULT 'v1.0.0',
        created_at REAL NOT NULL,
        updated_at REAL NOT NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_source_reg_mpn ON source_registry(mpn);",
    "CREATE INDEX IF NOT EXISTS idx_source_reg_hash ON source_registry(file_hash);",

    # 7. Review Actions Table
    """
    CREATE TABLE IF NOT EXISTS review_actions (
        id TEXT PRIMARY KEY,
        product_id TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
        field_name TEXT NOT NULL,
        action_type TEXT NOT NULL CHECK(action_type IN ('approve', 'edit', 'reject', 'mark_unknown')),
        old_value TEXT,
        new_value TEXT,
        user_id TEXT,
        user_email TEXT NOT NULL,
        reason TEXT,
        request_id TEXT,
        created_at REAL NOT NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_review_actions_prod ON review_actions(product_id);",
    "CREATE INDEX IF NOT EXISTS idx_review_actions_user ON review_actions(user_email);",

    # 8. Immutable Audit Logs Table
    """
    CREATE TABLE IF NOT EXISTS audit_logs (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        user_email TEXT NOT NULL,
        role TEXT NOT NULL,
        action TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        before_state_json TEXT,
        after_state_json TEXT,
        reason TEXT,
        request_id TEXT,
        ip_address TEXT,
        created_at REAL NOT NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);",
    "CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_email);",
    "CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);",

    # 9. Enrichment Jobs Table
    """
    CREATE TABLE IF NOT EXISTS enrichment_jobs (
        job_id TEXT PRIMARY KEY,
        idempotency_key TEXT UNIQUE,
        status TEXT NOT NULL CHECK(status IN ('queued', 'running', 'waiting_for_evidence', 'validating', 'review_required', 'completed', 'failed', 'cancelled')),
        total_products INTEGER DEFAULT 0,
        processed_products INTEGER DEFAULT 0,
        completed_products INTEGER DEFAULT 0,
        review_required_products INTEGER DEFAULT 0,
        failed_products INTEGER DEFAULT 0,
        cache_hits INTEGER DEFAULT 0,
        token_usage_json TEXT DEFAULT '{}',
        error_message TEXT,
        started_at REAL NOT NULL,
        completed_at REAL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_jobs_status ON enrichment_jobs(status);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_idempotency ON enrichment_jobs(idempotency_key);",

    # 10. Job Events Table
    """
    CREATE TABLE IF NOT EXISTS job_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL REFERENCES enrichment_jobs(job_id) ON DELETE CASCADE,
        mpn TEXT NOT NULL,
        stage TEXT NOT NULL,
        stage_message TEXT,
        is_cached INTEGER DEFAULT 0,
        duration_ms REAL DEFAULT 0.0,
        error_message TEXT,
        created_at REAL NOT NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_job_events_job ON job_events(job_id);",

    # 11. Benchmark Runs Table
    """
    CREATE TABLE IF NOT EXISTS benchmark_runs (
        run_id TEXT PRIMARY KEY,
        total_products INTEGER NOT NULL,
        passed_count INTEGER NOT NULL,
        failed_count INTEGER NOT NULL,
        exact_match_rate REAL NOT NULL,
        lov_adherence_rate REAL NOT NULL,
        summary_metrics_json TEXT NOT NULL,
        executed_by TEXT,
        created_at REAL NOT NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_benchmarks_created ON benchmark_runs(created_at);",

    # 12. Export History Table
    """
    CREATE TABLE IF NOT EXISTS export_history (
        export_id TEXT PRIMARY KEY,
        user_id TEXT,
        user_email TEXT NOT NULL,
        filters_json TEXT DEFAULT '{}',
        schema_version TEXT NOT NULL,
        product_count INTEGER NOT NULL,
        checksum_sha256 TEXT NOT NULL,
        file_path TEXT,
        created_at REAL NOT NULL
    );
    """,
    "CREATE INDEX IF NOT EXISTS idx_export_history_created ON export_history(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_job_events_mpn ON job_events(mpn);",
    "CREATE INDEX IF NOT EXISTS idx_source_reg_status ON source_registry(status);"
]


class DatabaseMigrationManager:
    """Runs database schema setup and migrations."""

    @staticmethod
    def run_migrations() -> None:
        """Execute all DDL schema statements safely in order with non-destructive column additions."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for stmt in SCHEMA_STATEMENTS:
                cursor.execute(stmt)

            # Non-destructive migrations for existing SQLite databases
            cursor.execute("PRAGMA table_info(source_registry);")
            source_cols = {row["name"] for row in cursor.fetchall()}
            if "superseded_by" not in source_cols:
                cursor.execute("ALTER TABLE source_registry ADD COLUMN superseded_by TEXT;")
            if "retrieval_metadata_json" not in source_cols:
                cursor.execute("ALTER TABLE source_registry ADD COLUMN retrieval_metadata_json TEXT DEFAULT '{}';")

            cursor.execute("PRAGMA table_info(enrichment_jobs);")
            job_cols = {row["name"] for row in cursor.fetchall()}
            if "force_refresh" not in job_cols:
                cursor.execute("ALTER TABLE enrichment_jobs ADD COLUMN force_refresh INTEGER DEFAULT 0;")

            conn.commit()
            logger.info("Database migrations executed successfully.")


def run_migrations() -> None:
    DatabaseMigrationManager.run_migrations()

