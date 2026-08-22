"""
Ground-Truth Benchmarking & Quality Assurance Evaluation Engine for UniHack PIM Catalog.

Evaluates enriched delivery format CSV against ground truth specification across all 252 columns:
1. Overall accuracy & per-column match rates across all 252 headers.
2. Comprehensive NLP & edit similarity for all 5 description tiers.
3. Hard gate verification (100% Invoice <=40 ALL CAPS, 100% Mobile 60-80, 0% LOV Hallucinations, 252 Columns).
4. Controlled Vocabulary (LOV) adherence & hallucination metrics.
5. Missing field rates & attribute triplet precision/recall/F1.
6. Multi-factor confidence distribution and anomaly detection summary.
"""

import os
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple, Union
import pandas as pd

from .metrics import (
    exact_match,
    normalized_exact_match,
    levenshtein_distance,
    levenshtein_similarity,
    token_jaccard,
    token_cosine,
    bleu_1,
    bleu_2,
    bleu_4,
    rouge_n,
    rouge_l,
    evaluate_triplet_attributes,
    calculate_text_similarity_suite
)
from .hard_gates import (
    HardGateSuite,
    HardGateSuiteReport,
    EXPECTED_252_COLUMNS
)
from .confidence import (
    ConfidenceScorer,
    score_catalog_batch,
    BatchConfidenceReport
)


@dataclass
class ColumnMetricResult:
    """Evaluation metrics for a single column across matched ground truth records."""
    column_name: str
    column_index: int
    exact_match_rate: Optional[float] = None
    normalized_match_rate: Optional[float] = None
    levenshtein_similarity: Optional[float] = None
    non_null_rate_enriched: float = 0.0
    non_null_rate_expected: Optional[float] = None
    sample_expected: str = ""
    sample_enriched: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DescriptionTierMetricResult:
    """Comprehensive NLP and structural metrics for a specific description tier."""
    tier_name: str
    exact_match_rate: Optional[float] = None
    normalized_match_rate: Optional[float] = None
    levenshtein_similarity: Optional[float] = None
    token_jaccard: Optional[float] = None
    token_cosine: Optional[float] = None
    bleu_1: Optional[float] = None
    bleu_2: Optional[float] = None
    bleu_4: Optional[float] = None
    rouge_1_f1: Optional[float] = None
    rouge_2_f1: Optional[float] = None
    rouge_l_f1: Optional[float] = None
    avg_length_enriched: float = 0.0
    avg_length_expected: Optional[float] = None
    length_compliance_rate: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BenchmarkReport:
    """Consolidated master benchmark evaluation report."""
    timestamp: str
    total_catalog_records: int
    total_ground_truth_records: int
    matched_benchmark_records: int
    schema_column_count: int
    overall_exact_match_rate: Optional[float]
    overall_normalized_match_rate: Optional[float]
    overall_levenshtein_similarity: Optional[float]
    overall_bleu_score: Optional[float]
    overall_rouge_l_f1: Optional[float]
    triplet_attribute_f1: Optional[float]
    hard_gates: HardGateSuiteReport
    confidence_summary: BatchConfidenceReport
    description_tier_metrics: Dict[str, DescriptionTierMetricResult]
    column_metrics: List[ColumnMetricResult]
    missing_fields_summary: Dict[str, float]
    is_ground_truth_calibrated: bool = False
    calibration_note: str = ""
    schema_compliance_rate: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "total_catalog_records": self.total_catalog_records,
            "total_ground_truth_records": self.total_ground_truth_records,
            "matched_benchmark_records": self.matched_benchmark_records,
            "schema_column_count": self.schema_column_count,
            "is_ground_truth_calibrated": self.is_ground_truth_calibrated,
            "calibration_note": self.calibration_note,
            "schema_compliance_rate": self.schema_compliance_rate,
            "overall_scores": {
                "exact_match_rate": self.overall_exact_match_rate,
                "normalized_match_rate": self.overall_normalized_match_rate,
                "average_levenshtein_similarity": self.overall_levenshtein_similarity,
                "average_bleu_score": self.overall_bleu_score,
                "average_rouge_l_f1": self.overall_rouge_l_f1,
                "triplet_attribute_f1": self.triplet_attribute_f1,
                "mean_confidence_score": self.confidence_summary.mean_confidence,
                "schema_compliance_rate": self.schema_compliance_rate,
            },
            "hard_rule_gates": self.hard_gates.to_dict(),
            "confidence_summary": self.confidence_summary.to_dict(),
            "description_tier_metrics": {k: v.to_dict() for k, v in self.description_tier_metrics.items()},
            "column_metrics": [c.to_dict() for c in self.column_metrics],
            "missing_fields_summary": self.missing_fields_summary
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_markdown(self) -> str:
        """Generate executive-ready Markdown benchmark summary."""
        def fmt_pct(val: Optional[float]) -> str:
            if val is None:
                return "N/A (Uncalibrated)"
            return f"{round(val * 100, 2)}%"

        lines = [
            "# UniHack Industrial Product Intelligence: QA Benchmarking Report",
            f"**Evaluation Timestamp**: {self.timestamp}  ",
            f"**Total Catalog Records**: {self.total_catalog_records} | **Ground Truth Records**: {self.total_ground_truth_records} | **Matched Records**: {self.matched_benchmark_records} | **Columns**: {self.schema_column_count}",
            f"**Calibration Status**: {'✅ CALIBRATED' if self.is_ground_truth_calibrated else '⚠️ NOT CALIBRATED'}",
            f"*{self.calibration_note}*",
            "",
            "## 1. Executive Summary & Overall Scores",
            "",
            "| Metric Dimension | Benchmark Score | Target Threshold | Status |",
            "|:---|:---|:---|:---|",
            f"| **Overall Exact Match Rate** | `{fmt_pct(self.overall_exact_match_rate)}` | $\\ge 85.0\\%$ | {'✅ PASS' if (self.overall_exact_match_rate or 0) >= 0.85 and self.is_ground_truth_calibrated else '⚠️ UNCALIBRATED' if not self.is_ground_truth_calibrated else '❌ FAIL'} |",
            f"| **Normalized Match Rate** | `{fmt_pct(self.overall_normalized_match_rate)}` | $\\ge 90.0\\%$ | {'✅ PASS' if (self.overall_normalized_match_rate or 0) >= 0.90 and self.is_ground_truth_calibrated else '⚠️ UNCALIBRATED' if not self.is_ground_truth_calibrated else '❌ FAIL'} |",
            f"| **Avg Levenshtein Similarity** | `{fmt_pct(self.overall_levenshtein_similarity)}` | $\\ge 90.0\\%$ | {'✅ PASS' if (self.overall_levenshtein_similarity or 0) >= 0.90 and self.is_ground_truth_calibrated else '⚠️ UNCALIBRATED' if not self.is_ground_truth_calibrated else '❌ FAIL'} |",
            f"| **Avg Description BLEU Score** | `{fmt_pct(self.overall_bleu_score)}` | $\\ge 80.0\\%$ | {'✅ PASS' if (self.overall_bleu_score or 0) >= 0.80 and self.is_ground_truth_calibrated else '⚠️ UNCALIBRATED' if not self.is_ground_truth_calibrated else '❌ FAIL'} |",
            f"| **Avg Description ROUGE-L F1** | `{fmt_pct(self.overall_rouge_l_f1)}` | $\\ge 85.0\\%$ | {'✅ PASS' if (self.overall_rouge_l_f1 or 0) >= 0.85 and self.is_ground_truth_calibrated else '⚠️ UNCALIBRATED' if not self.is_ground_truth_calibrated else '❌ FAIL'} |",
            f"| **Attribute Triplet F1 Score** | `{fmt_pct(self.triplet_attribute_f1)}` | $\\ge 90.0\\%$ | {'✅ PASS' if (self.triplet_attribute_f1 or 0) >= 0.90 and self.is_ground_truth_calibrated else '⚠️ UNCALIBRATED' if not self.is_ground_truth_calibrated else '❌ FAIL'} |",
            f"| **Mean Catalog Confidence** | `{round(self.confidence_summary.mean_confidence * 100, 2)}%` | $\\ge 85.0\\%$ | {'✅ PASS' if self.confidence_summary.mean_confidence >= 0.85 else '⚠️ REVIEW'} |",
            "",
            "## 2. Hard Rule Gates Compliance",
            "",
            "| Gate Name | Status | Compliance | Target | Evaluated | Violations |",
            "|:---|:---|:---|:---|:---|:---|",
        ]

        for g in self.hard_gates.summary_table:
            icon = "✅" if g["Status"] == "PASSED" else "❌"
            lines.append(f"| **{g['Gate']}** | {icon} {g['Status']} | `{g['Compliance']}` | {g['Target']} | {g['Evaluated']} | {g['Violations']} |")

        lines.extend([
            "",
            "## 3. 5-Tier Description Generation NLP Metrics",
            "",
            "| Description Tier | Exact Match | Normalized | Levenshtein | Jaccard | BLEU-4 | ROUGE-L F1 | Compliance |",
            "|:---|:---|:---|:---|:---|:---|:---|:---|",
        ])

        for tier, m in self.description_tier_metrics.items():
            lines.append(
                f"| **`{tier}`** | {fmt_pct(m.exact_match_rate)} | {fmt_pct(m.normalized_match_rate)} | "
                f"{fmt_pct(m.levenshtein_similarity)} | {fmt_pct(m.token_jaccard)} | "
                f"{fmt_pct(m.bleu_4)} | {fmt_pct(m.rouge_l_f1)} | {round(m.length_compliance_rate * 100, 1)}% |"
            )

        lines.extend([
            "",
            "## 4. Confidence Distribution & Anomaly Triage",
            "",
            f"- **Mean Confidence**: `{self.confidence_summary.mean_confidence}`",
            f"- **Median Confidence**: `{self.confidence_summary.median_confidence}`",
            f"- **Min / Max Confidence**: `{self.confidence_summary.min_confidence}` / `{self.confidence_summary.max_confidence}`",
            f"- **Workflow Status Counts**: `Validated: {self.confidence_summary.status_counts.get('Validated', 0)}` | `Enriched: {self.confidence_summary.status_counts.get('Enriched', 0)}` | `Flagged: {self.confidence_summary.status_counts.get('Flagged', 0)}`",
            f"- **Needs Human Review**: `{self.confidence_summary.needs_review_count}` items (`{self.confidence_summary.needs_review_pct}%`)",
            "",
            "### Anomaly Code Breakdown:",
        ])

        if self.confidence_summary.anomaly_code_counts:
            for code, cnt in sorted(self.confidence_summary.anomaly_code_counts.items(), key=lambda x: -x[1]):
                lines.append(f"- **`{code}`**: {cnt} occurrences")
        else:
            lines.append("- *No anomalies detected across catalog.*")

        lines.extend([
            "",
            "## 5. Top Evaluated Delivery Schema Columns",
            "",
            "| # | Column Header | Exact Match | Normalized Match | Levenshtein Sim | Enriched Populated | Expected Populated |",
            "|:---|:---|:---|:---|:---|:---|:---|",
        ])

        prominent_cols = [
            "MANUFACTURER_NAME", "BRAND_NAME", "TRADE_NAME", "MANUFACTURER_PART_NUMBER",
            "Classpath", "Product Name", "UNSPSC", "INVOICE_DESC", "MOBILE_DESC",
            "SHORT_DESC", "LONG_DESC1", "RETAIL_DESC", "MARKETING_DESCRIPTION",
            "ATTRIBUTE_LABEL 1", "ATTRIBUTE_VALUE 1", "ATTRIBUTE_UOM 1",
            "ATTRIBUTE_LABEL 4", "ATTRIBUTE_VALUE 4", "ATTRIBUTE_UOM 4",
            "ATTRIBUTE_LABEL 5", "ATTRIBUTE_VALUE 5", "ATTRIBUTE_UOM 5",
            "Product Image", "Specification Sheet", "Actual Image (Yes/No)"
        ]

        col_dict = {c.column_name: c for c in self.column_metrics}
        for idx, col_name in enumerate(prominent_cols, 1):
            if col_name in col_dict:
                cm = col_dict[col_name]
                exp_pop_str = f"{round(cm.non_null_rate_expected * 100, 1)}%" if cm.non_null_rate_expected is not None else "N/A"
                lines.append(
                    f"| {idx} | `{col_name}` | {fmt_pct(cm.exact_match_rate)} | "
                    f"{fmt_pct(cm.normalized_match_rate)} | {fmt_pct(cm.levenshtein_similarity)} | "
                    f"{round(cm.non_null_rate_enriched * 100, 1)}% | {exp_pop_str} |"
                )

        return "\n".join(lines)


# ===========================================================================
# 2. Master Catalog & Ground-Truth Evaluator
# ===========================================================================

class CatalogEvaluator:
    """Comprehensive evaluation engine comparing enriched catalog against ground truth."""

    def __init__(self, ground_truth_path: Optional[str] = None):
        if not ground_truth_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            ground_truth_path = os.path.join(base_dir, "Unihack_ Expected Output - Delivery Format.csv")
            if not os.path.exists(ground_truth_path):
                ground_truth_path = os.path.join(base_dir, "data", "ground_truth", "Unihack_ Expected Output - Delivery Format.csv")

        self.ground_truth_path = ground_truth_path
        self.gt_df = None
        if ground_truth_path and os.path.exists(ground_truth_path):
            self.gt_df = pd.read_csv(ground_truth_path)

    def evaluate_catalog(
        self,
        enriched_input: Union[str, pd.DataFrame, List[Dict[str, Any]]],
        ground_truth_input: Optional[Union[str, pd.DataFrame]] = None
    ) -> BenchmarkReport:
        """Execute complete ground-truth benchmark and QA analysis on the catalog dataset."""
        # 1. Load Enriched Catalog
        if isinstance(enriched_input, str):
            enriched_df = pd.read_csv(enriched_input)
        elif isinstance(enriched_input, pd.DataFrame):
            enriched_df = enriched_input
        else:
            enriched_df = pd.DataFrame(enriched_input)

        # 2. Load Ground Truth
        if ground_truth_input is not None:
            if isinstance(ground_truth_input, str):
                gt_df = pd.read_csv(ground_truth_input)
            else:
                gt_df = ground_truth_input
        elif self.gt_df is not None:
            gt_df = self.gt_df
        else:
            gt_df = pd.DataFrame()

        # 3. Evaluate Hard Gates
        hard_gate_report = HardGateSuite.evaluate(enriched_df)

        # 4. Evaluate Batch Confidence & Anomaly Detection
        confidence_report = score_catalog_batch(enriched_df)

        # 5. Match Enriched Records to Ground Truth
        matched_pairs = self._match_records(enriched_df, gt_df)

        # 6. Compute Per-Column Metrics across matched benchmark records
        col_metrics, overall_em, overall_nem, overall_lev = self._evaluate_column_metrics(matched_pairs, enriched_df)

        # 7. Compute Description Tier NLP Metrics
        desc_metrics, avg_bleu, avg_rouge = self._evaluate_description_tiers(matched_pairs, enriched_df)

        # 8. Compute Triplet Attribute Precision / Recall / F1
        triplet_f1 = self._evaluate_triplets(matched_pairs)

        # 9. Compute Missing Field Rates across all 252 headers
        missing_fields = self._compute_missing_rates(enriched_df)

        timestamp_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        is_calibrated = len(matched_pairs) > 0 and len(gt_df) > 0
        calib_note = (
            f"Ground-truth benchmark evaluated against {len(matched_pairs)} matched reference records."
            if is_calibrated
            else "Not calibrated: no matched labelled ground truth. Exact match scoring requires ground truth records with matching MPNs."
        )

        return BenchmarkReport(
            timestamp=timestamp_str,
            total_catalog_records=len(enriched_df),
            total_ground_truth_records=len(gt_df),
            matched_benchmark_records=len(matched_pairs),
            schema_column_count=len(enriched_df.columns),
            overall_exact_match_rate=round(overall_em, 4) if overall_em is not None else None,
            overall_normalized_match_rate=round(overall_nem, 4) if overall_nem is not None else None,
            overall_levenshtein_similarity=round(overall_lev, 4) if overall_lev is not None else None,
            overall_bleu_score=round(avg_bleu, 4) if avg_bleu is not None else None,
            overall_rouge_l_f1=round(avg_rouge, 4) if avg_rouge is not None else None,
            triplet_attribute_f1=round(triplet_f1, 4) if triplet_f1 is not None else None,
            hard_gates=hard_gate_report,
            confidence_summary=confidence_report,
            description_tier_metrics=desc_metrics,
            column_metrics=col_metrics,
            missing_fields_summary=missing_fields,
            is_ground_truth_calibrated=is_calibrated,
            calibration_note=calib_note,
            schema_compliance_rate=1.0 if hard_gate_report.all_passed else round(hard_gate_report.passed_gates_count / max(1, hard_gate_report.total_gates), 4)
        )

    def _match_records(
        self,
        enriched_df: pd.DataFrame,
        gt_df: pd.DataFrame
    ) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """Pair enriched records with ground-truth records strictly by reliable identifiers (MPN/SKU/Part Number)."""
        pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
        if gt_df is None or len(gt_df) == 0 or len(enriched_df) == 0:
            return pairs

        gt_records = gt_df.to_dict(orient="records")
        enr_records = enriched_df.to_dict(orient="records")

        # Index GT by reliable unique identifiers
        gt_by_key = {}
        for r in gt_records:
            for k in ("MANUFACTURER_PART_NUMBER", "Mfg_Part_Num", "PART_NUMBER", "SKU - MY_PART_NUMBER", "SKU"):
                val = str(r.get(k) or "").strip().upper()
                if val:
                    gt_by_key[val] = r

        # Match from enriched records
        seen_gt_ids = set()
        for r in enr_records:
            matched_gt = None
            for k in ("MANUFACTURER_PART_NUMBER", "Mfg_Part_Num", "PART_NUMBER", "SKU - MY_PART_NUMBER", "SKU"):
                val = str(r.get(k) or "").strip().upper()
                if val and val in gt_by_key:
                    matched_gt = gt_by_key[val]
                    break
            if matched_gt is not None:
                gt_id = id(matched_gt)
                if gt_id not in seen_gt_ids:
                    pairs.append((r, matched_gt))
                    seen_gt_ids.add(gt_id)

        return pairs

    def _evaluate_column_metrics(
        self,
        matched_pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]],
        enriched_df: pd.DataFrame
    ) -> Tuple[List[ColumnMetricResult], Optional[float], Optional[float], Optional[float]]:
        """Evaluate match rates for all 252 columns across matched records."""
        col_results: List[ColumnMetricResult] = []
        headers = EXPECTED_252_COLUMNS
        total_enr_rows = max(1, len(enriched_df))

        if not matched_pairs:
            # When uncalibrated: return real enriched non-null rates, but match rates as None
            for idx, col in enumerate(headers, 1):
                enr_non_null = 0
                sample_enr = ""
                if col in enriched_df.columns:
                    non_null_series = enriched_df[col].dropna()
                    enr_non_null = int((non_null_series.astype(str).str.strip() != "").sum())
                    if not non_null_series.empty:
                        sample_enr = str(non_null_series.iloc[0])[:60]

                col_results.append(
                    ColumnMetricResult(
                        column_name=col,
                        column_index=idx,
                        exact_match_rate=None,
                        normalized_match_rate=None,
                        levenshtein_similarity=None,
                        non_null_rate_enriched=round(enr_non_null / total_enr_rows, 4),
                        non_null_rate_expected=None,
                        sample_expected="",
                        sample_enriched=sample_enr
                    )
                )
            return col_results, None, None, None

        total_pairs = len(matched_pairs)
        em_list = []
        nem_list = []
        lev_list = []

        for col_idx, col_name in enumerate(headers, 1):
            em_count = 0
            nem_count = 0
            lev_sum = 0.0
            enr_non_null = 0
            gt_non_null = 0
            sample_exp = ""
            sample_enr = ""

            for enr_row, gt_row in matched_pairs:
                val_enr = enr_row.get(col_name)
                val_gt = gt_row.get(col_name)

                str_enr = str(val_enr).strip() if pd.notna(val_enr) and val_enr is not None else ""
                str_gt = str(val_gt).strip() if pd.notna(val_gt) and val_gt is not None else ""

                if str_enr:
                    enr_non_null += 1
                if str_gt:
                    gt_non_null += 1

                if not sample_exp and str_gt:
                    sample_exp = str_gt[:60]
                if not sample_enr and str_enr:
                    sample_enr = str_enr[:60]

                em = exact_match(str_gt, str_enr)
                nem = normalized_exact_match(str_gt, str_enr)
                lev = levenshtein_similarity(str_gt, str_enr)

                em_count += em
                nem_count += nem
                lev_sum += lev

            col_em = em_count / total_pairs
            col_nem = nem_count / total_pairs
            col_lev = lev_sum / total_pairs

            em_list.append(col_em)
            nem_list.append(col_nem)
            lev_list.append(col_lev)

            col_results.append(
                ColumnMetricResult(
                    column_name=col_name,
                    column_index=col_idx,
                    exact_match_rate=round(col_em, 4),
                    normalized_match_rate=round(col_nem, 4),
                    levenshtein_similarity=round(col_lev, 4),
                    non_null_rate_enriched=round(enr_non_null / total_pairs, 4),
                    non_null_rate_expected=round(gt_non_null / total_pairs, 4),
                    sample_expected=sample_exp,
                    sample_enriched=sample_enr
                )
            )

        mean_em = sum(em_list) / len(em_list) if em_list else None
        mean_nem = sum(nem_list) / len(nem_list) if nem_list else None
        mean_lev = sum(lev_list) / len(lev_list) if lev_list else None

        return col_results, mean_em, mean_nem, mean_lev

    def _evaluate_description_tiers(
        self,
        matched_pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]],
        enriched_df: pd.DataFrame
    ) -> Tuple[Dict[str, DescriptionTierMetricResult], Optional[float], Optional[float]]:
        """Compute NLP metrics across all description tiers."""
        tiers = [
            "INVOICE_DESC",
            "MOBILE_DESC",
            "SHORT_DESC",
            "LONG_DESC1",
            "RETAIL_DESC",
            "MARKETING_DESCRIPTION"
        ]

        tier_results: Dict[str, DescriptionTierMetricResult] = {}
        all_bleus = []
        all_rouges = []
        total_enr = max(1, len(enriched_df))

        for tier in tiers:
            if not matched_pairs:
                # Compute actual length and compliance from enriched dataframe without hallucinating match scores
                enr_series = enriched_df[tier].dropna().astype(str).str.strip() if tier in enriched_df.columns else pd.Series([], dtype=str)
                avg_len = float(enr_series.str.len().mean()) if not enr_series.empty else 0.0

                compliance_count = 0
                for val in enr_series:
                    if tier == "INVOICE_DESC":
                        if len(val) <= 40 and val.isupper():
                            compliance_count += 1
                    elif tier == "MOBILE_DESC":
                        if 60 <= len(val) <= 80:
                            compliance_count += 1
                    else:
                        compliance_count += 1

                tier_results[tier] = DescriptionTierMetricResult(
                    tier_name=tier,
                    exact_match_rate=None,
                    normalized_match_rate=None,
                    levenshtein_similarity=None,
                    token_jaccard=None,
                    token_cosine=None,
                    bleu_1=None,
                    bleu_2=None,
                    bleu_4=None,
                    rouge_1_f1=None,
                    rouge_2_f1=None,
                    rouge_l_f1=None,
                    avg_length_enriched=round(avg_len, 1),
                    avg_length_expected=None,
                    length_compliance_rate=round(compliance_count / max(1, len(enr_series)), 4)
                )
                continue

            em_sum = nem_sum = lev_sum = jacc_sum = cos_sum = 0.0
            b1_sum = b2_sum = b4_sum = r1_sum = r2_sum = rl_sum = 0.0
            enr_len_sum = gt_len_sum = 0
            compliance_count = 0
            total = len(matched_pairs)

            for enr_row, gt_row in matched_pairs:
                val_enr = enr_row.get(tier)
                val_gt = gt_row.get(tier)

                str_enr = str(val_enr).strip() if pd.notna(val_enr) and val_enr is not None else ""
                str_gt = str(val_gt).strip() if pd.notna(val_gt) and val_gt is not None else ""

                enr_len_sum += len(str_enr)
                gt_len_sum += len(str_gt)

                # Length compliance check
                if tier == "INVOICE_DESC":
                    if len(str_enr) <= 40 and str_enr.isupper():
                        compliance_count += 1
                elif tier == "MOBILE_DESC":
                    if 60 <= len(str_enr) <= 80:
                        compliance_count += 1
                else:
                    compliance_count += 1

                em_sum += exact_match(str_gt, str_enr)
                nem_sum += normalized_exact_match(str_gt, str_enr)
                lev_sum += levenshtein_similarity(str_gt, str_enr)
                jacc_sum += token_jaccard(str_gt, str_enr)
                cos_sum += token_cosine(str_gt, str_enr)
                b1_sum += bleu_1(str_gt, str_enr)
                b2_sum += bleu_2(str_gt, str_enr)
                b4_sum += bleu_4(str_gt, str_enr)
                r1_sum += rouge_n(str_gt, str_enr, n=1)["f1"]
                r2_sum += rouge_n(str_gt, str_enr, n=2)["f1"]
                rl_sum += rouge_l(str_gt, str_enr)["f1"]

            b4_avg = b4_sum / total
            rl_avg = rl_sum / total
            all_bleus.append(b4_avg)
            all_rouges.append(rl_avg)

            tier_results[tier] = DescriptionTierMetricResult(
                tier_name=tier,
                exact_match_rate=round(em_sum / total, 4),
                normalized_match_rate=round(nem_sum / total, 4),
                levenshtein_similarity=round(lev_sum / total, 4),
                token_jaccard=round(jacc_sum / total, 4),
                token_cosine=round(cos_sum / total, 4),
                bleu_1=round(b1_sum / total, 4),
                bleu_2=round(b2_sum / total, 4),
                bleu_4=round(b4_avg, 4),
                rouge_1_f1=round(r1_sum / total, 4),
                rouge_2_f1=round(r2_sum / total, 4),
                rouge_l_f1=round(rl_avg, 4),
                avg_length_enriched=round(enr_len_sum / total, 1),
                avg_length_expected=round(gt_len_sum / total, 1),
                length_compliance_rate=round(compliance_count / total, 4)
            )

        mean_bleu = sum(all_bleus) / len(all_bleus) if all_bleus else None
        mean_rouge = sum(all_rouges) / len(all_rouges) if all_rouges else None

        return tier_results, mean_bleu, mean_rouge

    def _evaluate_triplets(
        self,
        matched_pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]]
    ) -> Optional[float]:
        """Calculate average triplet attribute F1 score across matched ground-truth records."""
        if not matched_pairs:
            return None

        f1_list = []
        for enr_row, gt_row in matched_pairs:
            exp_triplets = []
            pred_triplets = []
            for i in range(1, 51):
                # Expected
                l_exp = str(gt_row.get(f"ATTRIBUTE_LABEL {i}", "")).strip() if pd.notna(gt_row.get(f"ATTRIBUTE_LABEL {i}")) else ""
                v_exp = str(gt_row.get(f"ATTRIBUTE_VALUE {i}", "")).strip() if pd.notna(gt_row.get(f"ATTRIBUTE_VALUE {i}")) else ""
                u_exp = str(gt_row.get(f"ATTRIBUTE_UOM {i}", "")).strip() if pd.notna(gt_row.get(f"ATTRIBUTE_UOM {i}")) else ""
                if l_exp and v_exp:
                    exp_triplets.append((l_exp, v_exp, u_exp))

                # Predicted
                l_enr = str(enr_row.get(f"ATTRIBUTE_LABEL {i}", "")).strip() if pd.notna(enr_row.get(f"ATTRIBUTE_LABEL {i}")) else ""
                v_enr = str(enr_row.get(f"ATTRIBUTE_VALUE {i}", "")).strip() if pd.notna(enr_row.get(f"ATTRIBUTE_VALUE {i}")) else ""
                u_enr = str(enr_row.get(f"ATTRIBUTE_UOM {i}", "")).strip() if pd.notna(enr_row.get(f"ATTRIBUTE_UOM {i}")) else ""
                if l_enr and v_enr:
                    pred_triplets.append((l_enr, v_enr, u_enr))

            res = evaluate_triplet_attributes(exp_triplets, pred_triplets)
            f1_list.append(res["f1"])

        return sum(f1_list) / len(f1_list) if f1_list else None

    def _compute_missing_rates(self, df: pd.DataFrame) -> Dict[str, float]:
        """Compute percentage of empty / null values per column."""
        missing = {}
        total = len(df)
        if total == 0:
            return missing

        for col in EXPECTED_252_COLUMNS:
            if col in df.columns:
                series = df[col]
                null_cnt = series.isna().sum() + (series.astype(str).str.strip() == "").sum()
                missing[col] = round(float(null_cnt) / total, 4)
            else:
                missing[col] = 1.0

        return missing
