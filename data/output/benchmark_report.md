# UniHack Industrial Product Intelligence: QA Benchmarking Report
**Evaluation Timestamp**: 2026-08-22T06:40:17Z  
**Total Catalog Records**: 1000 | **Ground Truth Records**: 2 | **Matched Records**: 2 | **Columns**: 252
**Calibration Status**: ✅ CALIBRATED
*Ground-truth benchmark evaluated against 2 matched reference records.*

## 1. Executive Summary & Overall Scores

| Metric Dimension | Benchmark Score | Target Threshold | Status |
|:---|:---|:---|:---|
| **Overall Exact Match Rate** | `83.73%` | $\ge 85.0\%$ | ❌ FAIL |
| **Normalized Match Rate** | `83.73%` | $\ge 90.0\%$ | ❌ FAIL |
| **Avg Levenshtein Similarity** | `85.0%` | $\ge 90.0\%$ | ❌ FAIL |
| **Avg Description BLEU Score** | `27.15%` | $\ge 80.0\%$ | ❌ FAIL |
| **Avg Description ROUGE-L F1** | `51.7%` | $\ge 85.0\%$ | ❌ FAIL |
| **Attribute Triplet F1 Score** | `34.77%` | $\ge 90.0\%$ | ❌ FAIL |
| **Mean Catalog Confidence** | `97.91%` | $\ge 85.0\%$ | ✅ PASS |

## 2. Hard Rule Gates Compliance

| Gate Name | Status | Compliance | Target | Evaluated | Violations |
|:---|:---|:---|:---|:---|:---|
| **INVOICE_DESC <= 40 Chars & 100% ALL CAPS** | ✅ PASSED | `100.0%` | 100.0% | 1000 | 0 |
| **MOBILE_DESC 60 to 80 Chars Length Range** | ✅ PASSED | `100.0%` | 100.0% | 1000 | 0 |
| **Controlled Vocabulary (LOV) 0% Hallucinations** | ✅ PASSED | `100.0%` | 0.0% Hallucinations (100% Adherence) | 1861 | 0 |
| **Master 252-Column Delivery Schema Exact Sequence** | ✅ PASSED | `100.0%` | 100.0% Exact Sequence Match | 252 | 0 |

## 3. 5-Tier Description Generation NLP Metrics

| Description Tier | Exact Match | Normalized | Levenshtein | Jaccard | BLEU-4 | ROUGE-L F1 | Compliance |
|:---|:---|:---|:---|:---|:---|:---|:---|
| **`INVOICE_DESC`** | 0.0% | 0.0% | 42.81% | 30.95% | 11.97% | 50.0% | 100.0% |
| **`MOBILE_DESC`** | 50.0% | 50.0% | 82.43% | 75.0% | 68.28% | 83.34% | 100.0% |
| **`SHORT_DESC`** | 0.0% | 0.0% | 73.58% | 65.81% | 46.39% | 76.82% | 100.0% |
| **`LONG_DESC1`** | 0.0% | 0.0% | 17.5% | 11.32% | 0.04% | 19.27% | 100.0% |
| **`RETAIL_DESC`** | 0.0% | 0.0% | 72.5% | 63.49% | 35.33% | 75.0% | 100.0% |
| **`MARKETING_DESCRIPTION`** | 0.0% | 0.0% | 13.08% | 3.33% | 0.9% | 5.77% | 100.0% |

## 4. Confidence Distribution & Anomaly Triage

- **Mean Confidence**: `0.9791`
- **Median Confidence**: `1.0`
- **Min / Max Confidence**: `0.94` / `1.0`
- **Workflow Status Counts**: `Validated: 654` | `Enriched: 346` | `Flagged: 0`
- **Needs Human Review**: `0` items (`0.0%`)

### Anomaly Code Breakdown:
- **`FALLBACK_TAXONOMY`**: 346 occurrences

## 5. Top Evaluated Delivery Schema Columns

| # | Column Header | Exact Match | Normalized Match | Levenshtein Sim | Enriched Populated | Expected Populated |
|:---|:---|:---|:---|:---|:---|:---|
| 1 | `MANUFACTURER_NAME` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 2 | `BRAND_NAME` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 3 | `TRADE_NAME` | 0.0% | 0.0% | 0.0% | 100.0% | 0.0% |
| 4 | `MANUFACTURER_PART_NUMBER` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 5 | `Classpath` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 6 | `Product Name` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 7 | `UNSPSC` | 0.0% | 0.0% | 0.0% | 100.0% | 0.0% |
| 8 | `INVOICE_DESC` | 0.0% | 0.0% | 42.81% | 100.0% | 100.0% |
| 9 | `MOBILE_DESC` | 50.0% | 50.0% | 82.43% | 100.0% | 100.0% |
| 10 | `SHORT_DESC` | 0.0% | 0.0% | 73.58% | 100.0% | 100.0% |
| 11 | `LONG_DESC1` | 0.0% | 0.0% | 17.5% | 100.0% | 100.0% |
| 12 | `RETAIL_DESC` | 0.0% | 0.0% | 72.5% | 100.0% | 100.0% |
| 13 | `MARKETING_DESCRIPTION` | 0.0% | 0.0% | 13.08% | 100.0% | 50.0% |
| 14 | `ATTRIBUTE_LABEL 1` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 15 | `ATTRIBUTE_VALUE 1` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 16 | `ATTRIBUTE_UOM 1` | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| 17 | `ATTRIBUTE_LABEL 4` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 18 | `ATTRIBUTE_VALUE 4` | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% |
| 19 | `ATTRIBUTE_UOM 4` | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% |
| 20 | `ATTRIBUTE_LABEL 5` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 21 | `ATTRIBUTE_VALUE 5` | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% |
| 22 | `ATTRIBUTE_UOM 5` | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% |
| 23 | `Product Image` | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% |
| 24 | `Specification Sheet` | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% |
| 25 | `Actual Image (Yes/No)` | 0.0% | 0.0% | 0.0% | 100.0% | 100.0% |