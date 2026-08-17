"""
Unit Test Suite for QA Benchmarking & Quality Assurance Suite (src/benchmark/).
"""

import pytest
import pandas as pd
from typing import Dict, Any, List

from src.benchmark.metrics import (
    exact_match,
    normalized_exact_match,
    levenshtein_distance,
    levenshtein_similarity,
    token_jaccard,
    token_cosine,
    sentence_bleu,
    bleu_1,
    bleu_2,
    bleu_4,
    rouge_n,
    rouge_l,
    evaluate_triplet_attributes,
    calculate_text_similarity_suite
)

from src.benchmark.hard_gates import (
    validate_invoice_desc,
    validate_invoice_desc_batch,
    validate_mobile_desc,
    validate_mobile_desc_batch,
    validate_lov_hallucinations,
    validate_schema_252,
    HardGateSuite,
    EXPECTED_252_COLUMNS
)

from src.benchmark.confidence import (
    ConfidenceScorer,
    score_catalog_batch,
    CONFIDENCE_WEIGHTS,
    CONFIDENCE_THRESHOLD_VALIDATED,
    CONFIDENCE_THRESHOLD_ENRICHED
)

from src.benchmark.evaluator import (
    CatalogEvaluator,
    BenchmarkReport
)

from src.benchmark.cli import run_benchmark_cli


# ===========================================================================
# 1. Metrics Module Unit Tests
# ===========================================================================

class TestMetricsModule:
    """Test suite for mathematical correctness of NLP and string metrics."""

    def test_exact_match(self):
        assert exact_match("DISHWASHER LEG 5 SST", "DISHWASHER LEG 5 SST") == 1.0
        assert exact_match("DISHWASHER", "Dishwasher") == 0.0
        assert exact_match("", "") == 1.0
        assert exact_match(None, "") == 1.0
        assert exact_match("ABC", "DEF") == 0.0

    def test_normalized_exact_match(self):
        assert normalized_exact_match("FRIGIDAIRE®", "frigidaire") == 1.0
        assert normalized_exact_match("  50.25   in  ", "50.25 in") == 1.0
        assert normalized_exact_match("“Smart” - Casing", "\"smart\" - casing") == 1.0
        assert normalized_exact_match("Brand A", "Brand B") == 0.0

    def test_levenshtein_distance_and_similarity(self):
        assert levenshtein_distance("kitten", "sitting") == 3
        assert levenshtein_distance("", "") == 0
        assert levenshtein_distance("test", "") == 4
        assert levenshtein_distance("DISHWASHER", "DISHWASHER") == 0

        # Similarity range [0, 1]
        sim_identical = levenshtein_similarity("PDSH4816AF", "PDSH4816AF")
        assert sim_identical == 1.0

        sim_partial = levenshtein_similarity("FRIGIDAIRE", "FRIGIDAIRE®")
        assert 0.85 <= sim_partial < 1.0

        sim_empty = levenshtein_similarity("", "")
        assert sim_empty == 1.0

        sim_disjoint = levenshtein_similarity("AAAA", "BBBB")
        assert sim_disjoint == 0.0

    def test_token_jaccard_and_cosine(self):
        s1 = "FRIGIDAIRE Dishwasher Stainless Steel 120V"
        s2 = "FRIGIDAIRE Professional Dishwasher Stainless Steel 120V"
        jacc = token_jaccard(s1, s2)
        assert 0.70 <= jacc <= 0.90

        assert token_jaccard("apple banana", "apple banana") == 1.0
        assert token_jaccard("apple banana", "orange cherry") == 0.0
        assert token_jaccard("", "") == 1.0

        cos = token_cosine(s1, s2)
        assert 0.80 <= cos <= 1.0
        assert token_cosine("apple", "banana") == 0.0

    def test_sentence_bleu_scores(self):
        ref = "FRIGIDAIRE Professional Series Dishwasher Stainless Steel 120V 15A"
        cand = "FRIGIDAIRE Professional Series Dishwasher Stainless Steel 120V 15A"
        
        # Identical candidate should yield 1.0
        assert bleu_1(ref, cand) == 1.0
        assert bleu_2(ref, cand) == 1.0
        assert bleu_4(ref, cand) == 1.0

        # Partial candidate
        partial = "FRIGIDAIRE Series Dishwasher Steel 120V"
        b1 = bleu_1(ref, partial)
        b4 = bleu_4(ref, partial)
        assert 0.50 <= b1 <= 1.0
        assert 0.0 <= b4 <= 1.0

        # Edge cases
        assert sentence_bleu("", "") == 1.0
        assert sentence_bleu("reference text", "") == 0.0

    def test_rouge_scores(self):
        ref = "FRIGIDAIRE Professional Series Dishwasher With CleanBoost"
        cand = "FRIGIDAIRE Professional Series Dishwasher With CleanBoost"

        r1 = rouge_n(ref, cand, n=1)
        r2 = rouge_n(ref, cand, n=2)
        rl = rouge_l(ref, cand)

        assert r1["f1"] == 1.0
        assert r2["f1"] == 1.0
        assert rl["f1"] == 1.0

        partial = "FRIGIDAIRE Dishwasher CleanBoost"
        rl_part = rouge_l(ref, partial)
        assert 0.50 <= rl_part["f1"] < 1.0
        assert rl_part["precision"] == 1.0  # all 3 tokens are in ref in order
        assert rl_part["recall"] < 1.0

    def test_triplet_attributes_evaluation(self):
        expected = [
            ("Mounting Type", "Leg", ""),
            ("Voltage Rating", "120", "V"),
            ("Amperage Rating", "15", "A"),
            ("Material", "Stainless Steel", "")
        ]
        predicted = [
            ("Mounting Type", "Leg", ""),
            ("Voltage Rating", "120", "V"),
            ("Amperage Rating", "15", "A"),
            ("Material", "Stainless Steel", "")
        ]

        res = evaluate_triplet_attributes(expected, predicted)
        assert res["f1"] == 1.0
        assert res["precision"] == 1.0
        assert res["recall"] == 1.0
        assert res["match_count"] == 4

        # Partial predicted
        pred_partial = [
            ("Mounting Type", "Leg", ""),
            ("Voltage Rating", "120", "V"),
            ("Color", "White", "")
        ]
        res_part = evaluate_triplet_attributes(expected, pred_partial)
        assert res_part["match_count"] == 2
        assert res_part["precision"] == pytest.approx(2 / 3, 0.001)
        assert res_part["recall"] == pytest.approx(2 / 4, 0.001)

    def test_calculate_text_similarity_suite(self):
        res = calculate_text_similarity_suite(
            "DISHWASHER LEG 5 SST 120V 15A",
            "DISHWASHER LEG 5 SST 120V 15A"
        )
        assert res["exact_match"] == 1.0
        assert res["normalized_match"] == 1.0
        assert res["levenshtein_similarity"] == 1.0
        assert res["token_jaccard"] == 1.0
        assert res["bleu_4"] == 1.0
        assert res["rouge_l_f1"] == 1.0


# ===========================================================================
# 2. Hard Gates Module Unit Tests
# ===========================================================================

class TestHardGatesModule:
    """Test suite for strict 100% hard rule compliance gates."""

    def test_validate_invoice_desc_valid(self):
        valid_desc = "DISHWASHER LEG 5 SST 120V 15A 50-1/4IN"
        is_val, reasons = validate_invoice_desc(valid_desc)
        assert is_val is True
        assert len(reasons) == 0
        assert len(valid_desc) <= 40

    def test_validate_invoice_desc_length_overflow(self):
        long_desc = "THIS INVOICE DESCRIPTION IS UNACCEPTABLY LONG AND EXCEEDS 40 CHARS"
        is_val, reasons = validate_invoice_desc(long_desc)
        assert is_val is False
        assert any("exceeds" in r.lower() for r in reasons)

    def test_validate_invoice_desc_lowercase_rejection(self):
        mixed_desc = "Dishwasher Leg 5 SST 120V"
        is_val, reasons = validate_invoice_desc(mixed_desc)
        assert is_val is False
        assert any("lowercase" in r.lower() for r in reasons)

    def test_validate_invoice_desc_batch(self):
        batch = [
            "DISHWASHER LEG 5 SST 120V 15A 50-1/4IN",
            "DISHWASHER BLTLN SST SST 120V 10A 41DBA",
            "SANDING BELT 1/2X18IN P80 6PK"
        ]
        res = validate_invoice_desc_batch(batch)
        assert res.passed is True
        assert res.compliance_rate == 1.0
        assert res.violation_count == 0

    def test_validate_mobile_desc_valid(self):
        valid_mob = "Rheem Manufacturing FRIGIDAIRE, Dishwasher, Professional Series, PDSH4816AF"
        assert 60 <= len(valid_mob) <= 80
        is_val, reasons = validate_mobile_desc(valid_mob)
        assert is_val is True
        assert len(reasons) == 0

    def test_validate_mobile_desc_out_of_bounds(self):
        too_short = "Short Title"
        is_val, reasons = validate_mobile_desc(too_short)
        assert is_val is False
        assert any("below" in r.lower() for r in reasons)

        too_long = "This is a ridiculously long mobile description that goes way beyond eighty characters in total length for mobile view"
        is_val, reasons = validate_mobile_desc(too_long)
        assert is_val is False
        assert any("exceeds" in r.lower() for r in reasons)

    def test_validate_mobile_desc_batch(self):
        batch = [
            "Rheem Manufacturing FRIGIDAIRE, Dishwasher, Professional Series, PDSH4816AF",
            "Whirlpool, Dishwasher, Eco Series, WDTS7024RZ, Built-in Mounting Check"
        ]
        res = validate_mobile_desc_batch(batch)
        assert res.passed is True
        assert res.compliance_rate == 1.0

    def test_validate_lov_hallucinations_zero_defects(self):
        valid_records = [
            {
                "ATTRIBUTE_LABEL 1": "Mounting Type",
                "ATTRIBUTE_VALUE 1": "Built-in",
                "ATTRIBUTE_UOM 1": "",
                "ATTRIBUTE_LABEL 2": "Material",
                "ATTRIBUTE_VALUE 2": "Stainless Steel",
                "ATTRIBUTE_UOM 2": "",
                "ATTRIBUTE_LABEL 3": "Voltage Rating",
                "ATTRIBUTE_VALUE 3": "120",
                "ATTRIBUTE_UOM 3": "V",
            }
        ]
        res = validate_lov_hallucinations(valid_records)
        assert res.passed is True
        assert res.violation_count == 0
        assert res.compliance_rate == 1.0

    def test_validate_lov_hallucinations_detects_fabrication(self):
        invalid_records = [
            {
                "ATTRIBUTE_LABEL 1": "Mounting Type",
                "ATTRIBUTE_VALUE 1": "Anti-Gravity Floating Mount",  # Hallucinated value
                "ATTRIBUTE_UOM 1": "",
            }
        ]
        res = validate_lov_hallucinations(invalid_records)
        assert res.passed is False
        assert res.violation_count == 1

    def test_validate_schema_252(self):
        # Exact headers
        res = validate_schema_252(EXPECTED_252_COLUMNS)
        assert res.passed is True
        assert res.compliance_rate == 1.0

        # Missing column
        broken_cols = EXPECTED_252_COLUMNS[:-1]
        res_broken = validate_schema_252(broken_cols)
        assert res_broken.passed is False

    def test_hard_gate_suite_full_run(self):
        df = pd.DataFrame([
            {
                "INVOICE_DESC": "DISHWASHER LEG 5 SST 120V 15A 50-1/4IN",
                "MOBILE_DESC": "Rheem Manufacturing FRIGIDAIRE, Dishwasher, Professional Series, PDSH4816AF",
                "ATTRIBUTE_LABEL 1": "Mounting Type",
                "ATTRIBUTE_VALUE 1": "Leg",
                "ATTRIBUTE_UOM 1": "",
                **{col: "" for col in EXPECTED_252_COLUMNS if col not in ["INVOICE_DESC", "MOBILE_DESC", "ATTRIBUTE_LABEL 1", "ATTRIBUTE_VALUE 1", "ATTRIBUTE_UOM 1"]}
            }
        ])
        # Reorder to exact 252 columns
        df = df[EXPECTED_252_COLUMNS]

        report = HardGateSuite.evaluate(df)
        assert report.all_passed is True
        assert report.total_gates == 4
        assert report.passed_gates_count == 4
        assert report.failed_gates_count == 0


# ===========================================================================
# 3. Confidence & Anomaly Detection Unit Tests
# ===========================================================================

class TestConfidenceModule:
    """Test suite for 5-factor composite confidence calculation and anomaly detection."""

    def test_composite_formula_weights(self):
        """Verify weights sum to 1.0."""
        total_w = sum(CONFIDENCE_WEIGHTS.values())
        assert round(total_w, 4) == 1.0
        assert CONFIDENCE_WEIGHTS["brand"] == 0.20
        assert CONFIDENCE_WEIGHTS["taxonomy"] == 0.20
        assert CONFIDENCE_WEIGHTS["attributes"] == 0.25
        assert CONFIDENCE_WEIGHTS["descriptions"] == 0.20
        assert CONFIDENCE_WEIGHTS["completeness"] == 0.15

    def test_high_confidence_product_scoring(self):
        record = {
            "Mfg_Part_Num": "PDSH4816AF",
            "MANUFACTURER_NAME": "Rheem Manufacturing",
            "BRAND_NAME": "FRIGIDAIRE®",
            "Classpath": "Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers",
            "Product Name": "Dishwasher",
            "UNSPSC": "52141505",
            "INVOICE_DESC": "DISHWASHER LEG 5 SST 120V 15A 50-1/4IN",
            "MOBILE_DESC": "Rheem Manufacturing FRIGIDAIRE, Dishwasher, Professional Series, PDSH4816AF",
            "SHORT_DESC": "FRIGIDAIRE® Professional Series PDSH4816AF Dishwasher",
            "LONG_DESC1": "FRIGIDAIRE® Dishwasher, Professional Series, 120 V, 15 A",
            "attributes": [
                {"label": "Series", "value": "Professional Series"},
                {"label": "Mounting Type", "value": "Leg"},
                {"label": "Voltage Rating", "value": "120"},
                {"label": "Amperage Rating", "value": "15"},
                {"label": "Material", "value": "Stainless Steel"},
            ]
        }

        report = ConfidenceScorer.score_record(record)
        assert report.composite_score >= 0.95
        assert report.status == "Validated"
        assert report.needs_human_review is False
        assert len(report.anomaly_flags) == 0

    def test_low_confidence_and_anomaly_detection(self):
        # Missing brand and invalid invoice desc
        bad_record = {
            "Mfg_Part_Num": "UNKNOWN-01",
            "MANUFACTURER_NAME": "Industrial Supplies",
            "BRAND_NAME": "-- Unbranded --",
            "Classpath": "General Hardware",
            "Product Name": "Hardware",
            "UNSPSC": "27110000",
            "INVOICE_DESC": "Invalid Lowercase Invoice Description That Is Far Too Long For Delivery",
            "MOBILE_DESC": "Too Short",
            "attributes": []
        }

        report = ConfidenceScorer.score_record(bad_record)
        assert report.composite_score < 0.85
        assert report.status == "Flagged"
        assert report.needs_human_review is True
        
        flag_codes = {f.code for f in report.anomaly_flags}
        assert "UNRESOLVED_BRAND" in flag_codes
        assert "FALLBACK_TAXONOMY" in flag_codes
        assert "LOW_CONFIDENCE" in flag_codes
        assert "INVOICE_DESC_LENGTH_OVERFLOW" in flag_codes

    def test_score_catalog_batch(self):
        records = [
            {
                "Mfg_Part_Num": f"ITEM-{i}",
                "MANUFACTURER_NAME": "Brand MFR",
                "BRAND_NAME": "Brand®",
                "Classpath": "A>B>C",
                "Product Name": "Product",
                "UNSPSC": "12345678",
                "INVOICE_DESC": "VALID INVOICE DESC 120V",
                "MOBILE_DESC": "Valid Mobile Description Length Between Sixty And Eighty Chars",
                "SHORT_DESC": "Short Desc",
                "LONG_DESC1": "Long Desc",
                "attributes": [{"label": "L", "value": "V"}] * 5
            }
            for i in range(10)
        ]
        batch_rep = score_catalog_batch(records)
        assert batch_rep.total_evaluated == 10
        assert batch_rep.mean_confidence >= 0.95
        assert batch_rep.status_counts["Validated"] == 10
        assert batch_rep.needs_review_count == 0


# ===========================================================================
# 4. Evaluator & CLI Unit Tests
# ===========================================================================

class TestEvaluatorAndCLI:
    """Test suite for full dataset evaluation against ground truth and CLI runner."""

    def test_evaluator_end_to_end(self, expected_output_path, project_root):
        evaluator = CatalogEvaluator(ground_truth_path=str(expected_output_path))
        
        # Evaluate ground truth against itself as baseline
        gt_df = pd.read_csv(expected_output_path)
        report = evaluator.evaluate_catalog(gt_df, gt_df)

        assert report.overall_exact_match_rate >= 0.90
        assert report.overall_levenshtein_similarity >= 0.95
        assert report.schema_column_count == 252
        assert report.hard_gates.all_passed is True

        # Test serializations
        d = report.to_dict()
        assert isinstance(d, dict)
        assert "overall_scores" in d

        j = report.to_json()
        assert isinstance(j, str)
        assert "overall_scores" in j

        md = report.to_markdown()
        assert isinstance(md, str)
        assert "# UniHack Industrial Product Intelligence: QA Benchmarking Report" in md

    def test_cli_runner_execution(self, expected_output_path, tmp_path):
        json_out = str(tmp_path / "test_report.json")
        md_out = str(tmp_path / "test_report.md")

        cli_args = [
            "-i", str(expected_output_path),
            "-g", str(expected_output_path),
            "-j", json_out,
            "-m", md_out,
            "--strict"
        ]

        exit_code = run_benchmark_cli(cli_args)
        assert exit_code == 0
        assert (tmp_path / "test_report.json").exists()
        assert (tmp_path / "test_report.md").exists()
