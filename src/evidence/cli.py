"""
Command-Line Interface for Official Manufacturer Evidence Management.
"""

import argparse
import sys
import json
def format_table(rows: list, headers: list) -> str:
    if not rows:
        return ""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))
    
    sep = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"
    hdr_line = "| " + " | ".join(f"{str(h):<{col_widths[i]}}" for i, h in enumerate(headers)) + " |"
    
    out = [sep, hdr_line, sep]
    for row in rows:
        out.append("| " + " | ".join(f"{str(v):<{col_widths[i]}}" for i, v in enumerate(row)) + " |")
    out.append(sep)
    return "\n".join(out)

from .models import SourceRegistrationRequest, EvidenceType
from .registry import EvidenceRegistryManager
from .search_engine import EvidenceSearchEngine
from .extractor import EvidenceAttributeExtractor
from .seed_data import seed_demo_evidence


def main():
    parser = argparse.ArgumentParser(
        prog="python -m src.evidence.cli",
        description="UniHack Simplifi Official Manufacturer Evidence Ingestion & Traceability CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Command: list
    list_p = subparsers.add_parser("list", help="List all registered manufacturer evidence sources")

    # Command: register
    reg_p = subparsers.add_parser("register", help="Register a new official manufacturer source")
    reg_p.add_argument("--url", type=str, help="Official manufacturer page or PDF URL")
    reg_p.add_argument("--mpn", type=str, required=True, help="Manufacturer Part Number")
    reg_p.add_argument("--brand", type=str, required=True, help="Brand Name")
    reg_p.add_argument("--manufacturer", type=str, required=True, help="Manufacturer Legal Entity")
    reg_p.add_argument("--file", type=str, help="Local HTML or text file path with downloaded content")
    reg_p.add_argument("--type", choices=["page", "pdf"], default="page", help="Source type (page | pdf)")
    reg_p.add_argument("--title", type=str, help="Document title")

    # Command: query
    query_p = subparsers.add_parser("query", help="Search ingested evidence chunks")
    query_p.add_argument("--mpn", type=str, help="Filter by MPN")
    query_p.add_argument("--keyword", type=str, help="Keyword query")

    # Command: extract
    ext_p = subparsers.add_parser("extract", help="Extract candidate specifications with citations for an MPN")
    ext_p.add_argument("--mpn", type=str, required=True, help="Target MPN")

    # Command: enrich
    enr_p = subparsers.add_parser("enrich", help="Execute 6-step LOV/UOM enrichment lifecycle and assemble verified descriptions")
    enr_p.add_argument("--mpn", type=str, required=True, help="Target MPN")

    # Command: seed
    seed_p = subparsers.add_parser("seed", help="Seed demo official manufacturer evidence")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    mgr = EvidenceRegistryManager()

    if args.command == "list":
        entries = mgr.load_registry()
        if not entries:
            print("No evidence sources registered yet.")
            return

        table = []
        for e in entries:
            table.append([
                e.source_id,
                e.mpn,
                e.brand,
                e.source_type,
                e.source_status,
                e.chunks_count,
                e.file_hash[:8] if e.file_hash else "-",
                e.url or e.raw_file_path or "-"
            ])
        headers = ["Source ID", "MPN", "Brand", "Type", "Status", "Chunks", "Hash", "URL / Source Path"]
        print(format_table(table, headers))

    elif args.command == "register":
        content = ""
        if args.file:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()

        src_type = EvidenceType.MANUFACTURER_PDF.value if args.type == "pdf" else EvidenceType.MANUFACTURER_PAGE.value
        req = SourceRegistrationRequest(
            url=args.url,
            mpn=args.mpn,
            brand=args.brand,
            manufacturer=args.manufacturer,
            source_type=src_type,
            title=args.title,
            raw_content=content
        )
        res = mgr.register_source(req)
        print(f"\n[{res.source_status}] Success: {res.success}")
        print(f"Source ID: {res.source_id}")
        print(f"Chunks Count: {res.chunks_count}")
        print(f"Message: {res.message}")
        if res.validation_flags:
            print(f"Validation Flags: {', '.join(res.validation_flags)}")

    elif args.command == "query":
        engine = EvidenceSearchEngine(mgr)
        if args.keyword:
            chunks = engine.search_by_keyword(args.keyword, mpn=args.mpn)
        elif args.mpn:
            chunks = engine.search_by_mpn(args.mpn)
        else:
            chunks = mgr.get_all_active_chunks()

        print(f"\nFound {len(chunks)} matching evidence chunks:\n")
        for c in chunks:
            print(f"=== [{c.mpn}] {c.section_title} (Chunk ID: {c.chunk_id}) ===")
            if c.key_value_specs:
                print(f"  Specs: {json.dumps(c.key_value_specs, indent=2)}")
            print(f"  Text: {c.text_content[:200]}...")
            print("-" * 60)

    elif args.command == "extract":
        extractor = EvidenceAttributeExtractor(mgr)
        candidates = extractor.extract_candidates_for_mpn(args.mpn)
        if not candidates:
            print(f"No candidates found for MPN '{args.mpn}'. Make sure official evidence has been registered.")
            return

        table = []
        for c in candidates:
            table.append([
                c.field_name,
                c.candidate_value,
                c.normalized_value,
                c.source_type,
                c.source_page_or_section,
                c.verification_status,
                f"{c.confidence * 100:.0f}%"
            ])
        headers = ["Field Name", "Candidate", "Normalized", "Source Type", "Section", "Status", "Conf"]
        print(f"\nExtracted Official Candidates for MPN: {args.mpn}")
        print(format_table(table, headers))

    elif args.command == "enrich":
        from .enrichment_service import EvidenceEnrichmentService
        service = EvidenceEnrichmentService(mgr)
        res = service.enrich_product_attributes(args.mpn)
        
        if res.get("status") == "NO_EVIDENCE_FOUND":
            print(f"Error: {res.get('message')}")
            return
            
        print(f"\n=======================================================")
        print(f" ENRICHMENT REPORT FOR MPN: {res['mpn']} ({res['brand']})")
        print(f" Manufacturer: {res['manufacturer']}")
        print(f" Provenance Score: {res['provenance_summary'].verification_score}%")
        print(f"=======================================================\n")
        
        print("--- Enriched & Verified Attributes (Raw vs Normalized) ---")
        table = []
        for fname, data in res["enriched_attributes"].items():
            table.append([
                fname,
                data.get("candidate_value", "-"),
                data.get("normalized_value", "-"),
                data.get("status", "verified"),
                data.get("dictionary", "Master Index")
            ])
        headers = ["Field Name", "Candidate (Raw)", "Normalized (LOV/UOM)", "Status", "LOV Reference"]
        print(format_table(table, headers))
        
        if res.get("rejected_attributes"):
            print("\n--- Rejected Candidate Facts (Failed LOV Validation) ---")
            rej_table = []
            for r in res["rejected_attributes"]:
                rej_table.append([r["field_name"], r["candidate_value"], r["reason"]])
            print(format_table(rej_table, ["Field Name", "Rejected Value", "Reason"]))
            
        print("\n--- Verified-Only Synchronized Product Descriptions ---")
        descs = res.get("verified_descriptions", {})
        print(f"  [SHORT_DESC]   : {descs.get('short_desc')}")
        print(f"  [LONG_DESC1]   : {descs.get('long_desc1')}")
        print(f"  [INVOICE_DESC] : {descs.get('invoice_desc')} ({len(descs.get('invoice_desc', ''))} chars)")
        print(f"  [MOBILE_DESC]  : {descs.get('mobile_desc')} ({len(descs.get('mobile_desc', ''))} chars)")

    elif args.command == "seed":
        results = seed_demo_evidence()
        print(f"Seeded {len(results)} official manufacturer sources.")


if __name__ == "__main__":
    main()
