"""
Pydantic Data Models for Industrial Product Intelligence & PIM Enrichment Pipeline.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator


class RawProduct(BaseModel):
    """Raw supplier catalog record from distributor feed."""
    mfg_part_num: str
    part_desc: str
    e1_brand: Optional[str] = None
    unilog_brand: Optional[str] = None
    dib_brand: Optional[str] = None
    part_manuf: Optional[str] = None
    row_id: Optional[int] = None


from datetime import datetime, timezone
from enum import Enum


class SourceType(str, Enum):
    MANUFACTURER_PAGE = "manufacturer_page"
    MANUFACTURER_PDF = "manufacturer_pdf"
    SUPPLIER_INPUT = "supplier_input"
    REFERENCE_DICTIONARY = "reference_dictionary"
    MANUAL_REVIEW = "manual_review"


class ExtractionMethod(str, Enum):
    DETERMINISTIC_RULE = "deterministic_rule"
    DOCUMENT_PARSER = "document_parser"
    GEMINI_STRUCTURED_EXTRACTION = "gemini_structured_extraction"
    MANUAL_REVIEW = "manual_review"


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    CANDIDATE = "candidate"
    REJECTED = "rejected"
    MISSING_EVIDENCE = "missing_evidence"


class EvidenceRecord(BaseModel):
    """Granular evidence record representing a verified data point, extraction artifact, or audit observation."""
    field_name: str
    candidate_value: Optional[str] = ""
    normalized_value: Optional[str] = ""
    source_url: Optional[str] = None
    source_type: str = SourceType.SUPPLIER_INPUT.value
    source_title: Optional[str] = None
    source_page_or_section: Optional[str] = None
    evidence_excerpt: Optional[str] = None
    extraction_method: str = ExtractionMethod.DETERMINISTIC_RULE.value
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    confidence: float = 1.0
    verification_status: str = VerificationStatus.CANDIDATE.value
    dictionary_identity: Optional[str] = None
    model_name: Optional[str] = None
    prompt_version: Optional[str] = None
    source_hash: Optional[str] = None
    conflicts: List[str] = Field(default_factory=list)
    extraction_reason: Optional[str] = None
    unresolved_reason: Optional[str] = None
    ai_extraction_unavailable: bool = False


class ProductProvenanceSummary(BaseModel):
    """Aggregated product-level provenance health and evidence verification statistics."""
    total_fields_tracked: int = 0
    verified_fields_count: int = 0
    candidate_fields_count: int = 0
    missing_evidence_count: int = 0
    rejected_fields_count: int = 0
    verification_score: float = 0.0
    primary_sources_breakdown: Dict[str, int] = Field(default_factory=dict)


class TaxonomyCandidate(BaseModel):
    """Ranked taxonomy candidate classification with transparent score and evidence."""
    classpath: str
    unspsc: str
    dept: str
    class_name: str
    fine: str
    product_name: str
    matching_terms: List[str] = Field(default_factory=list)
    score: float = 0.0
    source_evidence: str = ""
    rule_confidence: float = 1.0
    evidence_confidence: float = 0.5
    tie_break_reason: Optional[str] = None


class TaxonomyExplanation(BaseModel):
    """Explainable classification decision with candidate rankings and routing."""
    selected_classpath: str
    selected_unspsc: str
    is_ambiguous: bool = False
    is_fallback: bool = False
    top_candidates: List[TaxonomyCandidate] = Field(default_factory=list)
    rationale: str = ""
    routing_decision: str = "AUTO_APPROVED"  # AUTO_APPROVED | ROUTED_TO_HUMAN_REVIEW


class AuditRecord(BaseModel):
    """Immutable audit log recording reviewer, timestamp, field, previous value, new value, and reason."""
    id: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")[:17])
    field_name: str
    reviewer: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    previous_value: Optional[str] = ""
    new_value: Optional[str] = ""
    action: str = "edit"  # edit | approve | reject | mark_unknown
    reason: str = ""


class FieldReviewItem(BaseModel):
    """Field-level evidence review data model for HITL curation."""
    field_name: str
    display_label: str
    raw_supplier_input: Optional[str] = ""
    candidate_value: Optional[str] = ""
    normalized_value: Optional[str] = ""
    source_citation: Optional[str] = ""
    source_excerpt: Optional[str] = ""
    source_url: Optional[str] = None
    source_type: str = "supplier_input"
    confidence: float = 1.0
    validation_flags: List[str] = Field(default_factory=list)
    verification_status: str = "candidate"  # verified | candidate | rejected | unknown | missing_evidence
    dictionary_identity: Optional[str] = None
    is_high_risk: bool = False
    is_resolved: bool = False
    audit_history: List[AuditRecord] = Field(default_factory=list)


class FieldProvenance(BaseModel):
    """Traceable provenance and evidence lineage for backward compatibility."""
    field_name: str
    source_url: Optional[str] = None
    source_type: str = "supplier_input"
    extraction_method: str = "deterministic_rule"
    section_or_rule: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    confidence: float = 1.0
    verified: bool = False


class AttributeTriple(BaseModel):
    """Normalized technical specification slot triple (Label, Value, UOM)."""
    label: str = ""
    value: str = ""
    uom: Optional[str] = ""
    provenance: Optional[FieldProvenance] = None
    evidence_records: List[EvidenceRecord] = Field(default_factory=list)


class PhysicalDimensions(BaseModel):
    """Standardized physical dimensions and packaging measurements."""
    length: Optional[str] = None
    length_uom: Optional[str] = None
    height: Optional[str] = None
    height_uom: Optional[str] = None
    width: Optional[str] = None
    width_uom: Optional[str] = None
    weight: Optional[str] = None
    weight_uom: Optional[str] = None
    volume: Optional[str] = None
    volume_uom: Optional[str] = None


class EnrichedProduct(BaseModel):
    """Comprehensive 252-column standard enriched product entity."""
    # Field-level traceable evidence and provenance
    field_evidence: Dict[str, List[EvidenceRecord]] = Field(default_factory=dict)
    provenance_summary: Optional[ProductProvenanceSummary] = None
    field_provenance: Dict[str, FieldProvenance] = Field(default_factory=dict)
    # Core Identifiers
    part_number: str = ""
    sku: str = ""
    mfg_part_number: str = ""
    alternate_part_number: Optional[str] = ""
    upc: Optional[str] = ""
    ean: Optional[str] = ""
    gtin: Optional[str] = ""
    unspsc: str = ""
    
    # Audit & Inputs
    raw: RawProduct
    dept: str = ""
    class_name: str = ""
    fine: str = ""
    
    # Entity Resolution
    manufacturer_name: str = ""
    brand_name: str = ""
    trade_name: Optional[str] = ""
    mfr_url: Optional[str] = ""
    ref_urls: List[str] = Field(default_factory=list)
    
    # Taxonomy
    classpath: str = ""
    product_name: str = ""
    taxonomy_candidates: List[TaxonomyCandidate] = Field(default_factory=list)
    taxonomy_explanation: Optional[TaxonomyExplanation] = None
    
    # 5-Tier Descriptions
    invoice_desc: str = ""  # Strictly <= 40 chars, ALL CAPS
    mobile_desc: str = ""   # Strictly 60 to 80 chars
    short_desc: str = ""
    long_desc1: str = ""
    retail_desc: str = ""
    marketing_description: str = ""
    
    # Features & Specs
    item_features: List[str] = Field(default_factory=list)  # up to 20
    with_spec: Optional[str] = ""
    standard_approvals: Optional[str] = ""
    prop_65: Optional[str] = ""
    application: Optional[str] = ""
    includes: Optional[str] = ""
    
    # Dynamic Triplet Attributes (up to 50)
    attributes: List[AttributeTriple] = Field(default_factory=list)
    
    # Physical Dimensions
    dimensions: PhysicalDimensions = Field(default_factory=PhysicalDimensions)
    
    # Commercial
    warranty: Optional[str] = ""
    list_price: Optional[str] = ""
    selling_qty: Optional[str] = "1"
    selling_uom: Optional[str] = "EA"
    standard_packaging: Optional[str] = ""
    country_of_origin: Optional[str] = ""
    discontinued: Optional[str] = "No"
    
    # Digital Assets
    product_image: Optional[str] = ""
    alternate_images: List[str] = Field(default_factory=list)
    actual_image: Optional[str] = "No"
    documents: Dict[str, str] = Field(default_factory=dict)
    
    # Quality & Confidence
    confidence_score: float = 1.0
    confidence_breakdown: Dict[str, float] = Field(default_factory=dict)
    validation_flags: List[str] = Field(default_factory=list)
    status: str = "Enriched"  # Draft | Enriched | Validated | Flagged
    audit_trail: List[AuditRecord] = Field(default_factory=list)

    @field_validator("invoice_desc")
    @classmethod
    def validate_invoice_desc(cls, v: str) -> str:
        # Enforce max 40 chars and uppercase
        if len(v) > 40:
            v = v[:40].strip()
        return v.upper()

    @field_validator("mobile_desc")
    @classmethod
    def validate_mobile_desc(cls, v: str) -> str:
        # Ensure mobile desc is valid length
        return v.strip()


class DeliveryRow(BaseModel):
    """Flattened 252-column dictionary mapping."""
    columns: Dict[str, str] = Field(default_factory=dict)
