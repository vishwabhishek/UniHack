"""
Base Provider Abstraction & Pydantic Schemas for AI-Powered Evidence Extraction.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from ..models import EvidenceChunk


class GeminiExtractedFact(BaseModel):
    """
    Candidate product attribute fact proposed by Gemini from official manufacturer evidence chunks.
    """
    field_name: str = Field(
        ...,
        description="Target attribute name, e.g. 'Fitting Type', 'Material', 'Connection Type', 'Nominal Size', 'Pressure Rating', 'Voltage', 'Amps', 'Sound Level'"
    )
    raw_value: Optional[str] = Field(
        None,
        description="Exact literal value string as stated in source document text, or null if unsupported"
    )
    normalized_candidate: Optional[str] = Field(
        None,
        description="Proposed canonicalized attribute value matching standard vocabulary"
    )
    evidence_chunk_id: Optional[str] = Field(
        None,
        description="Exact ID of the source chunk that supports this extraction"
    )
    evidence_excerpt: Optional[str] = Field(
        None,
        description="Exact verbatim quote snippet from the source chunk text"
    )
    source_page_or_section: Optional[str] = Field(
        None,
        description="Source page number or section heading cited"
    )
    confidence: float = Field(
        0.95,
        ge=0.0,
        le=1.0,
        description="Model confidence score between 0.0 and 1.0"
    )
    extraction_reason: Optional[str] = Field(
        None,
        description="Brief justification for this extraction based on the cited excerpt"
    )
    unresolved_reason: Optional[str] = Field(
        None,
        description="If value is missing, ambiguous, or unsupported, reason why"
    )
    conflicts: List[str] = Field(
        default_factory=list,
        description="Any conflicting values found across chunks for this attribute"
    )


class GeminiExtractionOutput(BaseModel):
    """
    Strict Pydantic schema for Gemini structured JSON output.
    """
    mpn: str = Field(..., description="Target manufacturer part number")
    brand: Optional[str] = Field(None, description="Manufacturer brand name")
    manufacturer: Optional[str] = Field(None, description="Legal manufacturer entity")
    facts: List[GeminiExtractedFact] = Field(
        default_factory=list,
        description="Extracted candidate facts with supporting quotes and chunk citations"
    )
    unsupported_fields: List[str] = Field(
        default_factory=list,
        description="Requested category fields with no supporting evidence in the provided chunks (honest refusal)"
    )
    conflicts: List[str] = Field(
        default_factory=list,
        description="Documented contradictions or conflicts found in the sources"
    )


class ExtractionRequest(BaseModel):
    """
    Restricted payload sent into the AI extraction provider.
    Enforces strict input boundary containing ONLY registered official evidence context.
    """
    mpn: str
    brand_candidate: Optional[str] = None
    manufacturer_candidate: Optional[str] = None
    category_candidate: Optional[str] = None
    requested_fields: List[str] = Field(default_factory=list)
    lov_subset: Dict[str, List[str]] = Field(default_factory=dict)
    uom_rules: Dict[str, str] = Field(default_factory=dict)
    source_chunks: List[EvidenceChunk] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    """
    Structured extraction result returned by an evidence extraction provider.
    """
    mpn: str
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    facts: List[GeminiExtractedFact] = Field(default_factory=list)
    unsupported_fields: List[str] = Field(default_factory=list)
    conflicts: List[str] = Field(default_factory=list)
    model_name: str = "deterministic_fallback"
    prompt_version: str = "v1.0.0"
    source_hash: Optional[str] = None
    extraction_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "SUCCESS"  # SUCCESS, AI_EXTRACTION_UNAVAILABLE, TIMEOUT, ERROR
    error_message: Optional[str] = None
    ai_extraction_unavailable: bool = False


class BaseEvidenceExtractionProvider(ABC):
    """
    Abstract interface for official manufacturer evidence extraction providers.
    """

    @abstractmethod
    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        """
        Extract candidate facts from registered manufacturer source chunks.
        """
        raise NotImplementedError
