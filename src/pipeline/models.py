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


class FieldProvenance(BaseModel):
    """Traceable provenance and evidence lineage for an enriched field."""
    field_name: str
    source_url: Optional[str] = None
    source_type: str = "raw_input"  # raw_input | canonical_dictionary | manufacturer_doc | rule_engine | human_curated | unverified
    extraction_method: str = "deterministic_regex"  # deterministic_regex | entity_lookup | uom_converter | lov_graph | formula_builder | manual_override
    section_or_rule: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    confidence: float = 1.0
    verified: bool = True


class AttributeTriple(BaseModel):
    """Normalized technical specification slot triple (Label, Value, UOM)."""
    label: str = ""
    value: str = ""
    uom: Optional[str] = ""
    provenance: Optional[FieldProvenance] = None


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
    # Field-level traceable provenance dictionary
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
