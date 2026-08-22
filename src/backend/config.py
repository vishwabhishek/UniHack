"""Backend configuration and system paths for Industrial Product Intelligence & PIM Enrichment Platform."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel


def _load_dotenv(dotenv_path: Path) -> None:
    """Load environment variables from a .env file into os.environ if present."""
    if not dotenv_path.exists():
        return
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip("'").strip('"')
            # Do not overwrite already set environment variables
            if key not in os.environ:
                os.environ[key] = val


# Load project .env if present
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_load_dotenv(PROJECT_ROOT / ".env")


class Settings(BaseModel):
    """Application configuration settings and file path definitions."""
    app_name: str = "UniHack Simplifi PIM API"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # Root directory discovery
    project_root: Path = PROJECT_ROOT
    
    # Data paths
    raw_input_path: Path = project_root / "Unihack_ Sample Dataset - Input.csv"
    ground_truth_path: Path = project_root / "Unihack_ Expected Output - Delivery Format.csv"
    enriched_catalog_path: Path = project_root / "data" / "output" / "enriched_catalog_252_columns.csv"
    benchmark_report_path: Path = project_root / "data" / "output" / "benchmark_report.json"
    dictionaries_dir: Path = project_root / "data" / "dictionaries"
    output_dir: Path = project_root / "data" / "output"
    # Database configuration
    database_path: Path = Path(os.getenv("DATABASE_PATH", str(project_root / "data" / "unilog_pim.db")))
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{project_root / 'data' / 'unilog_pim.db'}")
    
    # Frontend build assets
    frontend_dist_dir: Path = project_root / "src" / "frontend" / "dist"
    
    # Server network settings
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    cors_origins: List[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8000").split(",")
        if origin.strip()
    ]

    # Security & Cryptography Configuration
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-insecure-secret-key-change-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expiration_seconds: int = int(os.getenv("JWT_EXPIRATION_SECONDS", "1800"))  # 30 minutes default

    # Initial Admin Bootstrap (Optional in development, required in production)
    admin_initial_email: Optional[str] = os.getenv("ADMIN_INITIAL_EMAIL", "admin@unilog.com" if os.getenv("ENVIRONMENT", "development").lower() != "production" else None)
    admin_initial_password: Optional[str] = os.getenv("ADMIN_INITIAL_PASSWORD", "Admin@123456" if os.getenv("ENVIRONMENT", "development").lower() != "production" else None)
    admin_initial_name: Optional[str] = os.getenv("ADMIN_INITIAL_NAME", "System Administrator")

    # Gemini AI Extraction Provider Configuration
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    gemini_enabled: bool = (
        os.getenv("GEMINI_ENABLED", "false").lower() in ("true", "1", "yes")
        and bool(os.getenv("GEMINI_API_KEY", "").strip())
    )
    gemini_schema_version: str = os.getenv("GEMINI_SCHEMA_VERSION", "v1.0.0")
    gemini_lov_version: str = os.getenv("GEMINI_LOV_VERSION", "lov_v1.0.0")
    gemini_input_cost_per_million: float = float(os.getenv("GEMINI_INPUT_COST_PER_MILLION", "0.075"))
    gemini_output_cost_per_million: float = float(os.getenv("GEMINI_OUTPUT_COST_PER_MILLION", "0.300"))

    def __init__(self, **data):
        super().__init__(**data)
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Verify fallback data locations
        if not self.raw_input_path.exists():
            fallback_raw = self.project_root / "data" / "raw" / "Unihack_ Sample Dataset - Input.csv"
            if fallback_raw.exists():
                self.raw_input_path = fallback_raw
        if not self.ground_truth_path.exists():
            fallback_gt = self.project_root / "data" / "ground_truth" / "Unihack_ Expected Output - Delivery Format.csv"
            if fallback_gt.exists():
                self.ground_truth_path = fallback_gt


settings = Settings()
