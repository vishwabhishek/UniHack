"""
Unit tests for honest benchmark evaluation and uncalibrated metrics handling.
"""

import pandas as pd
from src.benchmark.evaluator import CatalogEvaluator


def test_benchmark_returns_none_for_zero_matched_ground_truth():
    """Verify that when ground truth has 0 matching records, metric scores are returned as None (not 1.0 or 100%)."""
    evaluator = CatalogEvaluator(ground_truth_path="non_existent_file.csv")

    # Sample enriched dataframe with distinct MPNs
    dummy_df = pd.DataFrame([{
        "MANUFACTURER_PART_NUMBER": "NON_MATCHING_MPN_9999",
        "INVOICE_DESC": "VALVE BALL 1/2 IN BRASS",
        "MOBILE_DESC": "SharkBite 1/2 in Brass Ball Valve for PEX Plumbing",
        "SHORT_DESC": "SharkBite 1/2 in Brass Ball Valve",
        "LONG_DESC1": "SharkBite 1/2 in Brass Ball Valve 200 psi",
        "RETAIL_DESC": "SharkBite 1/2 in Brass Ball Valve",
        "MARKETING_DESCRIPTION": "Premium brass ball valve",
        "ATTRIBUTE_LABEL 1": "Size",
        "ATTRIBUTE_VALUE 1": "1/2 in",
        "ATTRIBUTE_UOM 1": "in"
    }])

    empty_gt = pd.DataFrame([{
        "MANUFACTURER_PART_NUMBER": "DIFFERENT_MPN_1111",
        "INVOICE_DESC": "OTHER DESC",
    }])

    report = evaluator.evaluate_catalog(enriched_input=dummy_df, ground_truth_input=empty_gt)

    assert report.matched_benchmark_records == 0
    assert report.is_ground_truth_calibrated is False
    assert "Not calibrated" in report.calibration_note
    assert report.overall_exact_match_rate is None
    assert report.overall_normalized_match_rate is None
    assert report.overall_levenshtein_similarity is None
    assert report.overall_bleu_score is None
    assert report.overall_rouge_l_f1 is None
    assert report.triplet_attribute_f1 is None

    # Check markdown serialization
    md = report.to_markdown()
    assert "N/A (Uncalibrated)" in md
    assert "NOT CALIBRATED" in md
