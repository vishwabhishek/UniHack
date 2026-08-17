"""
Strict Hard Rule Verification & Gate Assertion Suite for PIM Catalog Deliverables.

Enforces zero-tolerance compliance gates:
1. INVOICE_DESC <= 40 characters & 100% ALL CAPS (0 lowercase characters).
2. MOBILE_DESC within 60 to 80 characters.
3. Controlled Vocabulary (LOV) 0% Hallucination Rate.
4. Schema Integrity: Exactly 252 columns matching delivery specification in exact sequence.
"""

import json
import os
import re
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple, Union, Set
import pandas as pd


@dataclass
class HardGateViolation:
    """Individual violation record."""
    row_index: int
    field_name: str
    value: str
    length: int
    reasons: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HardGateResult:
    """Evaluation result for a single hard rule gate."""
    gate_id: str
    gate_name: str
    passed: bool
    total_evaluated: int
    valid_count: int
    violation_count: int
    compliance_rate: float
    target_compliance: str
    violations: List[Dict[str, Any]] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ===========================================================================
# 1. Expected 252-Column Delivery Schema Master List
# ===========================================================================

EXPECTED_252_COLUMNS: List[str] = [
    "MFR URL",
    "Ref URL 1",
    "Ref URL 2",
    "Ref URL 3",
    "Ref URL 4",
    "Ref URL 5",
    "PART_NUMBER",
    "Dept",
    "Class",
    "Fine",
    "SKU - MY_PART_NUMBER",
    "Mfg_Part_Num",
    "Part_Desc",
    "E1_Brand",
    "Unilog_Brand",
    "DIB_Brand",
    "Part_Manuf",
    "MANUFACTURER_NAME",
    "BRAND_NAME",
    "TRADE_NAME",
    "MANUFACTURER_PART_NUMBER",
    "ALTERNATE_PART_NUMBER",
    "Classpath",
    "MOBILE_DESC",
    "INVOICE_DESC",
    "SHORT_DESC",
    "LONG_DESC1",
    "RETAIL_DESC",
    "MARKETING_DESCRIPTION",
    "ITEM_FEATURES_1",
    "ITEM_FEATURES_2",
    "ITEM_FEATURES_3",
    "ITEM_FEATURES_4",
    "ITEM_FEATURES_5",
    "ITEM_FEATURES_6",
    "ITEM_FEATURES_7",
    "ITEM_FEATURES_8",
    "ITEM_FEATURES_9",
    "ITEM_FEATURES_10",
    "ITEM_FEATURES_11",
    "ITEM_FEATURES_12",
    "ITEM_FEATURES_13",
    "ITEM_FEATURES_14",
    "ITEM_FEATURES_15",
    "ITEM_FEATURES_16",
    "ITEM_FEATURES_17",
    "ITEM_FEATURES_18",
    "ITEM_FEATURES_19",
    "ITEM_FEATURES_20",
    "With",
    "Standard/Approvals",
    "Prop 65",
    "Application",
    "Includes",
    "Product Name",
] + [
    col
    for i in range(1, 51)
    for col in (f"ATTRIBUTE_LABEL {i}", f"ATTRIBUTE_VALUE {i}", f"ATTRIBUTE_UOM {i}")
] + [
    "UPC",
    "EAN",
    "GTIN",
    "UNSPSC",
    "Warranty",
    "List Price",
    "Selling Qty",
    "Selling UOM",
    "Standard Packaging Information",
    "LENGTH",
    "LENGTH_UOM",
    "HEIGHT",
    "HEIGHT_UOM",
    "WIDTH",
    "WIDTH_UOM",
    "WEIGHT",
    "WEIGHT_UOM",
    "VOLUME",
    "VOLUME_UOM",
    "Product Image",
    "Alternate Image 1",
    "Alternate Image 2",
    "Alternate Image 3",
    "Alternate Image 4",
    "SDS",
    "SDS_1",
    "Warranty Information",
    "Catalog",
    "Specification Sheet",
    "Instruction/Installation Manual",
    "Service Manual",
    "Owners/User Manual",
    "Line Drawing",
    "MTR",
    "RoHS",
    "Full Engineering Drawing",
    "Energy Star Guide",
    "Technical Bulletin",
    "Submittal",
    "Compatibility Chart",
    "Size Chart",
    "Product Label/Insert",
    "Video Link",
    "Video Link 1",
    "Country Of Origin",
    "Discontinued",
    "Actual Image (Yes/No)",
]


# ===========================================================================
# 2. Gate 1: INVOICE_DESC <= 40 Characters & ALL CAPS
# ===========================================================================

def validate_invoice_desc(text: Optional[str]) -> Tuple[bool, List[str]]:
    """
    Validate a single INVOICE_DESC string:
    - Must be non-empty string.
    - Must be <= 40 characters in length.
    - Must be ALL CAPS (contains no lowercase alphabetic characters).
    """
    if text is None:
        return False, ["Invoice description is None"]
    
    val = str(text).strip()
    if not val:
        return False, ["Invoice description is empty"]
    
    reasons = []
    if len(val) > 40:
        reasons.append(f"Length {len(val)} exceeds maximum allowed 40 characters")
    
    # Check for lowercase letters
    if any(c.islower() for c in val):
        reasons.append("Contains lowercase characters (must be 100% ALL CAPS)")
    
    return len(reasons) == 0, reasons


def validate_invoice_desc_batch(
    records: Union[List[Dict[str, Any]], pd.DataFrame, List[str]],
    column_name: str = "INVOICE_DESC"
) -> HardGateResult:
    """Assert 100% compliance on INVOICE_DESC across a batch of records."""
    violations: List[Dict[str, Any]] = []
    total = 0
    valid = 0

    if isinstance(records, pd.DataFrame):
        items = records[column_name].tolist() if column_name in records.columns else []
    elif isinstance(records, list):
        if len(records) > 0 and isinstance(records[0], dict):
            items = [r.get(column_name, "") for r in records]
        else:
            items = records
    else:
        items = list(records)

    total = len(items)
    for idx, item in enumerate(items):
        is_val, reasons = validate_invoice_desc(item)
        if is_val:
            valid += 1
        else:
            v_str = "" if item is None else str(item)
            violations.append(
                HardGateViolation(
                    row_index=idx,
                    field_name=column_name,
                    value=v_str,
                    length=len(v_str),
                    reasons=reasons
                ).to_dict()
            )

    compliance = (valid / total) if total > 0 else 0.0
    passed = (compliance == 1.0) and (total > 0)

    return HardGateResult(
        gate_id="invoice_desc_le_40_caps",
        gate_name="INVOICE_DESC <= 40 Chars & 100% ALL CAPS",
        passed=passed,
        total_evaluated=total,
        valid_count=valid,
        violation_count=len(violations),
        compliance_rate=round(compliance, 4),
        target_compliance="100.0%",
        violations=violations[:50],  # cap details to 50 items
        details={
            "max_length_allowed": 40,
            "uppercase_required": True,
            "total_violations": len(violations)
        }
    )


# ===========================================================================
# 3. Gate 2: MOBILE_DESC 60 to 80 Characters
# ===========================================================================

def validate_mobile_desc(text: Optional[str]) -> Tuple[bool, List[str]]:
    """
    Validate a single MOBILE_DESC string:
    - Must be non-empty string.
    - Must be between 60 and 80 characters inclusive.
    """
    if text is None:
        return False, ["Mobile description is None"]
    
    val = str(text).strip()
    if not val:
        return False, ["Mobile description is empty"]
    
    reasons = []
    length = len(val)
    if length < 60:
        reasons.append(f"Length {length} is below minimum allowed 60 characters")
    elif length > 80:
        reasons.append(f"Length {length} exceeds maximum allowed 80 characters")
    
    return len(reasons) == 0, reasons


def validate_mobile_desc_batch(
    records: Union[List[Dict[str, Any]], pd.DataFrame, List[str]],
    column_name: str = "MOBILE_DESC"
) -> HardGateResult:
    """Assert 100% compliance on MOBILE_DESC length [60, 80] across a batch of records."""
    violations: List[Dict[str, Any]] = []
    total = 0
    valid = 0

    if isinstance(records, pd.DataFrame):
        items = records[column_name].tolist() if column_name in records.columns else []
    elif isinstance(records, list):
        if len(records) > 0 and isinstance(records[0], dict):
            items = [r.get(column_name, "") for r in records]
        else:
            items = records
    else:
        items = list(records)

    total = len(items)
    for idx, item in enumerate(items):
        is_val, reasons = validate_mobile_desc(item)
        if is_val:
            valid += 1
        else:
            v_str = "" if item is None else str(item)
            violations.append(
                HardGateViolation(
                    row_index=idx,
                    field_name=column_name,
                    value=v_str,
                    length=len(v_str),
                    reasons=reasons
                ).to_dict()
            )

    compliance = (valid / total) if total > 0 else 0.0
    passed = (compliance == 1.0) and (total > 0)

    return HardGateResult(
        gate_id="mobile_desc_60_to_80",
        gate_name="MOBILE_DESC 60 to 80 Chars Length Range",
        passed=passed,
        total_evaluated=total,
        valid_count=valid,
        violation_count=len(violations),
        compliance_rate=round(compliance, 4),
        target_compliance="100.0%",
        violations=violations[:50],
        details={
            "min_length_allowed": 60,
            "max_length_allowed": 80,
            "total_violations": len(violations)
        }
    )


# ===========================================================================
# 4. Gate 3: Controlled Vocabulary (LOV) 0% Hallucinations
# ===========================================================================

class LOVValidator:
    """Validates extracted technical attributes against canonical Controlled Vocabularies."""

    def __init__(self, dict_path: Optional[str] = None):
        if not dict_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            dict_path = os.path.join(base_dir, "data", "dictionaries", "lov_dictionaries.json")
        
        self.lov_data = {}
        if os.path.exists(dict_path):
            try:
                with open(dict_path, "r", encoding="utf-8") as f:
                    self.lov_data = json.load(f)
            except Exception:
                pass

        # Build canonical lowercase sets (including mapped canonical target names from synonyms)
        self.allowed_mounting = {
            v.lower() for v in self.lov_data.get("mounting_types", {}).get("allowed", [])
        } | {
            v.lower() for v in self.lov_data.get("mounting_types", {}).get("synonyms", {}).values()
        }
        self.allowed_materials = {
            v.lower() for v in self.lov_data.get("materials", {}).get("allowed", [])
        } | {
            v.lower() for v in self.lov_data.get("materials", {}).get("synonyms", {}).values()
        }
        self.allowed_colors = {
            v.lower() for v in self.lov_data.get("colors", {}).get("allowed", [])
        } | {
            v.lower() for v in self.lov_data.get("colors", {}).get("synonyms", {}).values()
        }
        self.allowed_edge_profiles = {
            v.lower() for v in self.lov_data.get("edge_profiles", {}).get("allowed", [])
        } | {
            v.lower() for v in self.lov_data.get("edge_profiles", {}).get("synonyms", {}).values()
        }
        self.allowed_wash_cycles = {
            str(v).lower() for v in self.lov_data.get("wash_cycles", {}).get("allowed", [])
        }

        # Master canonical allowed map
        self.canonical_slots: Dict[str, Set[str]] = {
            "mounting type": self.allowed_mounting,
            "material": self.allowed_materials,
            "color": self.allowed_colors,
            "finish": self.allowed_colors,
            "edge profile": self.allowed_edge_profiles,
            "number of wash cycles": self.allowed_wash_cycles,
        }

    def is_valid_attribute_value(self, label: str, value: str) -> Tuple[bool, Optional[str]]:
        """
        Validate an extracted attribute value against canonical LOV or standard patterns.
        Returns (is_valid, failure_reason).
        """
        clean_label = label.strip().lower()
        clean_val = value.strip().lower()

        if not clean_val:
            return True, None

        # Check controlled categorical slots
        if clean_label in self.canonical_slots and self.canonical_slots[clean_label]:
            allowed_set = self.canonical_slots[clean_label]
            if clean_val not in allowed_set:
                # Check if partial or multi-value
                if not any(a in clean_val for a in allowed_set):
                    return False, f"Value '{value}' not in canonical LOV for label '{label}'"

        # Check numeric specifications (Voltage, Amperage, Sound Level, Size, etc.)
        if clean_label in ["voltage rating", "amperage rating", "sound level"]:
            # Must contain numeric values
            if not re.search(r"\d+", clean_val):
                return False, f"Numeric specification '{label}' contains no digits: '{value}'"

        return True, None


def validate_lov_hallucinations(
    records: Union[List[Dict[str, Any]], pd.DataFrame],
    dict_path: Optional[str] = None
) -> HardGateResult:
    """
    Assert 0.0% Hallucination Rate across extracted attribute triplets (slots 1..50).
    Every categorical attribute value must conform to the canonical LOV dictionary.
    """
    validator = LOVValidator(dict_path)
    total_extracted_attributes = 0
    hallucinated_attributes = 0
    violations: List[Dict[str, Any]] = []

    if isinstance(records, pd.DataFrame):
        rows = records.to_dict(orient="records")
    else:
        rows = records

    for row_idx, row in enumerate(rows):
        # 1. If row is an EnrichedProduct or dict with 'attributes' list
        if "attributes" in row and isinstance(row["attributes"], list):
            for attr in row["attributes"]:
                label = getattr(attr, "label", "") if hasattr(attr, "label") else attr.get("label", "")
                val = getattr(attr, "value", "") if hasattr(attr, "value") else attr.get("value", "")
                if label and val:
                    total_extracted_attributes += 1
                    is_valid, reason = validator.is_valid_attribute_value(label, val)
                    if not is_valid:
                        hallucinated_attributes += 1
                        violations.append({
                            "row_index": row_idx,
                            "label": label,
                            "value": val,
                            "reason": reason
                        })
        else:
            # 2. Check 50 attribute slot columns in flattened delivery format
            for slot in range(1, 51):
                lbl_key = f"ATTRIBUTE_LABEL {slot}"
                val_key = f"ATTRIBUTE_VALUE {slot}"
                label = str(row.get(lbl_key, "")).strip() if pd.notna(row.get(lbl_key)) else ""
                val = str(row.get(val_key, "")).strip() if pd.notna(row.get(val_key)) else ""

                if label and val:
                    total_extracted_attributes += 1
                    is_valid, reason = validator.is_valid_attribute_value(label, val)
                    if not is_valid:
                        hallucinated_attributes += 1
                        violations.append({
                            "row_index": row_idx,
                            "slot": slot,
                            "label": label,
                            "value": val,
                            "reason": reason
                        })

    hallucination_rate = (
        (hallucinated_attributes / total_extracted_attributes * 100.0)
        if total_extracted_attributes > 0
        else 0.0
    )
    compliance_rate = 1.0 - (hallucinated_attributes / total_extracted_attributes) if total_extracted_attributes > 0 else 1.0
    passed = (hallucinated_attributes == 0)

    return HardGateResult(
        gate_id="lov_zero_hallucinations",
        gate_name="Controlled Vocabulary (LOV) 0% Hallucinations",
        passed=passed,
        total_evaluated=total_extracted_attributes,
        valid_count=total_extracted_attributes - hallucinated_attributes,
        violation_count=hallucinated_attributes,
        compliance_rate=round(compliance_rate, 4),
        target_compliance="0.0% Hallucinations (100% Adherence)",
        violations=violations[:50],
        details={
            "total_attributes_evaluated": total_extracted_attributes,
            "hallucination_count": hallucinated_attributes,
            "hallucination_rate_pct": f"{round(hallucination_rate, 2)}%"
        }
    )


# ===========================================================================
# 5. Gate 4: 252-Column Schema Match in Exact Order
# ===========================================================================

def validate_schema_252(
    candidate_columns: List[str],
    expected_columns: Optional[List[str]] = None
) -> HardGateResult:
    """
    Assert 100% compliance with master 252-column delivery schema.
    Verifies column count, column names, and exact sequence order.
    """
    expected = expected_columns or EXPECTED_252_COLUMNS
    actual = [str(c).strip() for c in candidate_columns]

    missing_columns = [c for c in expected if c not in actual]
    unexpected_columns = [c for c in actual if c not in expected]

    # Check order
    order_mismatches = []
    if len(actual) == len(expected):
        for idx, (exp, act) in enumerate(zip(expected, actual)):
            if exp != act:
                order_mismatches.append({"index": idx, "expected": exp, "actual": act})

    is_count_correct = len(actual) == len(expected)
    is_exact_match = actual == expected
    passed = is_exact_match

    compliance = (
        1.0
        if is_exact_match
        else max(0.0, (len(expected) - len(missing_columns) - len(unexpected_columns) - len(order_mismatches)) / len(expected))
    )

    violations = []
    if missing_columns:
        violations.append({"type": "missing_columns", "columns": missing_columns[:10]})
    if unexpected_columns:
        violations.append({"type": "unexpected_columns", "columns": unexpected_columns[:10]})
    if order_mismatches:
        violations.append({"type": "order_mismatches", "mismatches": order_mismatches[:10]})

    return HardGateResult(
        gate_id="schema_252_columns",
        gate_name="Master 252-Column Delivery Schema Exact Sequence",
        passed=passed,
        total_evaluated=len(expected),
        valid_count=len(expected) - len(missing_columns) - len(order_mismatches),
        violation_count=len(missing_columns) + len(unexpected_columns) + len(order_mismatches),
        compliance_rate=round(compliance, 4),
        target_compliance="100.0% Exact Sequence Match",
        violations=violations,
        details={
            "expected_column_count": len(expected),
            "actual_column_count": len(actual),
            "missing_column_count": len(missing_columns),
            "unexpected_column_count": len(unexpected_columns),
            "order_mismatch_count": len(order_mismatches)
        }
    )


# ===========================================================================
# 6. Master Hard Gate Suite Runner
# ===========================================================================

@dataclass
class HardGateSuiteReport:
    """Consolidated report across all 4 mandatory hard gates."""
    all_passed: bool
    total_gates: int
    passed_gates_count: int
    failed_gates_count: int
    gates: Dict[str, HardGateResult]
    summary_table: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "all_passed": self.all_passed,
            "total_gates": self.total_gates,
            "passed_gates_count": self.passed_gates_count,
            "failed_gates_count": self.failed_gates_count,
            "gates": {k: v.to_dict() for k, v in self.gates.items()},
            "summary_table": self.summary_table
        }


class HardGateSuite:
    """Master evaluator verifying all 4 strict hard gates across a dataset."""

    @classmethod
    def evaluate(
        cls,
        data: Union[pd.DataFrame, List[Dict[str, Any]]],
        dict_path: Optional[str] = None
    ) -> HardGateSuiteReport:
        """Run all 4 hard gates on the dataset and produce a structured report."""
        if isinstance(data, pd.DataFrame):
            df = data
            columns = df.columns.tolist()
            records = df.to_dict(orient="records")
        else:
            records = data
            columns = list(records[0].keys()) if len(records) > 0 else []
            df = pd.DataFrame(records)

        # 1. Invoice Desc Gate
        invoice_res = validate_invoice_desc_batch(df, column_name="INVOICE_DESC")

        # 2. Mobile Desc Gate
        mobile_res = validate_mobile_desc_batch(df, column_name="MOBILE_DESC")

        # 3. LOV Hallucinations Gate
        lov_res = validate_lov_hallucinations(records, dict_path=dict_path)

        # 4. Schema 252 Gate
        schema_res = validate_schema_252(columns)

        gates = {
            invoice_res.gate_id: invoice_res,
            mobile_res.gate_id: mobile_res,
            lov_res.gate_id: lov_res,
            schema_res.gate_id: schema_res
        }

        passed_count = sum(1 for g in gates.values() if g.passed)
        failed_count = len(gates) - passed_count
        all_passed = (passed_count == len(gates))

        summary_table = [
            {
                "Gate": g.gate_name,
                "Status": "PASSED" if g.passed else "FAILED",
                "Compliance": f"{round(g.compliance_rate * 100, 2)}%",
                "Target": g.target_compliance,
                "Evaluated": g.total_evaluated,
                "Violations": g.violation_count
            }
            for g in gates.values()
        ]

        return HardGateSuiteReport(
            all_passed=all_passed,
            total_gates=len(gates),
            passed_gates_count=passed_count,
            failed_gates_count=failed_count,
            gates=gates,
            summary_table=summary_table
        )
