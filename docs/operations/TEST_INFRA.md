# E2E Test Infra: Industrial Product Intelligence & PIM Enrichment Pipeline

## Test Philosophy
- Opaque-box, requirement-driven testing derived strictly from `ORIGINAL_REQUEST.md`.
- No internal code dependence: tests invoke public interfaces (CLI scripts, Pipeline `Engine.process_record()`, FastAPI REST endpoints, and export outputs).
- Strict Assertion of Hard Gates:
  - 100% of `INVOICE_DESC` <= 40 characters and uppercase.
  - 100% of `MOBILE_DESC` between 60 and 80 characters.
  - 0% LOV hallucinations (all extracted technical attributes must match canonical LOVs).
  - Exact 252-column schema conformance and non-empty core fields.

## Feature Inventory & Test Coverage

| # | Feature | Requirement Source | Tier 1 (>=5) | Tier 2 (>=5) | Tier 3 (Pairwise) | Tier 4 (Workload) |
|---|---------|-------------------|:------------:|:------------:|:-----------------:|:-----------------:|
| 1 | Ingestion & Sanitization | R1 Ingestion | 5 | 5 | ✓ | ✓ |
| 2 | Brand/Manufacturer Entity Resolution | R1 Entity Resolution | 5 | 5 | ✓ | ✓ |
| 3 | Taxonomy & UNSPSC Classification | R1 Taxonomy | 5 | 5 | ✓ | ✓ |
| 4 | Attribute Extractor & LOV Engine | R1 Attributes | 5 | 5 | ✓ | ✓ |
| 5 | UOM & Fraction Standardization | R1 UOM | 5 | 5 | ✓ | ✓ |
| 6 | 5-Tier Description Generation | R1 5-Tier Descriptions | 5 | 5 | ✓ | ✓ |
| 7 | Full 252-Column Delivery Mapping | R1 Delivery Schema | 5 | 5 | ✓ | ✓ |
| 8 | Ground-Truth Benchmarking QA Suite | R2 QA Suite | 5 | 5 | ✓ | ✓ |
| 9 | Confidence Scoring & Anomaly Detection | R2 Confidence | 5 | 5 | ✓ | ✓ |
| 10 | FastAPI REST Backend API | R3 Backend | 5 | 5 | ✓ | ✓ |
| 11 | Catalog Explorer & Filter Engine | R3 Catalog Grid | 5 | 5 | ✓ | ✓ |
| 12 | Real-time Playground Sandbox API | R3 Playground | 5 | 5 | ✓ | ✓ |
| 13 | HITL Review & Approval Workflow | R3 HITL Queue | 5 | 5 | ✓ | ✓ |
| 14 | 252-Column CSV/Excel Exporter | R3 Exporter | 5 | 5 | ✓ | ✓ |

## Test Tiers

- **Tier 1: Feature Coverage (>= 5 tests per feature)**: Isolated happy-path unit and functional tests for every individual module and endpoint.
- **Tier 2: Boundary & Corner Cases (>= 5 tests per feature)**: Extreme length strings, empty inputs, unicode symbols, fraction conversions at limits (`0.0625`, `0.9375`, `128.5`), missing supplier data, invalid LOVs.
- **Tier 3: Cross-Feature Combinations**: Multi-feature interaction tests (e.g., entity resolution + LOV extraction + description length constraints on complex items).
- **Tier 4: Real-World Workloads**: Full 1,000-item batch processing, 252-column export validation against delivery format, and end-to-end benchmark comparison against ground truth.

## Test Runner
- Command: `python3 -m pytest tests/ -v`
- Pass Condition: 100% tests passing, zero errors or warnings.
