"""
Manufacturer Evidence Source Registry Manager.

Maintains the persistent source manifest in data/evidence/source_registry.json.
Guarantees auditability, SHA256 file hashing, and non-destructive persistence.
"""

import json
import os
import hashlib
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone

from .models import (
    SourceRegistryEntry,
    SourceRegistrationRequest,
    SourceRegistrationResponse,
    SourceStatus,
    EvidenceType,
    EvidenceChunk
)
from .security import security_validator
from src.backend.db.repositories.evidence import evidence_repo
from .html_parser import parse_manufacturer_html
from .pdf_parser import parse_manufacturer_pdf_text
from .chunker import create_evidence_chunks

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "evidence")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
REGISTRY_FILE = os.path.join(DATA_DIR, "source_registry.json")


from .acquisition import default_acquisition_engine, AcquisitionResult
from .cache import default_extraction_cache
from .pdf_parser import parse_manufacturer_pdf_file, parse_manufacturer_pdf_text


class EvidenceRegistryManager:
    """Manages persistent registration, caching, lifecycle, and loading of official manufacturer evidence."""

    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        self.raw_dir = os.path.join(data_dir, "raw")
        self.processed_dir = os.path.join(data_dir, "processed")
        self.registry_file = os.path.join(data_dir, "source_registry.json")
        self._ensure_directories()
        self._registry_cache: Dict[str, SourceRegistryEntry] = {}
        self.load_registry()

    def _ensure_directories(self):
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        if not os.path.exists(self.registry_file):
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)

    def load_registry(self) -> List[SourceRegistryEntry]:
        """Load all registered sources from the JSON manifest."""
        self._ensure_directories()
        try:
            with open(self.registry_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._registry_cache = {
                    item["source_id"]: SourceRegistryEntry(**item) for item in data
                }
        except Exception:
            self._registry_cache = {}
        return list(self._registry_cache.values())

    def _save_registry(self):
        """Save in-memory registry to disk atomically."""
        self._ensure_directories()
        entries = [entry.model_dump() for entry in self._registry_cache.values()]
        temp_file = f"{self.registry_file}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)
        os.replace(temp_file, self.registry_file)

    def register_source(self, req: SourceRegistrationRequest) -> SourceRegistrationResponse:
        """
        Register and process an official manufacturer evidence source.
        Performs server-side retrieval, SSRF validation, computes SHA256, parses content, and writes chunks.
        """
        # 1. Validate URL security if provided
        if req.url:
            is_valid_url, sec_reason = security_validator.validate_source_url(req.url)
            if not is_valid_url:
                source_id = f"src_{req.mpn.lower()}_{hashlib.md5(req.url.encode()).hexdigest()[:8]}"
                sec_flags = ["UNTRUSTED_SOURCE"] if any(w in (sec_reason or "").lower() for w in ["allowlist", "unauthorized", "scheme", "hostname"]) else ["BLOCKED_SSRF"]
                status_val = SourceStatus.REJECTED_UNTRUSTED.value if "UNTRUSTED_SOURCE" in sec_flags else SourceStatus.UNAVAILABLE.value

                entry = SourceRegistryEntry(
                    source_id=source_id,
                    url=req.url,
                    mpn=req.mpn,
                    brand=req.brand,
                    manufacturer=req.manufacturer,
                    source_type=req.source_type,
                    file_hash="",
                    source_status=status_val,
                    error_message=sec_reason,
                    title=req.title or "Untrusted / Blocked Source",
                    retrieval_metadata={"error": sec_reason, "flags": sec_flags}
                )
                self._registry_cache[source_id] = entry
                self._save_registry()
                return SourceRegistrationResponse(
                    success=False,
                    source_id=source_id,
                    source_status=status_val,
                    chunks_count=0,
                    file_hash="",
                    message=sec_reason or "Source failed security validation",
                    validation_flags=sec_flags
                )

        # 2. Acquire content: server-side fetch if no direct raw_content provided
        if req.url and not req.raw_content:
            acq_res = default_acquisition_engine.acquire_url(
                url=req.url,
                mpn=req.mpn,
                expected_brand=req.brand,
                expected_manufacturer=req.manufacturer,
            )
            if not acq_res.success:
                source_id = f"src_{req.mpn.lower()}_{hashlib.md5((req.url or '').encode()).hexdigest()[:8]}"
                status_val = SourceStatus.REJECTED_UNTRUSTED.value if "UNTRUSTED" in "".join(acq_res.validation_flags) else SourceStatus.UNAVAILABLE.value
                entry = SourceRegistryEntry(
                    source_id=source_id,
                    url=req.url,
                    mpn=req.mpn,
                    brand=req.brand,
                    manufacturer=req.manufacturer,
                    source_type=req.source_type,
                    file_hash="",
                    source_status=status_val,
                    error_message=acq_res.error_message,
                    title=req.title or "Unreachable / Rejected Source",
                    retrieval_metadata={
                        "final_url": acq_res.final_url,
                        "redirect_chain": acq_res.redirect_chain,
                        "http_status": acq_res.http_status,
                    }
                )
                self._registry_cache[source_id] = entry
                self._save_registry()
                try:
                    evidence_repo.upsert_source_registry_entry(
                        source_id=source_id,
                        mpn=req.mpn,
                        brand=req.brand,
                        manufacturer=req.manufacturer,
                        source_type=req.source_type,
                        file_hash="",
                        url=req.url,
                        title=entry.title,
                        status=status_val.lower(),
                    )
                except Exception:
                    pass

                val_flags = list(set(acq_res.validation_flags + (["UNAVAILABLE_SOURCE"] if status_val == SourceStatus.UNAVAILABLE.value else [])))
                return SourceRegistrationResponse(
                    success=False,
                    source_id=source_id,
                    source_status=status_val,
                    chunks_count=0,
                    file_hash="",
                    message=acq_res.error_message or "Evidence acquisition failed",
                    validation_flags=val_flags,
                )


            # Use acquired content and metadata
            content_bytes = acq_res.raw_bytes
            raw_content = acq_res.text_content or ""
            file_hash = acq_res.file_hash
            raw_path = acq_res.raw_file_path or ""
            source_type = EvidenceType.MANUFACTURER_PDF.value if acq_res.mime_type == "application/pdf" else EvidenceType.MANUFACTURER_PAGE.value
            retrieval_meta = {
                "final_url": acq_res.final_url,
                "redirect_chain": acq_res.redirect_chain,
                "http_status": acq_res.http_status,
                "mime_type": acq_res.mime_type,
            }
        else:
            # Direct content upload / fixture
            raw_content = req.raw_content or ""
            if not raw_content:
                source_id = f"src_{req.mpn.lower()}_empty"
                entry = SourceRegistryEntry(
                    source_id=source_id,
                    url=req.url,
                    mpn=req.mpn,
                    brand=req.brand,
                    manufacturer=req.manufacturer,
                    source_type=req.source_type,
                    file_hash="",
                    source_status=SourceStatus.UNAVAILABLE.value,
                    error_message="No content provided or URL is unreachable.",
                    title=req.title or "Unavailable Document"
                )
                self._registry_cache[source_id] = entry
                self._save_registry()
                return SourceRegistrationResponse(
                    success=False,
                    source_id=source_id,
                    source_status=SourceStatus.UNAVAILABLE.value,
                    chunks_count=0,
                    file_hash="",
                    message="Content unavailable or blocked",
                    validation_flags=["UNAVAILABLE_SOURCE"]
                )


            content_bytes = raw_content.encode("utf-8")
            valid_content, content_error = security_validator.validate_content_size_and_type(
                content_bytes, req.mime_type
            )
            if not valid_content:
                return SourceRegistrationResponse(
                    success=False,
                    source_id=f"src_{req.mpn.lower()}_rejected_content",
                    source_status=SourceStatus.REJECTED_UNTRUSTED.value,
                    chunks_count=0,
                    file_hash="",
                    message=content_error or "Evidence content failed security validation.",
                    validation_flags=["INVALID_EVIDENCE_CONTENT"],
                )

            file_hash = hashlib.sha256(content_bytes).hexdigest()
            source_type = req.source_type
            clean_mpn_slug = re.sub(r"[^a-zA-Z0-9_\-]", "_", req.mpn.lower())
            ext = "html" if req.source_type == EvidenceType.MANUFACTURER_PAGE.value else "txt"
            raw_filename = f"{clean_mpn_slug}_{file_hash[:8]}.{ext}"
            raw_path = os.path.join(self.raw_dir, raw_filename)
            with open(raw_path, "w", encoding="utf-8") as f:
                f.write(raw_content)
            retrieval_meta = {"mime_type": req.mime_type or "text/html"}

        # 2. Compute IDs and Parse Content into Chunks
        clean_mpn_slug = re.sub(r"[^a-zA-Z0-9_\-]", "_", req.mpn.lower())
        source_id = f"src_{clean_mpn_slug}_{file_hash[:8]}"

        if source_type == EvidenceType.MANUFACTURER_PDF.value:
            title, sections = parse_manufacturer_pdf_file(
                raw_path if raw_path and os.path.exists(raw_path) else content_bytes,
                title=req.title or "Official Spec Sheet"
            )
        else:
            title, sections = parse_manufacturer_html(raw_content)

        doc_title = req.title or title
        chunks = create_evidence_chunks(
            source_id=source_id,
            mpn=req.mpn,
            brand=req.brand,
            manufacturer=req.manufacturer,
            sections=sections
        )

        # 3. Store Processed Chunks
        processed_filename = f"{source_id}_chunks.json"
        processed_path = os.path.join(self.processed_dir, processed_filename)
        with open(processed_path, "w", encoding="utf-8") as f:
            json.dump([c.model_dump() for c in chunks], f, indent=2)

        # 4. Save Manifest Entry
        entry = SourceRegistryEntry(
            source_id=source_id,
            url=req.url,
            mpn=req.mpn,
            brand=req.brand,
            manufacturer=req.manufacturer,
            source_type=source_type,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            file_hash=file_hash,
            source_status=SourceStatus.ACTIVE.value,
            raw_file_path=os.path.relpath(raw_path, DATA_DIR) if raw_path else None,
            processed_file_path=os.path.relpath(processed_path, DATA_DIR),
            chunks_count=len(chunks),
            title=doc_title,
            retrieval_metadata=retrieval_meta,
        )
        self._registry_cache[source_id] = entry
        self._save_registry()

        try:
            evidence_repo.upsert_source_registry_entry(
                source_id=source_id,
                mpn=req.mpn,
                brand=req.brand,
                manufacturer=req.manufacturer,
                source_type=source_type,
                file_hash=file_hash,
                url=req.url,
                file_path=raw_path,
                title=doc_title,
                chunks_count=len(chunks),
                status=SourceStatus.ACTIVE.value.lower(),
                retrieved_at=entry.retrieved_at,
            )
        except Exception:
            pass

        return SourceRegistrationResponse(
            success=True,
            source_id=source_id,
            source_status=SourceStatus.ACTIVE.value,
            chunks_count=len(chunks),
            file_hash=file_hash,
            message=f"Successfully registered and chunked {len(chunks)} specification units from official source.",
            validation_flags=[]
        )

    # -----------------------------------------------------------------------
    # Source Lifecycle Management & Cache Invalidation
    # -----------------------------------------------------------------------

    def mark_source_stale(self, source_id: str, reason: str = "Source marked stale") -> bool:
        """Mark a source as stale and invalidate its extraction cache."""
        entry = self._registry_cache.get(source_id)
        if not entry:
            return False
        entry.source_status = SourceStatus.STALE.value
        entry.error_message = reason
        self._save_registry()
        try:
            evidence_repo.update_source_status(source_id, "stale")
        except Exception:
            pass
        if entry.file_hash:
            default_extraction_cache.invalidate_by_source_hash(entry.file_hash)
        return True

    def supersede_source(self, source_id: str, new_source_id: str, reason: str = "Superseded by newer source") -> bool:
        """Supersede an older source with a newer source ID."""
        entry = self._registry_cache.get(source_id)
        if not entry:
            return False
        entry.source_status = SourceStatus.SUPERSEDED.value
        entry.superseded_by = new_source_id
        entry.error_message = reason
        self._save_registry()
        try:
            evidence_repo.update_source_status(source_id, "superseded", superseded_by=new_source_id)
        except Exception:
            pass
        if entry.file_hash:
            default_extraction_cache.invalidate_by_source_hash(entry.file_hash)
        return True

    def reject_source(self, source_id: str, reason: str = "Source rejected") -> bool:
        """Reject an existing source document."""
        entry = self._registry_cache.get(source_id)
        if not entry:
            return False
        entry.source_status = SourceStatus.REJECTED_UNTRUSTED.value
        entry.error_message = reason
        self._save_registry()
        try:
            evidence_repo.update_source_status(source_id, "rejected_untrusted")
        except Exception:
            pass
        if entry.file_hash:
            default_extraction_cache.invalidate_by_source_hash(entry.file_hash)
        return True

    def reingest_source(self, source_id: str) -> SourceRegistrationResponse:
        """Re-acquire and re-chunk an existing registered source by URL."""
        entry = self._registry_cache.get(source_id)
        if not entry or not entry.url:
            return SourceRegistrationResponse(
                success=False,
                source_id=source_id,
                source_status=SourceStatus.UNAVAILABLE.value,
                chunks_count=0,
                file_hash="",
                message="Source does not exist or has no URL for re-ingestion.",
                validation_flags=["INVALID_SOURCE_ID"]
            )
        # Invalidate old cache
        if entry.file_hash:
            default_extraction_cache.invalidate_by_source_hash(entry.file_hash)

        req = SourceRegistrationRequest(
            url=entry.url,
            mpn=entry.mpn,
            brand=entry.brand,
            manufacturer=entry.manufacturer,
            source_type=entry.source_type,
            title=entry.title,
        )
        return self.register_source(req)

    def get_entry(self, source_id: str) -> Optional[SourceRegistryEntry]:
        return self._registry_cache.get(source_id)

    def get_entries_by_mpn(self, mpn: str) -> List[SourceRegistryEntry]:
        clean_mpn = mpn.strip().upper()
        return [
            entry for entry in self._registry_cache.values()
            if entry.mpn.strip().upper() == clean_mpn and entry.source_status == SourceStatus.ACTIVE.value
        ]

    def load_chunks_for_entry(self, entry: SourceRegistryEntry) -> List[EvidenceChunk]:
        """Load processed discrete chunks for a registry entry."""
        if not entry.processed_file_path:
            return []
        full_path = os.path.join(self.data_dir, entry.processed_file_path)
        if not os.path.exists(full_path):
            return []
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [EvidenceChunk(**c) for c in data]
        except Exception:
            return []

    def get_all_active_chunks(self) -> List[EvidenceChunk]:
        """Load all chunks across all active registered sources."""
        all_chunks: List[EvidenceChunk] = []
        for entry in self._registry_cache.values():
            if entry.source_status == SourceStatus.ACTIVE.value:
                all_chunks.extend(self.load_chunks_for_entry(entry))
        return all_chunks

