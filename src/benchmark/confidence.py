"""
Multi-Factor Composite Confidence Scoring & Automated Anomaly Detection Engine.

Implements the 5-factor weighted confidence formulation:
C = 0.20 * C_brand + 0.20 * C_tax + 0.25 * C_attr + 0.20 * C_desc + 0.15 * C_comp

Includes:
- Anomaly Detector for triage and Human-in-the-Loop (HITL) review queue.
- Workflow status assignment: Validated (>= 0.95), Enriched (>= 0.85), Flagged / Needs Human Review (< 0.85).
"""

import re
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple, Union
import pandas as pd


# Weight distribution constant
CONFIDENCE_WEIGHTS = {
    "brand": 0.20,
    "taxonomy": 0.20,
    "attributes": 0.25,
    "descriptions": 0.20,
    "completeness": 0.15,
}

CONFIDENCE_THRESHOLD_VALIDATED = 0.95
CONFIDENCE_THRESHOLD_ENRICHED = 0.85


@dataclass
class ConfidenceBreakdown:
    """Detailed score breakdown across all 5 confidence dimensions."""
    brand_confidence: float
    taxonomy_confidence: float
    attribute_confidence: float
    description_compliance: float
    completeness: float
    composite_score: float

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class AnomalyFlag:
    """Individual anomaly flag triggered on a product record."""
    code: str
    severity: str  # "HIGH", "MEDIUM", "LOW"
    message: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass
class ProductConfidenceReport:
    """Confidence and anomaly triage report for a single catalog item."""
    row_id: Optional[Union[int, str]]
    mfg_part_num: str
    composite_score: float
    status: str  # "Validated", "Enriched", "Flagged" / "Needs Human Review"
    breakdown: ConfidenceBreakdown
    anomaly_flags: List[AnomalyFlag] = field(default_factory=list)
    needs_human_review: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "row_id": self.row_id,
            "mfg_part_num": self.mfg_part_num,
            "composite_score": self.composite_score,
            "status": self.status,
            "needs_human_review": self.needs_human_review,
            "breakdown": self.breakdown.to_dict(),
            "anomaly_flags": [f.to_dict() for f in self.anomaly_flags]
        }


# ===========================================================================
# 1. Individual Sub-Score Calculators
# ===========================================================================

class ConfidenceScorer:
    """Calculates the 5-factor composite confidence score for catalog products."""

    @classmethod
    def calculate_brand_confidence(
        cls,
        brand_name: Optional[str],
        manufacturer_name: Optional[str],
        raw_manuf: Optional[str] = None
    ) -> Tuple[float, List[AnomalyFlag]]:
        """Calculate C_brand (0.0 to 1.0)."""
        flags: List[AnomalyFlag] = []
        brand = str(brand_name).strip() if brand_name else ""
        mfr = str(manufacturer_name).strip() if manufacturer_name else ""

        if not brand or brand.lower() in ["-- unbranded --", "unbranded", "generic", "commodity - unbranded", "-", ""]:
            flags.append(AnomalyFlag(
                code="UNRESOLVED_BRAND",
                severity="HIGH",
                message="Brand is unbranded, generic, or unresolved placeholder"
            ))
            return 0.40, flags

        # Check for registered trademark or trade symbol
        has_symbol = ("®" in brand) or ("™" in brand)
        if has_symbol and mfr and mfr != "Industrial Supplies":
            return 1.0, flags
        elif has_symbol:
            return 0.95, flags
        elif mfr and mfr != "Industrial Supplies":
            return 0.85, flags
        else:
            flags.append(AnomalyFlag(
                code="UNVERIFIED_BRAND_SYMBOL",
                severity="LOW",
                message="Brand has no registered trademark symbol"
            ))
            return 0.75, flags

    @classmethod
    def calculate_taxonomy_confidence(
        cls,
        classpath: Optional[str],
        unspsc: Optional[str],
        product_name: Optional[str]
    ) -> Tuple[float, List[AnomalyFlag]]:
        """Calculate C_tax (0.0 to 1.0)."""
        flags: List[AnomalyFlag] = []
        cp = str(classpath).strip() if classpath else ""
        code = str(unspsc).strip() if unspsc else ""
        name = str(product_name).strip() if product_name else ""

        if not cp or not code:
            flags.append(AnomalyFlag(
                code="MISSING_TAXONOMY",
                severity="HIGH",
                message="Classpath or UNSPSC code is completely missing"
            ))
            return 0.30, flags

        if code == "27110000" or "General Hardware" in cp:
            flags.append(AnomalyFlag(
                code="FALLBACK_TAXONOMY",
                severity="MEDIUM",
                message="Product assigned fallback general UNSPSC (27110000)"
            ))
            return 0.70, flags

        # Check 3-tier hierarchy depth
        tiers = [t.strip() for t in cp.split(">") if t.strip()]
        if len(tiers) >= 3 and name:
            return 1.0, flags
        elif len(tiers) >= 2:
            return 0.85, flags
        else:
            return 0.75, flags

    @classmethod
    def calculate_attribute_confidence(
        cls,
        attributes: Union[List[Any], Dict[str, Any], int]
    ) -> Tuple[float, List[AnomalyFlag]]:
        """Calculate C_attr (0.0 to 1.0)."""
        flags: List[AnomalyFlag] = []
        
        if isinstance(attributes, int):
            valid_count = attributes
        elif isinstance(attributes, list):
            valid_count = 0
            for attr in attributes:
                val = getattr(attr, "value", None) if hasattr(attr, "value") else attr.get("value")
                lbl = getattr(attr, "label", None) if hasattr(attr, "label") else attr.get("label")
                if val and str(val).strip() and lbl and str(lbl).strip():
                    valid_count += 1
        elif isinstance(attributes, dict):
            valid_count = len([v for v in attributes.values() if v])
        else:
            valid_count = 0

        if valid_count >= 5:
            return 1.0, flags
        elif valid_count >= 3:
            return 0.95, flags
        elif valid_count == 2:
            return 0.90, flags
        elif valid_count == 1:
            flags.append(AnomalyFlag(
                code="LOW_ATTRIBUTE_DENSITY",
                severity="MEDIUM",
                message="Only 1 technical attribute could be extracted"
            ))
            return 0.80, flags
        else:
            flags.append(AnomalyFlag(
                code="ZERO_ATTRIBUTES_EXTRACTED",
                severity="HIGH",
                message="No technical attribute triplets were extracted"
            ))
            return 0.65, flags

    @classmethod
    def calculate_description_confidence(
        cls,
        invoice_desc: Optional[str],
        mobile_desc: Optional[str],
        short_desc: Optional[str] = None,
        long_desc1: Optional[str] = None
    ) -> Tuple[float, List[AnomalyFlag]]:
        """Calculate C_desc (0.0 to 1.0)."""
        flags: List[AnomalyFlag] = []
        score = 1.0

        inv = str(invoice_desc).strip() if invoice_desc else ""
        mob = str(mobile_desc).strip() if mobile_desc else ""

        # INVOICE_DESC verification
        if not inv:
            score -= 0.40
            flags.append(AnomalyFlag(
                code="MISSING_INVOICE_DESC",
                severity="HIGH",
                message="INVOICE_DESC is missing"
            ))
        else:
            if len(inv) > 40:
                score -= 0.30
                flags.append(AnomalyFlag(
                    code="INVOICE_DESC_LENGTH_OVERFLOW",
                    severity="HIGH",
                    message=f"INVOICE_DESC length {len(inv)} exceeds 40 characters"
                ))
            if any(c.islower() for c in inv):
                score -= 0.10
                flags.append(AnomalyFlag(
                    code="INVOICE_DESC_CASING_ERROR",
                    severity="MEDIUM",
                    message="INVOICE_DESC contains lowercase letters (must be ALL CAPS)"
                ))

        # MOBILE_DESC verification
        if not mob:
            score -= 0.30
            flags.append(AnomalyFlag(
                code="MISSING_MOBILE_DESC",
                severity="HIGH",
                message="MOBILE_DESC is missing"
            ))
        else:
            if len(mob) < 60 or len(mob) > 80:
                score -= 0.20
                flags.append(AnomalyFlag(
                    code="MOBILE_DESC_LENGTH_OUT_OF_BOUNDS",
                    severity="HIGH",
                    message=f"MOBILE_DESC length {len(mob)} outside 60-80 chars"
                ))

        # Secondary descriptions check
        if not short_desc:
            score -= 0.05
        if not long_desc1:
            score -= 0.05

        return max(0.0, min(1.0, score)), flags

    @classmethod
    def calculate_completeness(
        cls,
        record: Dict[str, Any]
    ) -> Tuple[float, List[AnomalyFlag]]:
        """Calculate C_comp (0.0 to 1.0) based on core delivery fields."""
        flags: List[AnomalyFlag] = []
        core_fields = [
            "Mfg_Part_Num",
            "MANUFACTURER_NAME",
            "BRAND_NAME",
            "Classpath",
            "Product Name",
            "UNSPSC",
            "INVOICE_DESC",
            "MOBILE_DESC",
            "SHORT_DESC",
            "LONG_DESC1"
        ]
        
        present = 0
        for f in core_fields:
            val = record.get(f) or record.get(f.lower()) or record.get(f.replace(" ", "_").lower())
            if val and str(val).strip():
                present += 1
            else:
                if f in ["Mfg_Part_Num", "INVOICE_DESC", "MOBILE_DESC"]:
                    flags.append(AnomalyFlag(
                        code=f"MISSING_CORE_FIELD_{f.upper()}",
                        severity="HIGH",
                        message=f"Core field '{f}' is empty"
                    ))

        completeness_ratio = present / len(core_fields)
        return round(completeness_ratio, 4), flags

    @classmethod
    def score_record(cls, record: Dict[str, Any]) -> ProductConfidenceReport:
        """
        Compute full composite confidence and anomaly triage for a catalog record.
        Uses C = 0.20 * C_brand + 0.20 * C_tax + 0.25 * C_attr + 0.20 * C_desc + 0.15 * C_comp
        """
        all_flags: List[AnomalyFlag] = []

        # Extract values across dict or object formats
        mfg_part_num = str(record.get("Mfg_Part_Num") or record.get("mfg_part_num") or record.get("mfg_part_number") or "").strip()
        brand_name = record.get("BRAND_NAME") or record.get("brand_name")
        mfr_name = record.get("MANUFACTURER_NAME") or record.get("manufacturer_name")
        raw_manuf = record.get("Part_Manuf") or record.get("part_manuf")
        classpath = record.get("Classpath") or record.get("classpath")
        unspsc = record.get("UNSPSC") or record.get("unspsc")
        product_name = record.get("Product Name") or record.get("product_name")
        inv_desc = record.get("INVOICE_DESC") or record.get("invoice_desc")
        mob_desc = record.get("MOBILE_DESC") or record.get("mobile_desc")
        short_desc = record.get("SHORT_DESC") or record.get("short_desc")
        long_desc1 = record.get("LONG_DESC1") or record.get("long_desc1")
        row_id = record.get("row_id") or record.get("PART_NUMBER") or record.get("part_number")

        # 1. Brand Confidence
        c_brand, brand_flags = cls.calculate_brand_confidence(brand_name, mfr_name, raw_manuf)
        all_flags.extend(brand_flags)

        # 2. Taxonomy Confidence
        c_tax, tax_flags = cls.calculate_taxonomy_confidence(classpath, unspsc, product_name)
        all_flags.extend(tax_flags)

        # 3. Attribute Confidence
        if "attributes" in record and isinstance(record["attributes"], list):
            attr_input = record["attributes"]
        else:
            # Count populated attribute slots in delivery dict
            attr_count = 0
            for i in range(1, 51):
                lbl = record.get(f"ATTRIBUTE_LABEL {i}")
                val = record.get(f"ATTRIBUTE_VALUE {i}")
                if lbl and val and str(lbl).strip() and str(val).strip():
                    attr_count += 1
            attr_input = attr_count
        c_attr, attr_flags = cls.calculate_attribute_confidence(attr_input)
        all_flags.extend(attr_flags)

        # 4. Description Confidence
        c_desc, desc_flags = cls.calculate_description_confidence(inv_desc, mob_desc, short_desc, long_desc1)
        all_flags.extend(desc_flags)

        # 5. Completeness
        c_comp, comp_flags = cls.calculate_completeness(record)
        all_flags.extend(comp_flags)

        # Composite formula: 0.20 * C_brand + 0.20 * C_tax + 0.25 * C_attr + 0.20 * C_desc + 0.15 * C_comp
        composite = (
            CONFIDENCE_WEIGHTS["brand"] * c_brand
            + CONFIDENCE_WEIGHTS["taxonomy"] * c_tax
            + CONFIDENCE_WEIGHTS["attributes"] * c_attr
            + CONFIDENCE_WEIGHTS["descriptions"] * c_desc
            + CONFIDENCE_WEIGHTS["completeness"] * c_comp
        )
        composite = round(composite, 4)

        # Low confidence anomaly trigger
        if composite < CONFIDENCE_THRESHOLD_ENRICHED:
            all_flags.append(AnomalyFlag(
                code="LOW_CONFIDENCE",
                severity="HIGH",
                message=f"Composite confidence {composite} is below 0.85 threshold"
            ))

        # Workflow status determination
        has_high_severity = any(f.severity == "HIGH" for f in all_flags)
        needs_human_review = (composite < CONFIDENCE_THRESHOLD_ENRICHED) or has_high_severity

        if composite >= CONFIDENCE_THRESHOLD_VALIDATED and not all_flags:
            status = "Validated"
        elif composite >= CONFIDENCE_THRESHOLD_ENRICHED and not has_high_severity:
            status = "Enriched"
        else:
            status = "Flagged"

        breakdown = ConfidenceBreakdown(
            brand_confidence=round(c_brand, 4),
            taxonomy_confidence=round(c_tax, 4),
            attribute_confidence=round(c_attr, 4),
            description_compliance=round(c_desc, 4),
            completeness=round(c_comp, 4),
            composite_score=composite
        )

        return ProductConfidenceReport(
            row_id=row_id,
            mfg_part_num=mfg_part_num,
            composite_score=composite,
            status=status,
            breakdown=breakdown,
            anomaly_flags=all_flags,
            needs_human_review=needs_human_review
        )


# ===========================================================================
# 2. Batch Confidence & Anomaly Summarizer
# ===========================================================================

@dataclass
class BatchConfidenceReport:
    """Aggregated confidence statistics and anomaly summary across an entire catalog."""
    total_evaluated: int
    mean_confidence: float
    median_confidence: float
    min_confidence: float
    max_confidence: float
    status_counts: Dict[str, int]
    needs_review_count: int
    needs_review_pct: float
    anomaly_code_counts: Dict[str, int]
    product_reports: List[ProductConfidenceReport] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_evaluated": self.total_evaluated,
            "mean_confidence": self.mean_confidence,
            "median_confidence": self.median_confidence,
            "min_confidence": self.min_confidence,
            "max_confidence": self.max_confidence,
            "status_counts": self.status_counts,
            "needs_review_count": self.needs_review_count,
            "needs_review_pct": self.needs_review_pct,
            "anomaly_code_counts": self.anomaly_code_counts
        }


def score_catalog_batch(
    records: Union[pd.DataFrame, List[Dict[str, Any]]]
) -> BatchConfidenceReport:
    """Evaluate confidence and detect anomalies for a batch of records."""
    if isinstance(records, pd.DataFrame):
        rows = records.to_dict(orient="records")
    else:
        rows = records

    reports: List[ProductConfidenceReport] = []
    status_counts = {"Validated": 0, "Enriched": 0, "Flagged": 0}
    anomaly_counts: Dict[str, int] = {}
    needs_review = 0
    scores = []

    for r in rows:
        rep = ConfidenceScorer.score_record(r)
        reports.append(rep)
        scores.append(rep.composite_score)
        status_counts[rep.status] = status_counts.get(rep.status, 0) + 1
        if rep.needs_human_review:
            needs_review += 1
        for flag in rep.anomaly_flags:
            anomaly_counts[flag.code] = anomaly_counts.get(flag.code, 0) + 1

    total = len(reports)
    if total > 0:
        scores.sort()
        mean_c = sum(scores) / total
        median_c = scores[total // 2] if total % 2 != 0 else (scores[total // 2 - 1] + scores[total // 2]) / 2.0
        min_c = min(scores)
        max_c = max(scores)
        review_pct = round((needs_review / total) * 100.0, 2)
    else:
        mean_c = median_c = min_c = max_c = review_pct = 0.0

    return BatchConfidenceReport(
        total_evaluated=total,
        mean_confidence=round(mean_c, 4),
        median_confidence=round(median_c, 4),
        min_confidence=round(min_c, 4),
        max_confidence=round(max_c, 4),
        status_counts=status_counts,
        needs_review_count=needs_review,
        needs_review_pct=review_pct,
        anomaly_code_counts=anomaly_counts,
        product_reports=reports
    )
