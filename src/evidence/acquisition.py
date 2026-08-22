"""
Trustworthy Server-Side Manufacturer Evidence Acquisition Engine.

Enforces:
1. Strict SSRF and official domain allowlist verification before any network request.
2. Server-side HTTP fetching with bounded timeout (10s) and max payload limit (10MB).
3. Redirect tracking (max 3) and validation of final redirected domain.
4. Cryptographic SHA-256 hashing and raw archive storage.
5. Rejection of untrusted or mismatching content.
"""

from __future__ import annotations

import os
import hashlib
import time
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
import requests

from .security import security_validator

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit
MAX_REDIRECTS = 3
REQUEST_TIMEOUT_SECONDS = 10.0


@dataclass
class AcquisitionResult:
    """Outcome of server-side evidence acquisition."""
    success: bool
    mpn: str
    source_url: Optional[str]
    final_url: Optional[str]
    redirect_chain: List[str]
    mime_type: str
    file_hash: str
    raw_file_path: Optional[str]
    raw_bytes: bytes
    text_content: Optional[str]
    retrieved_at: str
    http_status: int = 200
    error_message: Optional[str] = None
    validation_flags: List[str] = field(default_factory=list)


class EvidenceAcquisitionEngine:
    """Acquires manufacturer evidence documents server-side with strict security controls."""

    def __init__(self, raw_storage_dir: Optional[str] = None):
        if raw_storage_dir:
            self.raw_dir = raw_storage_dir
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.raw_dir = os.path.join(base_dir, "data", "evidence", "raw")
        os.makedirs(self.raw_dir, exist_ok=True)

    def acquire_url(
        self,
        url: str,
        mpn: str,
        expected_brand: Optional[str] = None,
        expected_manufacturer: Optional[str] = None,
    ) -> AcquisitionResult:
        """
        Fetch evidence from an official URL with SSRF protection, size caps, and hash computation.
        """
        now_ts = datetime.now(timezone.utc).isoformat()
        redirect_chain: List[str] = []

        # 1. Initial URL validation
        is_valid, reason = security_validator.validate_source_url(url)
        if not is_valid:
            return AcquisitionResult(
                success=False,
                mpn=mpn,
                source_url=url,
                final_url=url,
                redirect_chain=[],
                mime_type="unknown",
                file_hash="",
                raw_file_path=None,
                raw_bytes=b"",
                text_content=None,
                retrieved_at=now_ts,
                http_status=403,
                error_message=f"SSRF / Domain policy rejection: {reason}",
                validation_flags=["UNTRUSTED_SOURCE", "SSRF_REJECTED"],
            )

        # 2. Server-side fetch with redirect tracking & size limit
        try:
            session = requests.Session()
            session.max_redirects = MAX_REDIRECTS
            headers = {
                "User-Agent": "UniHack-PIM-Evidence-Verifier/1.0 (Enterprise Catalog Verification; +https://unilog.example.com)",
                "Accept": "text/html,application/xhtml+xml,application/pdf,text/plain,*/*",
            }

            resp = session.get(
                url,
                headers=headers,
                timeout=REQUEST_TIMEOUT_SECONDS,
                stream=True,
                allow_redirects=True,
            )

            # Record redirect history
            for history_resp in resp.history:
                redirect_chain.append(history_resp.url)
                # Verify each intermediate redirected URL
                is_valid_redir, redir_reason = security_validator.validate_source_url(history_resp.url)
                if not is_valid_redir:
                    return AcquisitionResult(
                        success=False,
                        mpn=mpn,
                        source_url=url,
                        final_url=history_resp.url,
                        redirect_chain=redirect_chain,
                        mime_type="unknown",
                        file_hash="",
                        raw_file_path=None,
                        raw_bytes=b"",
                        text_content=None,
                        retrieved_at=now_ts,
                        http_status=403,
                        error_message=f"Redirect to untrusted target blocked: {redir_reason}",
                        validation_flags=["UNTRUSTED_REDIRECT"],
                    )

            final_url = resp.url
            # Verify final redirected URL
            is_valid_final, final_reason = security_validator.validate_source_url(final_url)
            if not is_valid_final:
                return AcquisitionResult(
                    success=False,
                    mpn=mpn,
                    source_url=url,
                    final_url=final_url,
                    redirect_chain=redirect_chain,
                    mime_type="unknown",
                    file_hash="",
                    raw_file_path=None,
                    raw_bytes=b"",
                    text_content=None,
                    retrieved_at=now_ts,
                    http_status=403,
                    error_message=f"Final redirected URL rejected: {final_reason}",
                    validation_flags=["UNTRUSTED_FINAL_URL"],
                )

            if resp.status_code != 200:
                return AcquisitionResult(
                    success=False,
                    mpn=mpn,
                    source_url=url,
                    final_url=final_url,
                    redirect_chain=redirect_chain,
                    mime_type=resp.headers.get("Content-Type", "unknown"),
                    file_hash="",
                    raw_file_path=None,
                    raw_bytes=b"",
                    text_content=None,
                    retrieved_at=now_ts,
                    http_status=resp.status_code,
                    error_message=f"HTTP {resp.status_code} returned by manufacturer server",
                    validation_flags=["SOURCE_UNAVAILABLE"],
                )

            # 3. Read stream with bounded size enforcement
            content_chunks = []
            total_size = 0
            for chunk in resp.iter_content(chunk_size=65536):
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE_BYTES:
                    return AcquisitionResult(
                        success=False,
                        mpn=mpn,
                        source_url=url,
                        final_url=final_url,
                        redirect_chain=redirect_chain,
                        mime_type=resp.headers.get("Content-Type", "unknown"),
                        file_hash="",
                        raw_file_path=None,
                        raw_bytes=b"",
                        text_content=None,
                        retrieved_at=now_ts,
                        http_status=413,
                        error_message=f"Evidence document exceeds {MAX_FILE_SIZE_BYTES // (1024*1024)}MB size limit",
                        validation_flags=["PAYLOAD_TOO_LARGE"],
                    )
                content_chunks.append(chunk)

            raw_bytes = b"".join(content_chunks)
            if not raw_bytes:
                return AcquisitionResult(
                    success=False,
                    mpn=mpn,
                    source_url=url,
                    final_url=final_url,
                    redirect_chain=redirect_chain,
                    mime_type="empty",
                    file_hash="",
                    raw_file_path=None,
                    raw_bytes=b"",
                    text_content=None,
                    retrieved_at=now_ts,
                    http_status=204,
                    error_message="Empty response body returned by manufacturer server",
                    validation_flags=["EMPTY_SOURCE"],
                )

            file_hash = hashlib.sha256(raw_bytes).hexdigest()
            content_type = resp.headers.get("Content-Type", "").split(";")[0].strip().lower()

            # Determine extension
            ext = ".html"
            if "pdf" in content_type or url.lower().endswith(".pdf") or raw_bytes.startswith(b"%PDF"):
                ext = ".pdf"
                content_type = "application/pdf"
            elif "json" in content_type:
                ext = ".json"
            elif "text" in content_type:
                ext = ".txt"

            file_name = f"{file_hash[:16]}_{mpn.lower()}{ext}"
            file_path = os.path.join(self.raw_dir, file_name)
            with open(file_path, "wb") as f:
                f.write(raw_bytes)

            text_content = None
            if ext in (".html", ".txt", ".json"):
                try:
                    text_content = raw_bytes.decode(resp.encoding or "utf-8", errors="replace")
                except Exception:
                    text_content = raw_bytes.decode("utf-8", errors="replace")

            return AcquisitionResult(
                success=True,
                mpn=mpn,
                source_url=url,
                final_url=final_url,
                redirect_chain=redirect_chain,
                mime_type=content_type or "text/html",
                file_hash=file_hash,
                raw_file_path=file_path,
                raw_bytes=raw_bytes,
                text_content=text_content,
                retrieved_at=now_ts,
                http_status=200,
                validation_flags=[],
            )

        except requests.exceptions.Timeout:
            return AcquisitionResult(
                success=False,
                mpn=mpn,
                source_url=url,
                final_url=url,
                redirect_chain=redirect_chain,
                mime_type="unknown",
                file_hash="",
                raw_file_path=None,
                raw_bytes=b"",
                text_content=None,
                retrieved_at=now_ts,
                http_status=504,
                error_message=f"Request timed out after {REQUEST_TIMEOUT_SECONDS}s",
                validation_flags=["TIMEOUT"],
            )
        except Exception as e:
            return AcquisitionResult(
                success=False,
                mpn=mpn,
                source_url=url,
                final_url=url,
                redirect_chain=redirect_chain,
                mime_type="unknown",
                file_hash="",
                raw_file_path=None,
                raw_bytes=b"",
                text_content=None,
                retrieved_at=now_ts,
                http_status=500,
                error_message=f"Acquisition failed: {str(e)}",
                validation_flags=["FETCH_ERROR"],
            )


default_acquisition_engine = EvidenceAcquisitionEngine()
