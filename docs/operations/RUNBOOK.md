# UniHack Simplifi PIM — Operational Runbook

## 1. Environment Setup & Configuration

### Prerequisites
- Python 3.10+
- SQLite 3.35+
- Node.js 18+ (for frontend)

### Environment Variables
Configure the following in your environment or `.env` file:

```bash
# Server Settings
ENVIRONMENT=development                # 'development' or 'production'
HOST=0.0.0.0
PORT=8000
DEBUG=false
CORS_ORIGINS=http://localhost:5173,http://localhost:8000

# Security & Secrets (Must be changed in production!)
JWT_SECRET=f9c2d1b8e4a7360592c81e7d3a5b6c8f1029384756a1b2c3d4e5f60718293a4b
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
ADMIN_INITIAL_EMAIL=admin@unilog.com
ADMIN_INITIAL_PASSWORD=Admin@123456

# Persistent Storage
DATABASE_PATH=data/unilog_pim.db

# Gemini Evidence Extraction (Optional)
GEMINI_ENABLED=false                  # Set to true when API key is present
GEMINI_API_KEY=                       # Google GenAI API key
GEMINI_MODEL=gemini-2.5-flash
GEMINI_SCHEMA_VERSION=v1.0.0
GEMINI_LOV_VERSION=lov_v1.0.0
```

---

## 2. Starting the Backend Server

```bash
# Activate virtual environment
source .venv/bin/activate

# Run database migrations and start server
python -m src.backend.main
```

FastAPI will start at `http://localhost:8000`. OpenAPI documentation is available at `http://localhost:8000/docs`.

---

## 3. Running Database Migrations

Database migrations execute automatically on server startup. To trigger them manually via Python:

```bash
python -c "from src.backend.db.migrations import run_migrations; run_migrations()"
```

---

## 4. Running Test Suites

```bash
# Run all unit, integration, and security pentest tests
pytest tests/ -v

# Run only security and SSRF tests
pytest tests/adversarial/ tests/unit/test_security_ssrf.py -v

# Run persistence and job runner tests
pytest tests/unit/test_persistence.py tests/integration/test_jobs_api.py -v
```

---

## 5. Maintenance & Disaster Recovery

### Dangling Job Recovery
If the server process is killed or abruptly restarts during an active enrichment job, dangling jobs are automatically marked as `failed` with an explicit recovery message upon next boot.

To manually trigger recovery:
```python
from src.backend.db.repositories.jobs import job_repo
recovered_count = job_repo.recover_dangling_jobs()
print(f"Recovered {recovered_count} interrupted jobs.")
```

### Database Backup & Restore
SQLite uses Write-Ahead Logging (WAL). To safely back up the database while active:

```bash
# Safe live backup using SQLite VACUUM INTO
sqlite3 data/unilog_pim.db "VACUUM INTO 'data/backup_unilog_pim_$(date +%Y%m%d_%H%M%S).db';"
```

To restore from a backup:
1. Stop the application server: `kill <pid>`
2. Replace `data/unilog_pim.db` with the backup file.
3. Remove any lingering `data/unilog_pim.db-wal` or `data/unilog_pim.db-shm` files.
4. Restart the application server.

---

## 6. Secrets Rotation

To rotate the `JWT_SECRET`:
1. Set the new `JWT_SECRET` in environment variables.
2. Restart the server.
3. All existing tokens signed with the previous key will be safely rejected (`401 Unauthorized`), requiring users to re-authenticate with their credentials.
