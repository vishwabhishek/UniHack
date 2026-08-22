"""
Persistent Deterministic Extraction Cache for Official Manufacturer Evidence.

Prevents unnecessary Gemini API calls when source documents, MPNs, models, schemas, and LOVs have not changed.
Cache Key Formula:
  SHA256(source_file_hash + "::" + mpn + "::" + model_name + "::" + schema_version + "::" + lov_version)
"""

from __future__ import annotations

import os
import json
import hashlib
import logging
from typing import Dict, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime, timezone
from threading import Lock

from .providers.base import ExtractionResult, GeminiExtractedFact

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "cache"
CACHE_FILE = CACHE_DIR / "gemini_extractions.json"


class GeminiExtractionCache:
    """
    Thread-safe, persistent atomic JSON cache for Gemini AI extractions.
    """

    def __init__(self, cache_file_path: Optional[Path] = None):
        self.cache_path = cache_file_path or CACHE_FILE
        self.cache_dir = self.cache_path.parent
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._cache_data: Dict[str, Dict[str, Any]] = {}
        self._hits: int = 0
        self._misses: int = 0
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cache entries from disk if present."""
        with self._lock:
            if not self.cache_path.exists():
                self._cache_data = {}
                return
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._cache_data = data.get("entries", {})
                    self._hits = data.get("hits", 0)
                    self._misses = data.get("misses", 0)
            except Exception as e:
                logger.warning(f"Failed to read cache file at {self.cache_path}: {e}. Initializing empty cache.")
                self._cache_data = {}

    def _save_cache(self) -> None:
        """Atomically persist cache entries to disk."""
        tmp_file = self.cache_path.with_suffix(".tmp")
        try:
            payload = {
                "version": "1.0.0",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "hits": self._hits,
                "misses": self._misses,
                "total_entries": len(self._cache_data),
                "entries": self._cache_data,
            }
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            tmp_file.replace(self.cache_path)
        except Exception as e:
            logger.error(f"Failed to write cache to {self.cache_path}: {e}")
            if tmp_file.exists():
                try:
                    tmp_file.unlink()
                except Exception:
                    pass

    @staticmethod
    def generate_cache_key(
        source_hash: str,
        mpn: str,
        model_name: str,
        schema_version: str,
        lov_version: str,
    ) -> str:
        """
        Deterministic 5-factor cache key generator.
        """
        raw_key = (
            f"{source_hash.strip()}::"
            f"{mpn.strip().upper()}::"
            f"{model_name.strip()}::"
            f"{schema_version.strip()}::"
            f"{lov_version.strip()}"
        )
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def get(self, cache_key: str) -> Optional[ExtractionResult]:
        """
        Retrieve a cached ExtractionResult by cache key.
        Returns None on cache miss.
        """
        with self._lock:
            entry = self._cache_data.get(cache_key)
            if entry is None:
                self._misses += 1
                return None

            self._hits += 1
            entry["hit_count"] = entry.get("hit_count", 0) + 1
            entry["last_accessed_at"] = datetime.now(timezone.utc).isoformat()
            self._save_cache()

            try:
                result_dict = entry.get("result", {})
                facts = [GeminiExtractedFact(**f) for f in result_dict.get("facts", [])]
                
                return ExtractionResult(
                    mpn=result_dict.get("mpn", ""),
                    brand=result_dict.get("brand"),
                    manufacturer=result_dict.get("manufacturer"),
                    facts=facts,
                    unsupported_fields=result_dict.get("unsupported_fields", []),
                    conflicts=result_dict.get("conflicts", []),
                    model_name=result_dict.get("model_name", "gemini_cached"),
                    prompt_version=result_dict.get("prompt_version", "v1.0.0"),
                    source_hash=result_dict.get("source_hash"),
                    extraction_timestamp=result_dict.get("extraction_timestamp", datetime.now(timezone.utc).isoformat()),
                    status="SUCCESS",
                    ai_extraction_unavailable=False,
                )
            except Exception as e:
                logger.warning(f"Failed to deserialize cached result for {cache_key}: {e}")
                return None

    def set(
        self,
        cache_key: str,
        mpn: str,
        source_hash: str,
        model_name: str,
        schema_version: str,
        lov_version: str,
        result: ExtractionResult,
        estimated_prompt_tokens: int = 450,
        estimated_candidate_tokens: int = 150,
    ) -> None:
        """
        Store an ExtractionResult into the persistent cache.
        """
        with self._lock:
            # Serialize facts
            facts_list = [f.model_dump() for f in result.facts]
            result_dict = {
                "mpn": result.mpn,
                "brand": result.brand,
                "manufacturer": result.manufacturer,
                "facts": facts_list,
                "unsupported_fields": result.unsupported_fields,
                "conflicts": result.conflicts,
                "model_name": result.model_name,
                "prompt_version": result.prompt_version,
                "source_hash": result.source_hash,
                "extraction_timestamp": result.extraction_timestamp,
            }

            self._cache_data[cache_key] = {
                "cache_key": cache_key,
                "mpn": mpn.strip().upper(),
                "source_hash": source_hash,
                "model_name": model_name,
                "schema_version": schema_version,
                "lov_version": lov_version,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_accessed_at": datetime.now(timezone.utc).isoformat(),
                "hit_count": 0,
                "estimated_prompt_tokens": estimated_prompt_tokens,
                "estimated_candidate_tokens": estimated_candidate_tokens,
                "result": result_dict,
            }
            self._save_cache()

    def get_stats(self) -> Dict[str, Any]:
        """
        Return comprehensive cache usage and ROI statistics.
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_ratio = round((self._hits / max(1, total_requests)) * 100.0, 1)
            file_size = self.cache_path.stat().st_size if self.cache_path.exists() else 0

            # Compute estimated tokens saved ($0.075 / 1M input tokens, $0.30 / 1M output tokens for gemini-2.5-flash)
            total_saved_prompt_tokens = sum(
                e.get("estimated_prompt_tokens", 450) * e.get("hit_count", 0)
                for e in self._cache_data.values()
            )
            total_saved_candidate_tokens = sum(
                e.get("estimated_candidate_tokens", 150) * e.get("hit_count", 0)
                for e in self._cache_data.values()
            )
            total_saved_tokens = total_saved_prompt_tokens + total_saved_candidate_tokens

            # Pricing from configuration
            input_rate = float(os.getenv("GEMINI_INPUT_COST_PER_MILLION", "0.075"))
            output_rate = float(os.getenv("GEMINI_OUTPUT_COST_PER_MILLION", "0.300"))
            cost_saved_usd = (
                (total_saved_prompt_tokens / 1_000_000.0) * input_rate +
                (total_saved_candidate_tokens / 1_000_000.0) * output_rate
            )

            return {
                "total_entries": len(self._cache_data),
                "hits": self._hits,
                "misses": self._misses,
                "total_requests": total_requests,
                "hit_ratio_percent": hit_ratio,
                "tokens_saved_estimate": total_saved_tokens,
                "cost_saved_usd_estimate": round(cost_saved_usd, 6),
                "file_size_bytes": file_size,
                "cache_file_path": str(self.cache_path),
            }

    def clear(self) -> None:
        """Invalidate and wipe the entire cache."""
        with self._lock:
            self._cache_data = {}
            self._hits = 0
            self._misses = 0
            self._save_cache()

    def invalidate_mpn(self, mpn: str) -> int:
        """Invalidate all cache entries for a specific MPN."""
        with self._lock:
            target_mpn = mpn.strip().upper()
            keys_to_remove = [
                k for k, v in self._cache_data.items()
                if v.get("mpn") == target_mpn
            ]
            for k in keys_to_remove:
                del self._cache_data[k]
            if keys_to_remove:
                self._save_cache()
            return len(keys_to_remove)

    def invalidate_by_source_hash(self, source_hash: str) -> int:
        """Invalidate all cache entries generated from a specific source file hash."""
        with self._lock:
            target_hash = source_hash.strip()
            keys_to_remove = [
                k for k, v in self._cache_data.items()
                if v.get("source_hash") == target_hash
            ]
            for k in keys_to_remove:
                del self._cache_data[k]
            if keys_to_remove:
                self._save_cache()
            return len(keys_to_remove)


# Default global instance
default_extraction_cache = GeminiExtractionCache()

