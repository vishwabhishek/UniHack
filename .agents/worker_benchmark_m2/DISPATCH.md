## 2026-08-16T11:35:23Z
You are Worker 2 (QA Benchmarking & Quality Assurance Suite Specialist) for the Industrial Product Intelligence & PIM Enrichment project.
Your working directory is /home/abhishek-vishwakarma/Documents/Hackathons/Unilog/.agents/worker_benchmark_m2.

Tasks:
1. Implement `src/benchmark/metrics.py`:
   - Exact match score
   - Levenshtein distance and normalized similarity
   - Token Jaccard similarity
   - BLEU score (BLEU-1, BLEU-2, BLEU-4) for text descriptions
   - ROUGE-L (Longest Common Subsequence) score
2. Implement `src/benchmark/hard_gates.py`:
   - Assert 100% compliance for `INVOICE_DESC` <= 40 chars & ALL CAPS
   - Assert 100% compliance for `MOBILE_DESC` 60 to 80 chars
   - Assert 0% LOV hallucinations (verifies extracted values match canonical LOVs)
   - Assert 252-column schema match (all expected columns present in exact order)
3. Implement `src/benchmark/confidence.py`:
   - 5-factor composite confidence scoring formula:
     `C = 0.20 * C_brand + 0.20 * C_tax + 0.25 * C_attr + 0.20 * C_desc + 0.15 * C_comp`
   - Anomaly detector: flags items with confidence < 0.85 or data conflicts as `Needs Human Review` / `Flagged`.
4. Implement `src/benchmark/evaluator.py`:
   - Evaluates enriched dataset against ground truth (`Unihack_ Expected Output - Delivery Format.csv` and ground truth reference records).
   - Computes:
     - Overall accuracy and per-column match rates across all 252 columns
     - Exact match and token similarity for all 5 description tiers
     - Hard gate compliance pass/fail status
     - LOV adherence percentage and hallucination rate
     - Missing field rates
     - Confidence distribution and anomaly summary
5. Implement `scripts/run_benchmark.py` and `src/benchmark/cli.py`:
   - CLI command accepting enriched CSV path and ground truth path.
   - Outputs rich console summary tables, saves structured JSON (`data/output/benchmark_report.json`), and generates markdown report (`data/output/benchmark_report.md`).
6. Implement `tests/unit/test_benchmark.py` and verify all tests pass with pytest.
7. Run the benchmark on `data/output/enriched_catalog_252_columns.csv` against `Unihack_ Expected Output - Delivery Format.csv` and verify clean execution.
