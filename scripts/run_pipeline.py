#!/usr/bin/env python3
"""
CLI Runner for Industrial Product Intelligence & PIM Enrichment Pipeline.
Processes raw supplier catalog CSV into the standardized 252-column delivery format.
"""

import argparse
import csv
import os
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.models import RawProduct
from src.pipeline.engine import EnrichmentEngine
from src.pipeline.delivery_mapper import DeliveryMapper


def main():
    parser = argparse.ArgumentParser(description="Run Industrial PIM Enrichment Pipeline on distributor catalog data.")
    parser.add_argument(
        "--input", "-i",
        default=str(PROJECT_ROOT / "Unihack_ Sample Dataset - Input.csv"),
        help="Path to raw input CSV file"
    )
    parser.add_argument(
        "--output", "-o",
        default=str(PROJECT_ROOT / "data" / "output" / "enriched_catalog_252_columns.csv"),
        help="Path to output 252-column delivery CSV file"
    )
    parser.add_argument(
        "--limit", "-n",
        type=int,
        default=0,
        help="Optional limit on number of rows to process (0 = all)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable detailed logging"
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"Error: Input file {input_path} not found.")
        sys.exit(1)

    print("========================================================================")
    print("UNILOG INDUSTRIAL PRODUCT INTELLIGENCE & PIM ENRICHMENT PIPELINE")
    print("========================================================================")
    print(f"Input file:  {input_path}")
    print(f"Output file: {output_path}")

    # Load raw items
    raw_items = []
    with open(input_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            if args.limit and idx >= args.limit:
                break
            raw_items.append(RawProduct(
                mfg_part_num=row.get("Mfg_Part_Num", ""),
                part_desc=row.get("Part_Desc", ""),
                e1_brand=row.get("E1_Brand"),
                unilog_brand=row.get("Unilog_Brand"),
                dib_brand=row.get("DIB_Brand"),
                part_manuf=row.get("Part_Manuf"),
                row_id=idx + 1
            ))

    print(f"Loaded {len(raw_items)} raw catalog records.")
    print("Initializing Enrichment Engine...")
    start_time = time.time()

    engine = EnrichmentEngine()
    
    def progress_callback(current, total):
        pct = (current / total) * 100
        elapsed = time.time() - start_time
        speed = current / elapsed if elapsed > 0 else 0
        print(f"  Processed {current:4d}/{total} records ({pct:5.1f}%) | {speed:5.1f} items/sec", end="\r")

    print("Executing 7-stage enrichment pipeline...")
    enriched_products = engine.process_batch(raw_items, progress_callback=progress_callback)
    total_time = time.time() - start_time
    print()  # newline after progress

    # Write 252-column delivery CSV
    print(f"Writing {len(enriched_products)} records to {output_path}...")
    headers = DeliveryMapper.get_column_headers()
    
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for p in enriched_products:
            delivery_dict = DeliveryMapper.to_delivery_dict(p)
            writer.writerow(delivery_dict)

    file_size_kb = output_path.stat().st_size / 1024

    # Compliance & Quality Audit
    invoice_violations = [p for p in enriched_products if len(p.invoice_desc) > 40 or not p.invoice_desc.isupper()]
    mobile_violations = [p for p in enriched_products if len(p.mobile_desc) < 60 or len(p.mobile_desc) > 80]
    flagged_items = [p for p in enriched_products if p.status == "Flagged"]
    avg_confidence = sum(p.confidence_score for p in enriched_products) / len(enriched_products) if enriched_products else 0

    print("========================================================================")
    print("PIPELINE EXECUTION & COMPLIANCE SUMMARY")
    print("========================================================================")
    print(f"Total Records Processed:     {len(enriched_products):,}")
    print(f"Elapsed Time:                {total_time:.2f} s ({len(enriched_products)/total_time:.1f} records/sec)")
    print(f"Output File Size:            {file_size_kb:.1f} KB (252 columns)")
    print(f"Average Confidence Score:    {avg_confidence:.3f}")
    print(f"Enriched / Validated Rate:   {((len(enriched_products) - len(flagged_items)) / len(enriched_products)) * 100:.1f}%")
    print(f"Human Review Flagged Count:  {len(flagged_items)} ({len(flagged_items)/len(enriched_products)*100:.1f}%)")
    print(f"INVOICE_DESC Compliance:     {((len(enriched_products) - len(invoice_violations)) / len(enriched_products)) * 100:.1f}% (<= 40 chars ALL CAPS)")
    print(f"MOBILE_DESC Compliance:      {((len(enriched_products) - len(mobile_violations)) / len(enriched_products)) * 100:.1f}% (60 - 80 chars)")
    print("========================================================================")

    if invoice_violations:
        print(f"Warning: {len(invoice_violations)} invoice description violations found.")
    if mobile_violations:
        print(f"Warning: {len(mobile_violations)} mobile description violations found.")


if __name__ == "__main__":
    main()
