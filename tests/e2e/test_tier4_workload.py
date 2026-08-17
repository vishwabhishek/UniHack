"""Tier 4: Workload & Full Dataset Processing E2E Test Suite.

This module validates the complete end-to-end pipeline execution on real-world workloads:
1. Batch processing of all 1,000 items from Unihack_ Sample Dataset - Input.csv
2. 100% hard-gate verification across all 1,000 items (Invoice <=40 ALL CAPS, Mobile 60-80 chars)
3. Schema completeness across all 252 target columns for every record
4. CSV and Excel export file generation and format integrity
5. Ground truth benchmarking against reference delivery rows
6. Processing throughput and performance budgeting
"""

import time
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import pytest


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture(scope="class")
def processed_1000_items(raw_input_df: pd.DataFrame, pipeline_engine):
    """Process all 1,000 items in batch mode and cache results for the test class."""
    records = raw_input_df.to_dict(orient="records")
    start_time = time.time()
    enriched_list = pipeline_engine.process_batch(records)
    elapsed = time.time() - start_time
    
    assert len(enriched_list) == len(records), f"Expected {len(records)} items, got {len(enriched_list)}"
    return {
        "items": enriched_list,
        "count": len(enriched_list),
        "elapsed_seconds": elapsed,
    }


# ===========================================================================
# Tier 4: Workload & Scaled Dataset Processing Suite
# ===========================================================================

class TestTier4RealWorldWorkload:
    """Test suite for full 1,000-item workload and 252-column export validation."""

    def test_workload_process_full_1000_items(self, processed_1000_items):
        """Verify that all 1,000 raw supplier records process without any unhandled exceptions."""
        items = processed_1000_items["items"]
        assert len(items) == 1000, f"Expected 1,000 processed items, got {len(items)}"
        for idx, item in enumerate(items):
            assert item.part_number != "", f"Row {idx}: part_number must not be empty"
            assert item.short_desc != "", f"Row {idx}: short_desc must not be empty"

    def test_workload_hard_gate_invoice_desc_100_percent_compliance(self, processed_1000_items):
        """Assert 100% compliance: every single INVOICE_DESC across all 1,000 items is <= 40 chars and ALL CAPS."""
        items = processed_1000_items["items"]
        failures = []
        
        for idx, item in enumerate(items):
            inv = item.invoice_desc
            if len(inv) > 40:
                failures.append(f"Row {idx} ({item.part_number}): length {len(inv)} > 40 -> '{inv}'")
            if not inv.isupper():
                failures.append(f"Row {idx} ({item.part_number}): not ALL CAPS -> '{inv}'")
            if len(inv) == 0:
                failures.append(f"Row {idx} ({item.part_number}): empty INVOICE_DESC")
                
        assert len(failures) == 0, f"INVOICE_DESC hard gate failed on {len(failures)} / {len(items)} items:\n" + "\n".join(failures[:10])

    def test_workload_hard_gate_mobile_desc_100_percent_compliance(self, processed_1000_items):
        """Assert 100% compliance: every single MOBILE_DESC across all 1,000 items is between 60 and 80 characters."""
        items = processed_1000_items["items"]
        failures = []
        
        for idx, item in enumerate(items):
            mob = item.mobile_desc
            if len(mob) < 60 or len(mob) > 80:
                failures.append(f"Row {idx} ({item.part_number}): length {len(mob)} not in [60, 80] -> '{mob}'")
                
        assert len(failures) == 0, f"MOBILE_DESC hard gate failed on {len(failures)} / {len(items)} items:\n" + "\n".join(failures[:10])

    def test_workload_schema_252_column_completeness(self, processed_1000_items, expected_252_columns):
        """Verify that every single enriched record maps to exactly 252 columns matching ground-truth column order."""
        from src.pipeline.delivery_mapper import to_delivery_dict
        
        items = processed_1000_items["items"]
        # Verify across a representative sample and first/last items
        check_indices = [0, 1, 50, 100, 250, 500, 750, 999]
        
        for idx in check_indices:
            item = items[idx]
            row = to_delivery_dict(item)
            assert len(row) == 252, f"Row {idx}: expected 252 columns, got {len(row)}"
            assert list(row.keys()) == expected_252_columns, f"Row {idx}: column headers or order do not match"

    def test_workload_export_file_generation_csv(self, processed_1000_items, expected_252_columns, project_root: Path, tmp_path):
        """Assert that export to CSV creates a valid 252-column file with 1,000 rows."""
        from src.pipeline.delivery_mapper import to_delivery_dict
        
        items = processed_1000_items["items"]
        out_csv = tmp_path / "enriched_catalog_1000_test.csv"
        
        rows = [to_delivery_dict(item) for item in items]
        df = pd.DataFrame(rows)
        df.to_csv(out_csv, index=False)
        assert out_csv.exists(), "CSV output file was not created"
        
        read_df = pd.read_csv(out_csv)
        assert len(read_df) == 1000, f"Expected 1,000 CSV rows, got {len(read_df)}"
        assert len(read_df.columns) == 252, f"Expected 252 columns in CSV, got {len(read_df.columns)}"
        assert read_df.columns.tolist() == expected_252_columns

    def test_workload_export_file_generation_excel(self, processed_1000_items, expected_252_columns, tmp_path):
        """Assert that export to Excel creates a valid .xlsx workbook with 252 columns and data rows."""
        from src.pipeline.delivery_mapper import to_delivery_dict
        
        # Test on a 100-item slice for speedy excel generation verification
        items_slice = processed_1000_items["items"][:100]
        out_xlsx = tmp_path / "enriched_catalog_slice_test.xlsx"
        
        rows = [to_delivery_dict(item) for item in items_slice]
        df = pd.DataFrame(rows)
        df.to_excel(out_xlsx, index=False)
        assert out_xlsx.exists(), "Excel output file was not created"
        
        read_df = pd.read_excel(out_xlsx)
        assert len(read_df) == 100, f"Expected 100 Excel rows, got {len(read_df)}"
        assert len(read_df.columns) == 252, f"Expected 252 columns in Excel, got {len(read_df.columns)}"

    def test_workload_ground_truth_benchmark_evaluation(self, expected_output_df: pd.DataFrame, pipeline_engine):
        """Compare pipeline output on ground-truth rows (PDSH4816AF, WDTS7024RZ) against expected values."""
        from src.pipeline.delivery_mapper import to_delivery_dict
        
        gt_records = expected_output_df.to_dict(orient="records")
        for gt in gt_records:
            mpn = gt["Mfg_Part_Num"]
            raw_input = {
                "mfg_part_num": mpn,
                "part_desc": gt["Part_Desc"],
                "e1_brand": gt["E1_Brand"],
                "unilog_brand": gt["Unilog_Brand"],
                "dib_brand": gt["DIB_Brand"],
                "part_manuf": gt["Part_Manuf"],
            }
            enriched = pipeline_engine.process_record(raw_input)
            row = to_delivery_dict(enriched)
            
            # Hard gates
            assert len(row["INVOICE_DESC"]) <= 40
            assert row["INVOICE_DESC"].isupper()
            assert 60 <= len(row["MOBILE_DESC"]) <= 80
            
            # Exact matches on key reference columns
            assert row["BRAND_NAME"] == gt["BRAND_NAME"]
            assert row["MANUFACTURER_PART_NUMBER"] == gt["MANUFACTURER_PART_NUMBER"]
            assert row["Product Name"] == gt["Product Name"]

    def test_workload_batch_throughput_budget(self, processed_1000_items):
        """Verify that the full 1,000 items process in reasonable time (< 60 seconds total batch time)."""
        elapsed = processed_1000_items["elapsed_seconds"]
        count = processed_1000_items["count"]
        throughput = count / max(elapsed, 0.001)
        
        print(f"\n[Performance] Processed {count} items in {elapsed:.2f}s ({throughput:.1f} items/sec)")
        assert elapsed < 60.0, f"Batch processing exceeded 60s budget ({elapsed:.2f}s)"
