# Project: UniHack Simplifi — Industrial Product Intelligence & PIM Enrichment Platform

## Architecture & Codebase Map

The system is organized into modular Python packages, a REST backend, and a modern React TypeScript evidence workbench:

```text
Unilog/
├── data/                                  # Data inputs, reference dictionaries, and exports
│   ├── raw/                               # Unihack_ Sample Dataset - Input.csv (1,000 raw supplier records)
│   ├── ground_truth/                      # Unihack_ Expected Output - Delivery Format.csv (252 columns)
│   ├── dictionaries/                      # Canonical brand mappings, taxonomy classpaths, LOV tables, UOM rules
│   ├── evidence/                          # Official manufacturer evidence registry & storage
│   │   ├── source_registry.json           # Cryptographically hashed manufacturer source catalog
│   │   ├── raw/                           # Ingested raw HTML product pages & text spec sheets
│   │   └── processed/                     # Discrete JSON chunk files indexed by section and page
│   └── output/                            # Generated 252-column delivery CSV/Excel exports
├── src/
│   ├── pipeline/                          # Multi-Stage Product Catalog Enrichment Engine
│   │   ├── models.py                      # Pydantic data schemas (RawProduct, EnrichedProduct, DeliveryRow, EvidenceRecord)
│   │   ├── sanitizer.py                   # Stage 1: Ingestion cleaner & placeholder nullifier
│   │   ├── entity_resolver.py             # Stage 2: Canonical brand & manufacturer entity resolution (®/™ casing)
│   │   ├── taxonomy.py                    # Stage 3: Explainable Classpath (Dept > Class > Fine) & UNSPSC classification
│   │   ├── attribute_extractor.py         # Stage 4: Attribute extraction & LOV controlled vocabulary validation
│   │   ├── uom_standardizer.py            # Stage 5: UOM standardization & decimal-to-fraction converter
│   │   ├── description_generator.py       # Stage 6: 5-Tier verified-only description engine
│   │   ├── delivery_mapper.py             # Stage 7: Exact 252-column delivery row assembler & formula sanitizer
│   │   ├── confidence_config.py           # Single source of truth for confidence weights & penalties
│   │   └── engine.py                      # Master pipeline orchestrator
│   ├── evidence/                          # Official Manufacturer Evidence Ingestion & Provenance Service
│   │   ├── models.py                      # SourceRegistryEntry, EvidenceChunk, ExtractedCandidate schemas
│   │   ├── registry.py                    # EvidenceRegistryManager with SHA-256 integrity hashing & whitelist
│   │   ├── extractor.py                   # EvidenceAttributeExtractor for candidate specifications
│   │   ├── search_engine.py               # EvidenceSearchEngine for keyword and MPN chunk lookups
│   │   └── enrichment_service.py          # EvidenceEnrichmentService (6-step lifecycle & verified description assembly)
│   ├── benchmark/                         # Ground-Truth Benchmarking & Quality Assurance Suite
│   │   ├── metrics.py                     # Exact match, Levenshtein, Token Jaccard, BLEU-1/2/4, ROUGE-L
│   │   ├── hard_gates.py                  # Strict assertion verifier (100% Invoice <=40, Mobile 60-80, 252 Columns)
│   │   ├── confidence.py                  # Multi-factor explainable confidence scorer & penalty calculation
│   │   ├── evaluator.py                   # 252-column schema & ground-truth evaluator with calibration states
│   │   └── cli.py                         # CLI runner outputting JSON & Markdown benchmark summary
│   ├── backend/                           # FastAPI REST Backend Service
│   │   ├── main.py                        # FastAPI application setup, CORS, lifespan, static file serving
│   │   ├── auth.py                        # JWT authentication, Argon2id hashing, Role-Based Access Control (RBAC)
│   │   ├── config.py                      # Backend settings & paths
│   │   ├── state.py                       # In-memory thread-safe indexed catalog store & review queue state
│   │   ├── routes/
│   │   │   ├── catalog.py                 # GET /api/products, GET /api/products/{id}, stats, filters
│   │   │   ├── evidence.py                # GET /api/evidence/registry, POST /api/evidence/register, GET /api/evidence/query
│   │   │   ├── playground.py              # POST /api/playground/transform, GET /api/playground/presets
│   │   │   ├── review.py                  # Field-level review actions (approve, edit, reject, mark_unknown) & promote
│   │   │   ├── benchmark.py               # GET /api/benchmark/results, POST /api/benchmark/run
│   │   │   ├── rag.py                     # GET /api/rag/search (Hybrid keyword + semantic neural search)
│   │   │   └── export.py                  # GET /api/export/csv, GET /api/export/xlsx (252 columns)
│   │   └── schemas.py                     # API request/response schemas
│   └── frontend/                          # React + TypeScript + Vite + Tailwind Workbench
│       ├── src/
│       │   ├── App.tsx                    # Main app shell & router/view navigation
│       │   ├── components/                # Modular UI components
│       │   │   ├── Sidebar.tsx            # Grouped navigation (WORKSPACE, GOVERNANCE, DELIVERY)
│       │   │   ├── Topbar.tsx             # Contextual breadcrumbs, search, user session, mobile toggle
│       │   │   ├── MetricsBanner.tsx      # Scoped catalog KPI counters and evidence coverage strip
│       │   │   ├── CatalogExplorer.tsx    # Searchable/filterable grid with evidence badges & search mode selector
│       │   │   ├── TransformationInspector.tsx # 6-Tab inspector (Overview, Evidence, Attributes, Quality, 252-Col, Graph)
│       │   │   ├── EvidenceInbox.tsx      # Live manufacturer source registry, chunk drawer, source registration modal
│       │   │   ├── InteractivePlayground.tsx   # Live instant sandbox with fittings demo preset
│       │   │   ├── ReviewQueue.tsx        # Field-level exception triage, edit drawer, mark unknown, audit history
│       │   │   ├── BenchmarkDashboard.tsx # Validation & Benchmark screen with schema compliance metrics
│       │   │   └── DeliveryExporter.tsx   # Full 252-column export trigger with column selector & preview
│       │   ├── services/api.ts            # Typed Fetch API client
│       │   └── types/index.ts             # Shared frontend TypeScript interfaces
│       ├── package.json
│       ├── vite.config.ts
│       ├── tailwind.config.js
│       └── dist/                          # Production static build
├── tests/                                 # 382 Passing Unit, Integration, E2E & Adversarial Tests
│   ├── conftest.py                        # Test fixtures & test adapters
│   ├── unit/                              # Unit tests for pipeline, evidence, explainability, provenance
│   ├── integration/                       # FastAPI REST API & pipeline integration tests
│   ├── e2e/                               # 4-Tier E2E test suite (Feature, Boundary, Pairwise, Workload)
│   └── adversarial/                       # Tier 5 white-box coverage hardening & OWASP security tests
├── scripts/
│   ├── run_pipeline.py                    # Standalone CLI batch runner
│   ├── run_benchmark.py                   # Standalone CLI benchmark runner
│   └── start_dashboard.sh                 # Startup script
└── PROJECT.md
```

---

## Feature Inventory & Completion Status

| # | Feature Area | Description | Status |
|---|--------------|-------------|:------:|
| 1 | Ingestion & Placeholder Sanitizer | Strip dummy placeholders (`-- Unbranded --`, `-- No Unilog Brand --`), normalize Unicode, clean noisy distributor feeds. | DONE |
| 2 | Canonical Brand & Manufacturer Resolver | Map supplier strings to legal manufacturer names & trademarked brands with proper casing and symbols (`FRIGIDAIRE®`, `SharkBite®`, `NIBCO®`). | DONE |
| 3 | Explainable Taxonomy Classifier | Hierarchical Classpath (`Dept > Class > Fine`) and UNSPSC codes with multi-candidate ranking, matched terms, score, and tie-breaking explanation. | DONE |
| 4 | Attribute Extractor & LOV Validation | Extract specifications into 50 slot triplets strictly validated against canonical LOV dictionaries. | DONE |
| 5 | UOM & Fraction Standardization | 64th decimal-to-fraction converter (`50.25 in` → `50-1/4 in`), hyphenated mixed fractions, mandatory single space before unit (`1/2 in`, `120 V`, `200 psi`). | DONE |
| 6 | Verified-Only Description Engine | Assemble `INVOICE_DESC` ($\le 40$ chars ALL CAPS), `MOBILE_DESC` ($60\text{--}80$ chars), `SHORT_DESC`, `LONG_DESC1` strictly from verified evidence fields. | DONE |
| 7 | 252-Column Delivery Mapper | Construct all 252 target columns matching exact ordering and naming with formula injection defense (CWE-1236). | DONE |
| 8 | Field-Level Provenance & Evidence Model | Multi-record evidence lineage per field with source URL, source type, title, section/page citation, excerpt, method, timestamp, and confidence. | DONE |
| 9 | Manufacturer Evidence Ingestion Registry | Whitelisted official manufacturer URL and PDF parser with local SHA-256 storage, heading/page chunking, and MPN search. | DONE |
| 10 | Candidate vs Verified Identity Policy | Registry metadata treated as candidate identity (0.80); promoted to verified (0.98) only upon explicit mention in ingested document text. | DONE |
| 11 | Single Source of Truth Confidence Model | Documented component weights with explicit penalties for missing evidence, fallback taxonomy, LOV rejection, and source conflicts. | DONE |
| 12 | Field-Level Human-in-the-Loop Review Queue | Field triage with approve, edit, reject, and mark_unknown actions, immutable audit trail, and high-risk validation gating. | DONE |
| 13 | Live Evidence Inbox UI | Real-time view of `data/evidence/source_registry.json`, interactive chunk drawer, and live manufacturer source registration modal. | DONE |
| 14 | Responsive 3-Domain Evidence Workbench | Workspace (Catalog, Playground), Governance (Evidence Inbox, Review Queue, Validation & Benchmark), Delivery (252-Column Export). | DONE |
| 15 | Fittings End-to-End Featured Demo Flow | Preloaded SharkBite (`U008LFA`) and NIBCO (`NIB-607-1/2`) flows demonstrating candidate extraction, LOV normalization, unsupported withholding, and export. | DONE |
| 16 | Comprehensive 382-Test Regression Suite | 100% test pass rate across unit, integration, pairwise, boundary, workload, and security pentest suites. | DONE |
