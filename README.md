# 🚀 UniHack Simplifi — Industrial Product Intelligence & Evidence-Review Workbench

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React 18](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite-61DAFB.svg?logo=react&logoColor=black)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/Language-TypeScript-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Tests Passing](https://img.shields.io/badge/Tests-382%2F382%20Passed-10B981.svg)](https://pytest.org)
[![Schema 252](https://img.shields.io/badge/Schema-252%20Delivery%20Columns-8B5CF6.svg)](file:///data/output/enriched_catalog_252_columns.csv)

---

## 📌 Executive Summary

**UniHack Simplifi** is a provenance-first industrial product intelligence and PIM (Product Information Management) enrichment platform designed for B2B industrial distributor catalogs (tools, hardware, abrasives, plumbing fittings, faucets, electrical, building materials, and appliances).

Instead of relying on black-box LLM guessing or unverified scraping, UniHack Simplifi uses a **deterministic 7-stage enrichment pipeline**, a **strict official manufacturer source registry**, and a **field-level provenance model** to ensure that every enriched product attribute is supported by verifiable citations.

### Three Foundational Principles:
1. **What do we know?** — Extracted candidate specifications and normalized canonical entities.
2. **What is the evidence?** — Cryptographically hashed official manufacturer PDFs/pages with exact section/page citations.
3. **What needs review?** — Any ambiguous classification, conflicting value, or field lacking evidence is held in a field-level Human-in-the-Loop review queue. Unverified fields remain intentionally blank.

---

## 🏗️ System Architecture

```text
                               ┌─────────────────────────────────────────┐
                               │       Raw Supplier Feed (CSV)           │
                               │ [MPN, Part_Desc, Dummy Noise Tokens]   │
                               └────────────────────┬────────────────────┘
                                                    │
                                                    ▼
                               ┌─────────────────────────────────────────┐
                               │  Stage 1: Placeholder & Feed Sanitizer  │
                               │  (Strips '-- Unbranded --', casing)     │
                               └────────────────────┬────────────────────┘
                                                    │
                                                    ▼
                               ┌─────────────────────────────────────────┐
                               │  Stage 2: Entity & Brand Resolver       │
                               │  (UniCat index match, ® / ™ symbols)    │
                               └────────────────────┬────────────────────┘
                                                    │
                                                    ▼
┌───────────────────────────────┐  Stage 3: Explainable Taxonomy Engine  │
│  Official Manufacturer Store  │  (Multi-candidate ranking & tie-break) │
│  • Whitelisted PDF/HTML Docs  ├───────────────────┬────────────────────┘
│  • SHA-256 Cryptographic Hash │                   │
│  • Section / Heading Chunks   │                   ▼
└───────────────┬───────────────┘  Stage 4: Attribute Extraction & LOV   │
                │                  (6-step lifecycle: cand -> norm -> ev)│
                └───────────────────────────────────┬────────────────────┘
                                                    │
                                                    ▼
                               ┌─────────────────────────────────────────┐
                               │  Stage 5: UOM Standardizer              │
                               │  (Fraction formatting, spacing rules)   │
                               └────────────────────┬────────────────────┘
                                                    │
                                                    ▼
                               ┌─────────────────────────────────────────┐
                               │  Stage 6: Verified-Only Content Engine  │
                               │  (INVOICE <=40 CAPS, MOBILE 60-80 chars)│
                               └────────────────────┬────────────────────┘
                                                    │
                                                    ▼
                               ┌─────────────────────────────────────────┐
                               │  Stage 7: 252-Column Delivery Exporter  │
                               │  (Strict header matching, formula safe) │
                               └────────────────────┬────────────────────┘
                                                    │
                                                    ▼
                               ┌─────────────────────────────────────────┐
                               │  Human-in-the-Loop Field Review Queue   │
                               │  (Immutable audit trail, gate checks)   │
                               └─────────────────────────────────────────┘
```

---

## 🛡️ Field-Level Provenance & Evidence Ingestion

### 6-Step Evidence Lifecycle
1. **Extract Candidate Fact**: Extracted directly from official manufacturer HTML product pages or PDF technical specification sheets.
2. **Validate against LOV**: Checked against category-specific List of Values (LOV) dictionaries.
3. **Normalize UOM**: Standardized using Unilog UOM rules (`1/2 in`, `120 V`, `15 A`, `200 psi`).
4. **Record Lineage**: Attaches source URL, document title, section/page, text excerpt, extraction method, timestamp, and confidence.
5. **Reject Unsupported Facts**: Invalid candidate values are rejected with explicit audit flags.
6. **Preserve Candidate Value**: The original raw source string is stored separately from the normalized canonical value.

### Identity Verification Rule
```text
Registry Metadata = Candidate Identity (0.80 Confidence)
Explicit Document Mention = Verified Identity (0.98 Confidence)
UniCat Dictionary Match = Normalized Entity
```

---

## 🔍 Featured Demo: Fittings End-to-End Flow

To demonstrate the full power of traceable enrichment, UniHack Simplifi includes a pre-indexed **Fittings & Plumbing** showcase:

```text
Raw Supplier Input:
  "U008LFA 1/2IN BRASS PUSH COUPLING -- No Brand -- 200PSI LEAD FREE"
  ↓
Official Source:
  SharkBite 1/2-in Push-to-Connect Brass Straight Coupling Spec Sheet (SHA-256: 5734924d...)
  ↓
Extracted Candidate Attributes:
  • Fitting Type: "Coupling" (Verified · UniCat LOV)
  • Connection Type: "Push-to-Connect" (Verified · UniCat LOV)
  • Material: Raw "Lead-Free Brass" → Norm "Brass" (Verified · UniCat LOV)
  • Nominal Size: "1/2 in" (Verified · Unilog UOM)
  • Pressure Rating: "200 psi" (Verified)
  ↓
Unsupported Attributes Withheld:
  • Sound Level: <Blank> (No evidence in spec sheet → withheld as safety success state)
  • Voltage / Amps: <Blank> (Withheld)
  ↓
Generated Content (Verified-Only):
  • INVOICE_DESC: "CPLG BRS PUSH 1/2IN 200PSI" (26/40 chars, ALL CAPS)
  • MOBILE_DESC: "SharkBite 1/2 in Brass Push-to-Connect Straight Coupling 200 psi" (64 chars)
  • SHORT_DESC: "SharkBite® U008LFA 1/2 in Push-to-Connect Brass Straight Coupling 200 psi"
  ↓
Delivery Output:
  Row exported with 252 columns; verified fields populated, unknown fields blank.
```

---

## 📊 Benchmarking & Schema Validation

- **Deterministic Hard Gates**:
  - `INVOICE_DESC`: $\le 40$ characters, **100% ALL CAPS**.
  - `MOBILE_DESC`: Strictly **60 to 80 characters**.
  - `252 Delivery Columns`: 100% header preservation matching Unilog delivery format.
  - `Formula Injection Defense`: Sanitizes leading `=`, `+`, `-`, `@`, `\t` characters (CWE-1236).
- **Ground-Truth Calibration**:
  - The evaluation suite runs deterministic schema and hard-gate checks across all 252 delivery headers.
  - Exact match and token similarity metrics are calibrated against external labelled ground-truth workbooks upon ingestion.

---

## 🖥️ Interactive Workbench Architecture

The web application is organized into three operational domains:

- **WORKSPACE**:
  - `Catalog Explorer`: Searchable 1,000-SKU grid with keyword and semantic search modes, filterable by category, brand, and review state.
  - `Enrichment Playground`: Real-time interactive sandbox with 1-click presets (Fittings, Dishwashers, Cut-Off Discs) for sub-second rule testing.
- **GOVERNANCE**:
  - `Evidence Inbox`: Live manufacturer source registry displaying active PDF/HTML sources, SHA-256 hashes, retrieval dates, and discrete chunk inspection.
  - `Review Queue`: Field-level triage queue with approve, edit, reject, and "mark unknown" actions, backed by an immutable audit trail.
  - `Validation & Benchmark`: 252-column schema compliance monitoring and fill rate metrics.
- **DELIVERY**:
  - `Delivery Export`: One-click 252-column CSV and Excel (.xlsx) export.

---

## 📁 Structured Repository Layout

```text
.
├── docs/                         # 📚 Comprehensive Documentation
│   ├── api/                      # API Contracts & OpenAPI specs
│   │   └── API_CONTRACT.md
│   ├── architecture/             # System, Backend & Security Architecture
│   │   ├── ARCHITECTURE_SYSTEM_DESIGN.md
│   │   ├── BACKEND_ARCHITECTURE.md
│   │   └── SECURITY_MODEL.md
│   ├── operations/               # Operational Runbooks & Testing Infrastructure
│   │   ├── RUNBOOK.md
│   │   ├── TEST_INFRA.md
│   │   └── TEST_READY.md
│   └── specifications/           # Original Specs & Solution Guides
│       ├── ORIGINAL_REQUEST.md
│       ├── PROJECT.md
│       ├── UniHack_Solution_Guide.html
│       └── UniHack_Solution_Guide.md
├── src/                          # 🛠️ Application Source Code
│   ├── backend/                  # FastAPI REST Backend, DB Repositories & State
│   │   ├── db/                   # SQLite Migrations & Repositories
│   │   ├── jobs/                 # Persistent Batch Enrichment Engine
│   │   ├── routes/               # Modular API Routers (Auth, Catalog, Evidence, Export, Review)
│   │   └── state.py              # In-Memory Index + SQLite WAL Synchronization
│   ├── benchmark/                # Ground-Truth Evaluator & Metric Scorers
│   ├── evidence/                 # Acquisition, PDF Parsing, Security & Gemini Provider
│   ├── frontend/                 # React 18 + TypeScript + Vite Dashboard
│   └── pipeline/                 # 7-Stage Deterministic Industrial Enrichment Engine
├── data/                         # 💾 Persistent Data & Dictionaries
│   ├── cache/                    # Extraction & RAG Caches
│   ├── dictionaries/             # LOV, UOM, Brand & Taxonomy Dictionaries
│   ├── evidence/                 # Raw & Processed Manufacturer Documents
│   ├── ground_truth/             # Reference Ground-Truth Datasets
│   ├── output/                   # Enriched 252-Column Exports & Benchmark Reports
│   └── raw/                      # Raw Supplier Feeds
├── scripts/                      # ⚡ Standalone CLI Tools & Automations
│   ├── build_rag_index.py        # Neural Embedding Vector Indexer
│   ├── e2e_browser_test.py       # Playwright UI Verification
│   ├── run_benchmark.py          # Benchmark Runner CLI
│   ├── run_pipeline.py           # Batch Catalog Processing CLI
│   └── security_audit.py         # Static & Runtime Security Auditor
└── tests/                        # 🧪 449+ Automated Pytest Test Cases
    ├── adversarial/              # Penetration, SSRF & Injection Tests
    ├── e2e/                      # End-to-End Workflow & Boundary Tests
    ├── integration/              # FastAPI Endpoint & Pipeline Integration Tests
    └── unit/                     # Focused Component & Provenance Unit Tests
```

---

## ⚡ Quick Start & Verification

### Local Development
```bash
# 1. Activate Python virtual environment & install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Run comprehensive test suite (449+ tests)
pytest tests/ -v

# 3. Build frontend assets
cd src/frontend
npm install
npm run build
cd ../..

# 4. Start FastAPI server (serves API & frontend on port 8000)
python -m uvicorn src.backend.main:app --host 0.0.0.0 --port 8000
```

### Docker Compose
```bash
docker compose build
docker compose up
```

Access the workbench at **`http://localhost:8000`** (or **`http://localhost:5173`** for Vite live-reload).  
Default credentials: `admin@unilog.com` / `Admin@123456`

