# UniHack Industrial Product Intelligence: QA Benchmarking Report
**Evaluation Timestamp**: 2026-08-16T15:03:15Z  
**Total Catalog Records**: 1000 | **Ground Truth Records**: 2 | **Columns**: 252

## 1. Executive Summary & Overall Scores

| Metric Dimension | Benchmark Score | Target Threshold | Status |
|:---|:---|:---|:---|
| **Overall Exact Match Rate** | `92.46%` | $\ge 85.0\%$ | ✅ PASS |
| **Normalized Match Rate** | `92.86%` | $\ge 90.0\%$ | ✅ PASS |
| **Avg Levenshtein Similarity** | `93.23%` | $\ge 90.0\%$ | ✅ PASS |
| **Avg Description BLEU Score** | `100.0%` | $\ge 80.0\%$ | ✅ PASS |
| **Avg Description ROUGE-L F1** | `100.0%` | $\ge 85.0\%$ | ✅ PASS |
| **Attribute Triplet F1 Score** | `95.84%` | $\ge 90.0\%$ | ✅ PASS |
| **Mean Catalog Confidence** | `97.85%` | $\ge 85.0\%$ | ✅ PASS |

## 2. Hard Rule Gates Compliance

| Gate Name | Status | Compliance | Target | Evaluated | Violations |
|:---|:---|:---|:---|:---|:---|
| **INVOICE_DESC <= 40 Chars & 100% ALL CAPS** | ✅ PASSED | `100.0%` | 100.0% | 1000 | 0 |
| **MOBILE_DESC 60 to 80 Chars Length Range** | ✅ PASSED | `100.0%` | 100.0% | 1000 | 0 |
| **Controlled Vocabulary (LOV) 0% Hallucinations** | ✅ PASSED | `100.0%` | 0.0% Hallucinations (100% Adherence) | 1587 | 0 |
| **Master 252-Column Delivery Schema Exact Sequence** | ✅ PASSED | `100.0%` | 100.0% Exact Sequence Match | 252 | 0 |

## 3. 5-Tier Description Generation NLP Metrics

| Description Tier | Exact Match | Normalized | Levenshtein | Jaccard | BLEU-4 | ROUGE-L F1 | Compliance |
|:---|:---|:---|:---|:---|:---|:---|:---|
| **`INVOICE_DESC`** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| **`MOBILE_DESC`** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| **`SHORT_DESC`** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| **`LONG_DESC1`** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| **`RETAIL_DESC`** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| **`MARKETING_DESCRIPTION`** | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |

## 4. Confidence Distribution & Anomaly Triage

- **Mean Confidence**: `0.9785`
- **Median Confidence**: `1.0`
- **Min / Max Confidence**: `0.94` / `1.0`
- **Workflow Status Counts**: `Validated: 644` | `Enriched: 356` | `Flagged: 0`
- **Needs Human Review**: `0` items (`0.0%`)

### Anomaly Code Breakdown:
- **`FALLBACK_TAXONOMY`**: 356 occurrences

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
| 8 | `INVOICE_DESC` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 9 | `MOBILE_DESC` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 10 | `SHORT_DESC` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 11 | `LONG_DESC1` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 12 | `RETAIL_DESC` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 13 | `MARKETING_DESCRIPTION` | 100.0% | 100.0% | 100.0% | 50.0% | 50.0% |
| 14 | `ATTRIBUTE_LABEL 1` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 15 | `ATTRIBUTE_VALUE 1` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 16 | `ATTRIBUTE_UOM 1` | 100.0% | 100.0% | 100.0% | 0.0% | 0.0% |
| 17 | `ATTRIBUTE_LABEL 4` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 18 | `ATTRIBUTE_VALUE 4` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 19 | `ATTRIBUTE_UOM 4` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 20 | `ATTRIBUTE_LABEL 5` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 21 | `ATTRIBUTE_VALUE 5` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 22 | `ATTRIBUTE_UOM 5` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| 23 | `Product Image` | 50.0% | 100.0% | 83.3% | 100.0% | 100.0% |
| 24 | `Specification Sheet` | 50.0% | 100.0% | 90.9% | 100.0% | 100.0% |
| 25 | `Actual Image (Yes/No)` | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |