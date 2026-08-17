"""
Backend configuration and system paths for Industrial Product Intelligence & PIM Enrichment Platform.
"""

import os
from pathlib import Path
from typing import List
from pydantic import BaseModel


class Settings(BaseModel):
    """Application configuration settings and file path definitions."""
    app_name: str = "UniHack Industrial Product Intelligence PIM API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Root directory discovery
    project_root: Path = Path(__file__).resolve().parent.parent.parent
    
    # Data paths
    raw_input_path: Path = project_root / "Unihack_ Sample Dataset - Input.csv"
    ground_truth_path: Path = project_root / "Unihack_ Expected Output - Delivery Format.csv"
    enriched_catalog_path: Path = project_root / "data" / "output" / "enriched_catalog_252_columns.csv"
    benchmark_report_path: Path = project_root / "data" / "output" / "benchmark_report.json"
    dictionaries_dir: Path = project_root / "data" / "dictionaries"
    output_dir: Path = project_root / "data" / "output"
    
    # Frontend build assets
    frontend_dist_dir: Path = project_root / "src" / "frontend" / "dist"
    
    # Server network settings
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    cors_origins: List[str] = ["*"]

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
