"""
Single Source of Truth for Pipeline Confidence Scoring, Field Weights, Penalties, and Review Routing.

Threshold Rationale:
--------------------
The default review threshold of 0.85 is a configurable demo threshold established for the
UniHack Simplifi MVP. In production, this threshold is calibrated against labelled ground truth
(e.g., the 200-row test evaluation dataset) via ROC/Precision-Recall curves to balance human
review workload against automated acceptance accuracy.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

# ============================================================================
# Core Component Weights (Sum = 1.0)
# ============================================================================
WEIGHT_IDENTITY: float = 0.25      # Brand & Manufacturer Master Resolution
WEIGHT_TAXONOMY: float = 0.25      # Classpath, Dept/Class/Fine, UNSPSC Classification
WEIGHT_ATTRIBUTES: float = 0.25    # LOV Attribute Density & Normalized Values
WEIGHT_EVIDENCE: float = 0.15      # Official Manufacturer Source Evidence Lineage
WEIGHT_DESCRIPTION: float = 0.10   # 5-Tier Character Limit & Formatting Compliance

COMPONENT_WEIGHTS: Dict[str, float] = {
    "identity": WEIGHT_IDENTITY,
    "taxonomy": WEIGHT_TAXONOMY,
    "attributes": WEIGHT_ATTRIBUTES,
    "evidence": WEIGHT_EVIDENCE,
    "description": WEIGHT_DESCRIPTION,
}

# ============================================================================
# Documented Confidence Penalties
# ============================================================================
PENALTY_MISSING_OFFICIAL_EVIDENCE: float = 0.15   # No registered official manufacturer URL or PDF
PENALTY_FALLBACK_TAXONOMY: float = 0.20          # Unclassified item defaulted to generic hardware UNSPSC 27110000
PENALTY_AMBIGUOUS_TAXONOMY: float = 0.15         # Top 2 classification candidates scored within close margin
PENALTY_UNRESOLVED_IDENTITY: float = 0.25        # Brand or Manufacturer could not be matched to master index
PENALTY_LOV_REJECTION: float = 0.10              # Per-attribute penalty when candidate fails category LOV
PENALTY_CONFLICTING_SOURCES: float = 0.20        # Supplier feed contradicts manufacturer evidence

CONFIDENCE_PENALTIES: Dict[str, float] = {
    "MISSING_OFFICIAL_EVIDENCE": PENALTY_MISSING_OFFICIAL_EVIDENCE,
    "FALLBACK_TAXONOMY": PENALTY_FALLBACK_TAXONOMY,
    "AMBIGUOUS_TAXONOMY": PENALTY_AMBIGUOUS_TAXONOMY,
    "UNRESOLVED_IDENTITY": PENALTY_UNRESOLVED_IDENTITY,
    "LOV_REJECTION": PENALTY_LOV_REJECTION,
    "CONFLICTING_SOURCES": PENALTY_CONFLICTING_SOURCES,
}

# ============================================================================
# Review Routing Threshold
# ============================================================================
# Configurable demo threshold for human review routing (calibrated against 200-row test dataset)
REVIEW_CONFIDENCE_THRESHOLD: float = 0.85


class FieldConfidenceBreakdown(BaseModel):
    """Granular explainability for a specific confidence dimension."""
    dimension_name: str
    weight: float
    raw_score: float
    penalties_applied: Dict[str, float] = Field(default_factory=dict)
    final_score: float
    explanation: str


class TransparentConfidenceSummary(BaseModel):
    """Product-level confidence summary aggregating all dimensions and penalties."""
    composite_confidence: float
    review_threshold: float = REVIEW_CONFIDENCE_THRESHOLD
    requires_human_review: bool
    review_routing_reasons: List[str] = Field(default_factory=list)
    dimension_breakdowns: Dict[str, FieldConfidenceBreakdown] = Field(default_factory=dict)
    active_penalties: Dict[str, float] = Field(default_factory=dict)
    weight_formula: str = "0.25*Identity + 0.25*Taxonomy + 0.25*Attributes + 0.15*Evidence + 0.10*Description - Penalties"
