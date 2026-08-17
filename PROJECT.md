# Project: Industrial Product Intelligence & PIM Enrichment Pipeline & Dashboard (UniHack)

## Architecture

The system is organized into modular Python packages and a modern React TypeScript web application:

```
Unilog/
├── data/                                  # Data inputs, ground truths, LOV dictionaries, and output exports
│   ├── raw/                               # Unihack_ Sample Dataset - Input.csv (1,000 raw supplier records)
│   ├── ground_truth/                      # Unihack_ Expected Output - Delivery Format.csv (252 columns)
│   ├── dictionaries/                      # Canonical brand mappings, taxonomy classpaths, LOV tables, UOM rules
│   └── output/                            # Generated 252-column delivery CSV/Excel exports & benchmark reports
├── src/
│   ├── pipeline/                          # R1: Multi-Stage Product Catalog Enrichment Engine
│   │   ├── __init__.py
│   │   ├── models.py                      # Pydantic data schemas (RawProduct, EnrichedProduct, DeliveryRow, AttributeTriple)
│   │   ├── sanitizer.py                   # Stage 1: Ingestion cleaner & placeholder nullifier
│   │   ├── entity_resolver.py             # Stage 2: Canonical brand & manufacturer entity resolution (®/™ casing)
│   │   ├── taxonomy.py                    # Stage 3: Classpath (Dept > Class > Fine) & UNSPSC classification
│   │   ├── attribute_extractor.py         # Stage 4: Attribute extraction & LOV controlled vocabulary validation
│   │   ├── uom_standardizer.py            # Stage 5: UOM standardization & 64th decimal-to-fraction converter
│   │   ├── description_generator.py       # Stage 6: 5-Tier description engine (Invoice <=40 CAPS, Mobile 60-80)
│   │   ├── delivery_mapper.py             # Stage 7: Exact 252-column delivery row assembler
│   │   └── engine.py                      # Master pipeline orchestrator & batch processor
│   ├── benchmark/                         # R2: Ground-Truth Benchmarking & Quality Assurance Suite
│   │   ├── __init__.py
│   │   ├── metrics.py                     # Exact match, Levenshtein, Token Jaccard, BLEU-1/2/4, ROUGE-L
│   │   ├── hard_gates.py                  # Strict assertion verifier (100% Invoice <=40, Mobile 60-80, 0% LOV hallucination)
│   │   ├── confidence.py                  # 5-Factor composite confidence scorer & anomaly detector (< 0.85)
│   │   ├── evaluator.py                   # 252-column ground truth evaluator
│   │   └── cli.py                         # CLI runner outputting JSON & Markdown benchmark summary
│   ├── backend/                           # R3: FastAPI REST Backend Service
│   │   ├── __init__.py
│   │   ├── main.py                        # FastAPI application setup, CORS, lifespan, static file serving
│   │   ├── config.py                      # Backend settings & paths
│   │   ├── state.py                       # In-memory indexed catalog store & review queue state
│   │   ├── routes/
│   │   │   ├── catalog.py                 # GET /api/products, GET /api/products/{id}, stats, filters
│   │   │   ├── playground.py              # POST /api/playground/transform (real-time sub-second sandbox)
│   │   │   ├── review.py                  # GET /api/review/queue, POST /api/review/{id}/approve, PUT /api/review/{id}
│   │   │   ├── benchmark.py               # GET /api/benchmark/results, POST /api/benchmark/run
│   │   │   └── export.py                  # GET /api/export/csv, GET /api/export/xlsx (252 columns)
│   │   └── schemas.py                     # API request/response schemas
│   └── frontend/                          # R3: Modern React + TypeScript + Vite + Tailwind Dashboard
│       ├── src/
│       │   ├── App.tsx                    # Main app shell & router/view navigation
│       │   ├── components/                # Modular UI components (6 Views + Navbar & KPIs)
│       │   │   ├── Navbar.tsx             # Top navigation & system status
│       │   │   ├── MetricsBanner.tsx      # Global KPI cards (1,000 products, 100% Hard Gates, etc.)
│       │   │   ├── CatalogExplorer.tsx    # 1,000-item searchable/filterable grid with status badges
│       │   │   ├── TransformationInspector.tsx # Side-by-side raw vs 5-tier & attribute diff viewer
│       │   │   ├── InteractivePlayground.tsx   # Live instant sandbox for arbitrary distributor strings
│       │   │   ├── ReviewQueue.tsx        # Human-in-the-loop triage, editor & approval workflow
│       │   │   ├── BenchmarkDashboard.tsx # QA metrics visualizer, radar charts, hard-gate pass badges
│       │   │   └── DeliveryExporter.tsx   # Full 252-column export trigger with column selector & preview
│       │   ├── services/api.ts            # Typed Axios/Fetch API client
│       │   └── types/index.ts             # Shared frontend TypeScript interfaces
│       ├── package.json
│       ├── vite.config.ts
│       ├── tailwind.config.js
│       └── dist/                          # Production static build
├── tests/                                 # 306 Passing Opaque-Box, Unit, Integration & Adversarial Tests
│   ├── conftest.py                        # Test fixtures & test adapters
│   ├── unit/                              # Unit tests for pipeline & benchmarking
│   ├── integration/                       # FastAPI REST API & pipeline integration tests
│   ├── e2e/                               # 4-Tier E2E test suite (Feature, Boundary, Pairwise, Workload)
│   └── adversarial/                       # Tier 5 white-box coverage hardening tests
├── scripts/
│   ├── run_pipeline.py                    # Standalone CLI batch runner (1,000 items in <0.6s)
│   ├── run_benchmark.py                   # Standalone CLI benchmark runner
│   └── start_dashboard.sh                 # Single-command backend + frontend startup script
└── PROJECT.md
```

---

## Feature Inventory

| # | Feature | Description | Milestone | Status |
|---|---------|-------------|-----------|:------:|
| 1 | Ingestion & Placeholder Sanitizer | Strip dummy placeholders (`-- Unbranded --`, `-- No Unilog Brand --`, `-- No DIB Brand --`, `COMMODITY - UNBRANDED`), normalize Unicode, isolate MPN tokens. | M1 | DONE |
| 2 | Canonical Brand & Manufacturer Resolver | Map supplier strings/distributor codes to legal manufacturer names & trademarked brands with symbols (`FRIGIDAIRE®`, `Whirlpool®`, `Trex®`). | M1 | DONE |
| 3 | Taxonomy & UNSPSC Classifier | Classify items into hierarchical 3-level Classpath (`Dept > Class > Fine`) and 8-digit UNSPSC codes. | M1 | DONE |
| 4 | Attribute Extractor & Controlled Vocabulary (LOV) | Extract technical specifications into 50 slot triplets (`LABEL`, `VALUE`, `UOM`) strictly validated against canonical LOV dictionaries (0% hallucination). | M1 | DONE |
| 5 | UOM & Fraction Standardization | 64th decimal-to-fraction converter (`50.25 in` → `50-1/4 in`), hyphenated mixed fractions, mandatory single space before unit (`24 in`, `120 V`, `15 A`, `47 dBA`), canonical unit abbreviations. | M1 | DONE |
| 6 | 5-Tier Content & Description Generator | Generate `INVOICE_DESC` ($\le 40$ chars, 100% ALL CAPS), `MOBILE_DESC` ($60\text{--}80$ chars), `SHORT_DESC` (facet title), `LONG_DESC1` (full spec sentence), `MARKETING_DESCRIPTION` (feature bullets). | M1 | DONE |
| 7 | Full 252-Column Delivery Mapper | Assemble all 252 target columns matching exact ordering and naming of `Unihack_ Expected Output - Delivery Format.csv`. | M1 | DONE |
| 8 | Multi-Metric Similarity Evaluator | Measure Exact Match, Levenshtein, Token Jaccard, BLEU-1/2/4, and ROUGE-L across generated descriptions against ground truth. | M2 | DONE |
| 9 | Hard Gate Compliance Validator | Assert 100% compliance on character limits (`INVOICE_DESC` $\le 40$ CAPS, `MOBILE_DESC` $60\text{--}80$) and 0% LOV hallucinations. | M2 | DONE |
| 10 | Composite Confidence Scorer & Anomaly Detection | Calculate 5-factor weighted confidence ($C_{\text{brand}}, C_{\text{tax}}, C_{\text{attr}}, C_{\text{desc}}, C_{\text{comp}}$) and flag items with $C < 0.85$ for "Needs Human Review". | M2 | DONE |
| 11 | QA Benchmark CLI & Reporting Engine | Execute complete evaluation against ground-truth and generate structured JSON & Markdown summary reports. | M2 | DONE |
| 12 | FastAPI Backend Service | REST API providing endpoints for catalog browsing, single item transformation, live sandbox execution, HITL queue, benchmark metrics, and export. | M3 | DONE |
| 13 | Catalog Explorer & Product Grid UI | Paginated, searchable, filterable grid displaying all 1,000 catalog products with status badges (Draft → Enriched → Validated → Flagged). | M3 | DONE |
| 14 | Side-by-Side Transformation Inspector UI | Visual diff comparing raw supplier input against all 5 description tiers, normalized attributes, and confidence breakdown. | M3 | DONE |
| 15 | Real-Time Interactive Playground UI | Instant sandbox for judges to paste arbitrary messy distributor strings and view step-by-step pipeline transformations with sub-second feedback. | M3 | DONE |
| 16 | Human-in-the-Loop Review Queue UI | Dedicated triage interface to review low-confidence items ($C < 0.85$), edit attributes/descriptions, and approve them for production. | M3 | DONE |
| 17 | Full 252-Column Delivery Exporter UI & API | One-click CSV and Excel exporter outputting the processed 1,000-item catalog in the exact Unilog 252-column schema. | M3 | DONE |
| 18 | Opaque-Box E2E Testing Suite (Tiers 1–4) | Comprehensive test suite covering feature coverage, boundary conditions, pairwise combinations, and real-world catalog workloads. | M4 | DONE |
| 19 | Adversarial Coverage Hardening (Tier 5) | White-box stress testing targeting edge cases, malformed strings, and boundary character limits. | M4 | DONE |

---

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|:------:|
| E2E | E2E Testing Track | Comprehensive 4-Tier test suite (`tests/e2e/`), test runner, and `TEST_READY.md`. | none | **DONE** |
| M1 | Core Enrichment Pipeline Engine | Full Python enrichment engine (`src/pipeline/`): Sanitizer, Resolver, Taxonomy, Attributes & LOV, UOM/Fractions, 5-Tier Descriptions, 252-Column Mapper. | none | **DONE** |
| M2 | QA Benchmarking & Scoring Suite | Ground-truth scoring engine (`src/benchmark/`): metrics (EM, Levenshtein, BLEU, ROUGE-L), 100% hard gates, confidence scoring, anomaly detection, CLI runner. | M1 | **DONE** |
| M3 | FastAPI Backend & Modern PIM Dashboard UI | FastAPI REST service (`src/backend/`) and React + TypeScript dashboard (`src/frontend/`): Catalog Explorer, Side-by-Side Inspector, Interactive Playground, HITL Review Queue, 252-Column Exporter. | M1, M2 | **DONE** |
| M4 | 100% E2E Verification & Adversarial Hardening | Verify all 1,000 items process cleanly, 100% of E2E test cases pass, execute Tier 5 adversarial stress testing (306/306 passing tests), and verify single-command startup. | E2E, M1, M2, M3 | **DONE** |

---

## Verification Results Summary

- **Total Automated Tests**: **306 tests** across Tiers 1–5, Integration, and Unit tests (100% pass rate in 6.55s).
- **Hard Gate Compliance**:
  - `INVOICE_DESC` <= 40 chars & 100% ALL CAPS: **1,000 / 1,000 items compliant (100.0%)**
  - `MOBILE_DESC` 60–80 chars: **1,000 / 1,000 items compliant (100.0%)**
  - Controlled Vocabulary (LOV) 0% Hallucinations: **100.0% adherence (0 hallucinations)**
  - Master 252-Column Delivery Schema: **252 / 252 headers match exactly**
- **Catalog Processing Throughput**: 1,000 items enriched in 0.57s (**>1,750 items/sec**).
- **Interactive Playground Latency**: **~1.33 ms** (sub-second requirement exceeded by 750x).
- **Single-Command Startup**: `./scripts/start_dashboard.sh` launches on `http://localhost:8000`.
