"""
Pydantic Data Models for Official Manufacturer Evidence Ingestion & Traceability.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum


class SourceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    UNAVAILABLE = "UNAVAILABLE"
    REJECTED_UNTRUSTED = "REJECTED_UNTRUSTED"
    PENDING_REVIEW = "PENDING_REVIEW"
    STALE = "STALE"
    SUPERSEDED = "SUPERSEDED"


class EvidenceType(str, Enum):
    MANUFACTURER_PAGE = "manufacturer_page"
    MANUFACTURER_PDF = "manufacturer_pdf"


class SourceRegistryEntry(BaseModel):
    """Manifest record for a registered manufacturer source."""
    source_id: str
    url: Optional[str] = None
    mpn: str
    brand: str
    manufacturer: str
    source_type: str = EvidenceType.MANUFACTURER_PAGE.value
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    file_hash: str
    source_status: str = SourceStatus.ACTIVE.value
    raw_file_path: Optional[str] = None
    processed_file_path: Optional[str] = None
    chunks_count: int = 0
    error_message: Optional[str] = None
    title: Optional[str] = None
    superseded_by: Optional[str] = None
    parser_version: str = "v1.0.0"
    retrieval_metadata: Dict[str, Any] = Field(default_factory=dict)



class EvidenceChunk(BaseModel):
    """Structured discrete evidence chunk grouped by heading, specification table, or page."""
    chunk_id: str
    source_id: str
    mpn: str
    brand: str
    manufacturer: str
    section_title: str
    page_number: Optional[int] = 1
    text_content: str
    key_value_specs: Dict[str, str] = Field(default_factory=dict)
    chunk_hash: str


class ExtractedCandidate(BaseModel):
    """Candidate attribute value extracted from official evidence with full lineage."""
    field_name: str
    candidate_value: str
    normalized_value: str
    source_url: Optional[str] = None
    source_type: str = EvidenceType.MANUFACTURER_PAGE.value
    source_title: str
    source_page_or_section: str
    evidence_excerpt: str
    extraction_method: str = "deterministic_rule"
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    confidence: float = 1.0
    verification_status: str = "verified"
    dictionary_identity: Optional[str] = None
    chunk_id: Optional[str] = None
    model_name: Optional[str] = None
    prompt_version: Optional[str] = None
    source_hash: Optional[str] = None
    conflicts: List[str] = Field(default_factory=list)
    extraction_reason: Optional[str] = None
    unresolved_reason: Optional[str] = None
    ai_extraction_unavailable: bool = False


class SourceRegistrationRequest(BaseModel):
    """Payload for registering a new manufacturer evidence document or URL."""
    url: Optional[str] = None
    mpn: str
    brand: str
    manufacturer: str
    source_type: str = EvidenceType.MANUFACTURER_PAGE.value
    title: Optional[str] = None
    mime_type: Optional[str] = None
    raw_content: Optional[str] = None  # Raw HTML or text if pre-downloaded


class SourceRegistrationResponse(BaseModel):
    """Result of source ingestion."""
    success: bool
    source_id: str
    source_status: str
    chunks_count: int
    file_hash: str
    message: str
    validation_flags: List[str] = Field(default_factory=list)


class EvidenceQueryResponse(BaseModel):
    """Search query response over official evidence chunks."""
    mpn: str
    brand: Optional[str] = None
    total_chunks: int
    chunks: List[EvidenceChunk]
    candidates: List[ExtractedCandidate] = Field(default_factory=list)
