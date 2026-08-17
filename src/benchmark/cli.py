"""
Command-Line Interface for the UniHack Ground-Truth Benchmarking & Quality Assurance Suite.
"""

import os
import sys
import argparse
import time
from typing import Optional

from .evaluator import CatalogEvaluator


def print_banner():
    print("=" * 80)
    print("  UniHack Industrial Product Intelligence & PIM Enrichment")
    print("  Ground-Truth Benchmarking & Quality Assurance Suite")
    print("=" * 80)


def print_table(headers: list, rows: list, title: Optional[str] = None):
    """Print a clean ASCII table."""
    if title:
        print(f"\n--- {title} ---")

    widths = [len(str(h)) for h in headers]
    for row in rows:
        for idx, val in enumerate(row):
            widths[idx] = max(widths[idx], len(str(val)))

    header_line = " | ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers))
    sep_line = "-+-".join("-" * widths[i] for i in range(len(headers)))

    print(header_line)
    print(sep_line)
    for row in rows:
        row_line = " | ".join(str(val).ljust(widths[i]) for i, val in enumerate(row))
        print(row_line)


def run_benchmark_cli(args: Optional[list] = None) -> int:
    """Execute benchmarking from CLI arguments."""
    parser = argparse.ArgumentParser(
        description="UniHack PIM Catalog Ground-Truth Benchmarking & QA Suite"
    )
    parser.add_argument(
        "-i", "--enriched", "--input",
        dest="enriched",
        default="data/output/enriched_catalog_252_columns.csv",
        help="Path to generated 252-column enriched CSV file"
    )
    parser.add_argument(
        "-g", "--ground-truth", "--expected",
        dest="ground_truth",
        default="Unihack_ Expected Output - Delivery Format.csv",
        help="Path to 252-column ground truth delivery template CSV"
    )
    parser.add_argument(
        "-j", "--output-json",
        dest="output_json",
        default="data/output/benchmark_report.json",
        help="Destination path for structured JSON benchmark report"
    )
    parser.add_argument(
        "-m", "--output-md",
        dest="output_md",
        default="data/output/benchmark_report.md",
        help="Destination path for Markdown benchmark summary report"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail with non-zero exit code if any hard rule gate fails"
    )

    parsed = parser.parse_args(args)

    print_banner()
    print(f"[*] Enriched Catalog Path:    {parsed.enriched}")
    print(f"[*] Ground Truth Path:        {parsed.ground_truth}")
    print(f"[*] Output JSON Report Path:  {parsed.output_json}")
    print(f"[*] Output Markdown Report:   {parsed.output_md}")

    # Check enriched file exists
    if not os.path.exists(parsed.enriched):
        print(f"\n[ERROR] Enriched catalog file not found: {parsed.enriched}")
        print("Please run the enrichment pipeline first via scripts/run_pipeline.py.")
        return 1

    # Check fallback for ground truth if default not found in cwd
    gt_path = parsed.ground_truth
    if not os.path.exists(gt_path):
        alt_gt = os.path.join("data", "ground_truth", "Unihack_ Expected Output - Delivery Format.csv")
        if os.path.exists(alt_gt):
            gt_path = alt_gt

    print("\n[*] Starting evaluation...")
    start_time = time.time()

    evaluator = CatalogEvaluator(ground_truth_path=gt_path)
    report = evaluator.evaluate_catalog(
        enriched_input=parsed.enriched,
        ground_truth_input=gt_path if os.path.exists(gt_path) else None
    )

    elapsed = time.time() - start_time
    print(f"[+] Evaluation completed in {round(elapsed, 2)} seconds.")

    # 1. Print Overall Score Summary Table
    overall_headers = ["Metric Dimension", "Score", "Target Threshold", "Status"]
    overall_rows = [
        [
            "Overall Exact Match Rate",
            f"{round(report.overall_exact_match_rate * 100, 2)}%",
            ">= 85.0%",
            "PASS" if report.overall_exact_match_rate >= 0.85 else "WARN"
        ],
        [
            "Normalized Match Rate",
            f"{round(report.overall_normalized_match_rate * 100, 2)}%",
            ">= 90.0%",
            "PASS" if report.overall_normalized_match_rate >= 0.90 else "WARN"
        ],
        [
            "Levenshtein Similarity",
            f"{round(report.overall_levenshtein_similarity * 100, 2)}%",
            ">= 90.0%",
            "PASS" if report.overall_levenshtein_similarity >= 0.90 else "WARN"
        ],
        [
            "Average Description BLEU-4",
            f"{round(report.overall_bleu_score * 100, 2)}%",
            ">= 80.0%",
            "PASS" if report.overall_bleu_score >= 0.80 else "WARN"
        ],
        [
            "Average Description ROUGE-L F1",
            f"{round(report.overall_rouge_l_f1 * 100, 2)}%",
            ">= 85.0%",
            "PASS" if report.overall_rouge_l_f1 >= 0.85 else "WARN"
        ],
        [
            "Attribute Triplet F1 Score",
            f"{round(report.triplet_attribute_f1 * 100, 2)}%",
            ">= 90.0%",
            "PASS" if report.triplet_attribute_f1 >= 0.90 else "WARN"
        ],
        [
            "Mean Confidence Score",
            f"{round(report.confidence_summary.mean_confidence * 100, 2)}%",
            ">= 85.0%",
            "PASS" if report.confidence_summary.mean_confidence >= 0.85 else "WARN"
        ],
    ]
    print_table(overall_headers, overall_rows, title="Overall Benchmark Scores")

    # 2. Print Hard Rule Gates Table
    gate_headers = ["Hard Rule Gate", "Status", "Compliance", "Target", "Violations"]
    gate_rows = [
        [
            g["Gate"],
            g["Status"],
            g["Compliance"],
            g["Target"],
            str(g["Violations"])
        ]
        for g in report.hard_gates.summary_table
    ]
    print_table(gate_headers, gate_rows, title="Mandatory Hard Rule Gates")

    # 3. Print 5-Tier Description Metrics Table
    desc_headers = ["Description Tier", "Exact Match", "Norm Match", "Levenshtein", "BLEU-4", "ROUGE-L F1", "Compliance"]
    desc_rows = [
        [
            tier,
            f"{round(m.exact_match_rate * 100, 1)}%",
            f"{round(m.normalized_match_rate * 100, 1)}%",
            f"{round(m.levenshtein_similarity * 100, 1)}%",
            f"{round(m.bleu_4 * 100, 1)}%",
            f"{round(m.rouge_l_f1 * 100, 1)}%",
            f"{round(m.length_compliance_rate * 100, 1)}%"
        ]
        for tier, m in report.description_tier_metrics.items()
    ]
    print_table(desc_headers, desc_rows, title="5-Tier Description Generation Quality")

    # 4. Save JSON Report
    if parsed.output_json:
        os.makedirs(os.path.dirname(os.path.abspath(parsed.output_json)), exist_ok=True)
        with open(parsed.output_json, "w", encoding="utf-8") as f:
            f.write(report.to_json(indent=2))
        print(f"\n[+] Saved JSON benchmark report -> {parsed.output_json}")

    # 5. Save Markdown Report
    if parsed.output_md:
        os.makedirs(os.path.dirname(os.path.abspath(parsed.output_md)), exist_ok=True)
        with open(parsed.output_md, "w", encoding="utf-8") as f:
            f.write(report.to_markdown())
        print(f"[+] Saved Markdown benchmark report -> {parsed.output_md}")

    # Exit code
    if parsed.strict and not report.hard_gates.all_passed:
        print("\n[FAILED] Strict gate validation failed. Review violations above.")
        return 1

    print("\n[SUCCESS] Benchmark suite completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(run_benchmark_cli())
