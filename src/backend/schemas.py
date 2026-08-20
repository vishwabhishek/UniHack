"""
Pydantic Request & Response Schemas for UniHack PIM API.
"""

from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 1. Product & Attribute Schemas
# ---------------------------------------------------------------------------

class RawProductSchema(BaseModel):
    """Raw distributor supplier record."""
    mfg_part_num: str
    part_desc: str
    e1_brand: Optional[str] = None
    unilog_brand: Optional[str] = None
    dib_brand: Optional[str] = None
    part_manuf: Optional[str] = None
    row_id: Optional[int] = None


class AttributeTripleSchema(BaseModel):
    """Normalized technical specification slot triple (Label, Value, UOM)."""
    label: str = ""
    value: str = ""
    uom: Optional[str] = ""


class PhysicalDimensionsSchema(BaseModel):
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


class ProductListItem(BaseModel):
    """Compact product summary for high-performance table views."""
    id: str
    row_id: int
    part_number: str
    sku: str
    mfg_part_number: str
    brand_name: str
    manufacturer_name: str
    classpath: str
    product_name: str
    dept: str
    invoice_desc: str
    invoice_desc_len: int
    mobile_desc: str
    mobile_desc_len: int
    short_desc: str
    confidence_score: float
    status: str  # Validated | Enriched | Flagged | Draft
    validation_flags: List[str] = Field(default_factory=list)


class ProductListResponse(BaseModel):
    """Paginated catalog exploration response."""
    items: List[ProductListItem]
    total: int
    page: int
    limit: int
    total_pages: int


class ProductDetailResponse(BaseModel):
    """Complete 252-column product detail entity."""
    id: str
    row_id: int
    part_number: str
    sku: str
    mfg_part_number: str
    alternate_part_number: Optional[str] = ""
    upc: Optional[str] = ""
    ean: Optional[str] = ""
    gtin: Optional[str] = ""
    unspsc: str
    
    # Audit & Raw Inputs
    raw: Dict[str, Any]
    dept: str
    class_name: str
    fine: str
    
    # Canonical Entity Resolution
    manufacturer_name: str
    brand_name: str
    trade_name: Optional[str] = ""
    mfr_url: Optional[str] = ""
    ref_urls: List[str] = Field(default_factory=list)
    
    # Taxonomy
    classpath: str
    product_name: str
    
    # 5-Tier Descriptions
    invoice_desc: str
    invoice_desc_len: int
    mobile_desc: str
    mobile_desc_len: int
    short_desc: str
    long_desc1: str
    retail_desc: str
    marketing_description: str
    
    # Features & Specs
    item_features: List[str] = Field(default_factory=list)
    with_spec: Optional[str] = ""
    standard_approvals: Optional[str] = ""
    prop_65: Optional[str] = ""
    application: Optional[str] = ""
    includes: Optional[str] = ""
    
    # Dynamic Triplet Attributes
    attributes: List[AttributeTripleSchema] = Field(default_factory=list)
    
    # Dimensions & Packaging
    dimensions: PhysicalDimensionsSchema = Field(default_factory=PhysicalDimensionsSchema)
    
    # Commercial Terms
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
    
    # Quality, Confidence & Provenance
    confidence_score: float
    confidence_breakdown: Dict[str, float] = Field(default_factory=dict)
    validation_flags: List[str] = Field(default_factory=list)
    field_provenance: Dict[str, Any] = Field(default_factory=dict)
    status: str
    
    # 252-Column Dictionary
    delivery_columns: Optional[Dict[str, str]] = None


# ---------------------------------------------------------------------------
# 2. Statistics & Filter Schemas
# ---------------------------------------------------------------------------

class CatalogStatsResponse(BaseModel):
    """Overall catalog health, KPI counts, and compliance rates."""
    total_items: int
    enriched_count: int
    validated_count: int
    flagged_count: int
    draft_count: int
    mean_confidence: float
    median_confidence: float
    invoice_compliance_pct: float
    mobile_compliance_pct: float
    lov_compliance_pct: float
    schema_columns_count: int
    status_counts: Dict[str, int]
    dept_counts: Dict[str, int]
    top_brands: Dict[str, int]


class FilterOptionsResponse(BaseModel):
    """Available search and drill-down filter facet counts."""
    statuses: List[Dict[str, Any]]
    departments: List[Dict[str, Any]]
    brands: List[Dict[str, Any]]


# ---------------------------------------------------------------------------
# 3. Interactive Playground Schemas
# ---------------------------------------------------------------------------

class TransformRequest(BaseModel):
    """Arbitrary raw supplier input for instant sandbox transformation."""
    part_desc: str
    mfg_part_num: Optional[str] = ""
    e1_brand: Optional[str] = None
    unilog_brand: Optional[str] = None
    dib_brand: Optional[str] = None
    part_manuf: Optional[str] = None
    row_id: Optional[int] = None


class PipelineStageOutput(BaseModel):
    """Individual stage step visualization metadata."""
    stage_id: int
    stage_name: str
    description: str
    duration_ms: float
    output: Dict[str, Any]


class TransformResponse(BaseModel):
    """Full transformation result with stage outputs and sub-second latency timing."""
    # 5-Tier Descriptions (Required for backward compat with integration tests)
    invoice_desc: str
    invoice_desc_len: int
    mobile_desc: str
    mobile_desc_len: int
    short_desc: str
    long_desc1: str
    retail_desc: str
    marketing_description: str
    
    # Classification & Entity
    brand_name: str
    manufacturer_name: str
    classpath: str
    product_name: str
    unspsc: str
    
    # Specs & Attributes
    item_features: List[str] = Field(default_factory=list)
    attributes: List[AttributeTripleSchema] = Field(default_factory=list)
    dimensions: PhysicalDimensionsSchema = Field(default_factory=PhysicalDimensionsSchema)
    
    # Confidence & Flags
    confidence_score: float
    confidence_breakdown: Dict[str, float] = Field(default_factory=dict)
    validation_flags: List[str] = Field(default_factory=list)
    status: str
    
    # Stage-by-Stage Breakdown & Timing
    stages: List[PipelineStageOutput] = Field(default_factory=list)
    total_latency_ms: float
    
    # Full 252-Column Map
    delivery_columns: Dict[str, str] = Field(default_factory=dict)


class PlaygroundPreset(BaseModel):
    """Preset sample for one-click testing."""
    id: str
    name: str
    category: str
    mfg_part_num: str
    part_desc: str
    part_manuf: str
    e1_brand: Optional[str] = None
    unilog_brand: Optional[str] = None
    dib_brand: Optional[str] = None


# ---------------------------------------------------------------------------
# 4. Human-In-The-Loop (HITL) Review Schemas
# ---------------------------------------------------------------------------

class ReviewItem(BaseModel):
    """Product awaiting human validation or correction."""
    id: str
    row_id: int
    part_number: str
    mfg_part_num: str
    brand_name: str
    manufacturer_name: str
    classpath: str
    invoice_desc: str
    mobile_desc: str
    short_desc: str
    confidence_score: float
    status: str
    anomaly_flags: List[str]
    raw_part_desc: str
    raw_manufacturer: str


class ReviewQueueResponse(BaseModel):
    """Review queue list response."""
    items: List[ReviewItem]
    total: int
    flagged_count: int
    low_confidence_count: int


class ProductUpdatePayload(BaseModel):
    """Fields modifiable during human review."""
    brand_name: Optional[str] = None
    manufacturer_name: Optional[str] = None
    classpath: Optional[str] = None
    unspsc: Optional[str] = None
    invoice_desc: Optional[str] = None
    mobile_desc: Optional[str] = None
    short_desc: Optional[str] = None
    long_desc1: Optional[str] = None
    marketing_description: Optional[str] = None
    attributes: Optional[List[AttributeTripleSchema]] = None
    status: Optional[str] = None
    reviewer_notes: Optional[str] = None


class ApprovalPayload(BaseModel):
    """Reviewer approval payload."""
    approved: bool = True
    notes: Optional[str] = ""


class ApprovalResponse(BaseModel):
    """Approval result."""
    success: bool
    status: str
    id: str
    message: str


# ---------------------------------------------------------------------------
# 5. QA Benchmark Schemas
# ---------------------------------------------------------------------------

class BenchmarkRunRequest(BaseModel):
    """Trigger benchmark evaluation run."""
    force_recompute: bool = False
