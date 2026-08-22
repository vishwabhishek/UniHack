"""
Product Lifecycle State Machine & Approval Policy Engine.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Set
from enum import Enum


class ProductLifecycleState(str, Enum):
    RAW = "raw"
    ENRICHED = "enriched"
    REVIEW_REQUIRED = "review_required"
    VALIDATED = "validated"
    REJECTED = "rejected"
    EXPORTED = "exported"


# Permissible State Transitions
VALID_TRANSITIONS: Dict[ProductLifecycleState, Set[ProductLifecycleState]] = {
    ProductLifecycleState.RAW: {ProductLifecycleState.ENRICHED, ProductLifecycleState.REVIEW_REQUIRED, ProductLifecycleState.REJECTED},
    ProductLifecycleState.ENRICHED: {ProductLifecycleState.REVIEW_REQUIRED, ProductLifecycleState.VALIDATED, ProductLifecycleState.REJECTED},
    ProductLifecycleState.REVIEW_REQUIRED: {ProductLifecycleState.VALIDATED, ProductLifecycleState.REJECTED, ProductLifecycleState.ENRICHED},
    ProductLifecycleState.VALIDATED: {ProductLifecycleState.EXPORTED, ProductLifecycleState.REVIEW_REQUIRED, ProductLifecycleState.REJECTED},
    ProductLifecycleState.REJECTED: {ProductLifecycleState.REVIEW_REQUIRED, ProductLifecycleState.RAW},
    ProductLifecycleState.EXPORTED: {ProductLifecycleState.REVIEW_REQUIRED},
}

HIGH_RISK_FIELDS: List[str] = [
    "mfg_part_number",
    "brand_name",
    "manufacturer_name",
    "classpath",
    "unspsc",
    "invoice_desc",
    "short_desc"
]


class ProductLifecycleValidator:
    """Enforces strict state transitions and approval preconditions."""

    @staticmethod
    def can_transition(current_state: str, target_state: str) -> Tuple[bool, Optional[str]]:
        try:
            curr = ProductLifecycleState(current_state.lower())
            tgt = ProductLifecycleState(target_state.lower())
        except ValueError:
            return False, f"Invalid lifecycle state: '{current_state}' -> '{target_state}'"

        allowed = VALID_TRANSITIONS.get(curr, set())
        if tgt not in allowed:
            return False, f"Illegal state transition from '{curr.value}' to '{tgt.value}'. Permitted: {[s.value for s in allowed]}"

        return True, None

    @staticmethod
    def check_approval_preconditions(
        product_dict: Dict,
        field_records: Optional[List[Dict]] = None
    ) -> Tuple[bool, List[str]]:
        """
        Product cannot become 'validated' if high-risk fields have:
        missing evidence, data conflict, rejected status, unresolved identity, or low confidence.
        """
        blocking_reasons: List[str] = []

        # 1. Product Confidence Gate
        conf = product_dict.get("confidence", 0.0)
        if conf < 0.85:
            blocking_reasons.append(f"Overall product confidence ({conf:.2f}) is below approval threshold (0.85).")

        # 2. Data Conflicts Check
        conflicts = product_dict.get("data_conflicts", [])
        if conflicts:
            blocking_reasons.append(f"Product has {len(conflicts)} active unresolved data conflict(s): {', '.join(conflicts[:2])}")

        # 3. High-Risk Fields Integrity
        for hr_field in HIGH_RISK_FIELDS:
            val = product_dict.get(hr_field)
            if not val or val == "--" or str(val).strip() == "":
                blocking_reasons.append(f"High-risk field '{hr_field}' is unresolved or empty.")

        # 4. Field Evidence Verification
        if field_records:
            for f in field_records:
                fname = f.get("field_name", "")
                fstatus = f.get("status", "")
                if fname in HIGH_RISK_FIELDS and fstatus in ("rejected", "missing_evidence"):
                    blocking_reasons.append(f"High-risk attribute '{fname}' has status '{fstatus}'.")

        is_approved = len(blocking_reasons) == 0
        return is_approved, blocking_reasons


lifecycle_validator = ProductLifecycleValidator()
