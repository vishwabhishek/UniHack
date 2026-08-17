# Survey Report: System Architecture, QA Benchmark Suite & Interactive PIM Dashboard

**Project**: UniHack Industrial Product Intelligence & PIM Enrichment Platform  
**Agent**: Explorer 3 (System Architecture, QA & UI Specialist)  
**Date**: 2026-08-16  
**Status**: Comprehensive Survey Complete  

---

## 1. Executive Summary & Scope Overview

The UniHack Industrial Product Intelligence & PIM Enrichment Platform is an enterprise-grade solution designed to transform noisy, unstructured, and heavily abbreviated industrial distributor catalog data into fully normalized, taxonomy-classified, attribute-extracted, and 5-tier described product records across the strict Unilog 252-column delivery standard.

This survey provides the complete architectural blueprint, mathematical definitions, API contracts, UI component hierarchy, runtime environment verification, and directory layout for:
1. **R2: Ground-Truth Benchmarking & Quality Assurance Suite**: A rigorous, multi-metric evaluation harness that validates pipeline enrichment against ground truth across all 252 columns, character limits, LOV compliance, and anomaly triggers.
2. **R3: Interactive PIM & Product Intelligence Dashboard**: A modern, high-performance React + TypeScript single-page application powered by a robust Python FastAPI backend, featuring a 1,000-item Catalog Grid, a Side-by-Side Visual Diff Inspector, a Real-Time Interactive Playground / Sandbox, a Human-in-the-Loop (HITL) Review Queue, and a 1-click 252-column CSV/Excel Exporter.
3. **System Architecture & Modular Layout**: An enterprise-grade directory structure separating pipeline stages, benchmarking, backend services, frontend presentation, and comprehensive unit/integration test suites.

---

## 2. Ground-Truth Benchmarking & Quality Assurance Suite (R2)

### 2.1 Complete Metric Mathematical Formulations

To ensure rigorous quality assurance, the benchmarking suite evaluates pipeline outputs against ground truth (`Unihack_ Expected Output - Delivery Format.csv`) across multiple orthogonal dimensions:

```
+---------------------------------------------------------------------------------------+
|                               GROUND-TRUTH QA SUITE                                   |
+---------------------------------------------------------------------------------------+
|  1. Exact Match & Normalized Equality (All 252 columns)                               |
|  2. Token & Edit Similarity: Levenshtein, Token Jaccard, Token Cosine                 |
|  3. NLP Evaluation Metrics: Sentence BLEU-1/2/4, ROUGE-1/2/L                         |
|  4. Hard Rule Constraints: INVOICE_DESC <=40 (ALL CAPS), MOBILE_DESC 60-80            |
|  5. Controlled Vocabulary (LOV) Adherence: 0% Hallucination Verification              |
|  6. Missing Field Rate & Triplet Attribute F1 (Label, Value, UOM)                     |
|  7. Composite Confidence Scoring & Automated Anomaly Detection Engine                 |
+---------------------------------------------------------------------------------------+
```

#### A. Exact Match & Normalized Equality
For any field $k \in \{1, \dots, 252\}$ across $N$ evaluated records:
- **Exact Match Rate**:
  $$\text{EM}(k) = \frac{1}{N} \sum_{i=1}^N \mathbb{I}(y_{i, k} = \hat{y}_{i, k})$$
- **Normalized Match Rate** (case-folded, whitespace-collapsed, punctuation-normalized):
  $$\text{NEM}(k) = \frac{1}{N} \sum_{i=1}^N \mathbb{I}(\text{norm}(y_{i, k}) = \text{norm}(\hat{y}_{i, k}))$$

#### B. Character-Level Normalized Levenshtein Similarity
For description strings $s_1$ (ground truth) and $s_2$ (pipeline generated):
$$\text{Sim}_{\text{Lev}}(s_1, s_2) = 1 - \frac{\text{LevenshteinDistance}(s_1, s_2)}{\max(|s_1|, |s_2|)}$$
Where $\text{Sim}_{\text{Lev}} \in [0, 1]$, with $1.0$ representing identity.

#### C. Token Jaccard & Cosine Similarity
- **Token Jaccard Similarity**:
  $$\text{Jaccard}(T_1, T_2) = \frac{|T_1 \cap T_2|}{|T_1 \cup T_2|}$$
  where $T_1 = \text{tokens}(s_1)$ and $T_2 = \text{tokens}(s_2)$.
- **Token Cosine Similarity**:
  $$\text{Cosine}(\mathbf{v}_1, \mathbf{v}_2) = \frac{\mathbf{v}_1 \cdot \mathbf{v}_2}{\|\mathbf{v}_1\|_2 \|\mathbf{v}_2\|_2}$$
  using sub-word or unigram TF-IDF vector representations.

#### D. NLP Evaluation Metrics: Sentence BLEU & ROUGE
- **Sentence BLEU-n** (n-gram precision with brevity penalty):
  $$\text{BLEU} = \text{BP} \cdot \exp\left( \sum_{n=1}^N w_n \ln p_n \right)$$
  $$\text{BP} = \begin{cases} 1 & \text{if } c > r \\ \exp(1 - r/c) & \text{if } c \le r \end{cases}$$
  where $c$ is candidate length, $r$ is reference length, and $p_n$ is modified $n$-gram precision.
- **ROUGE-1, ROUGE-2, ROUGE-L** (Recall, Precision, and F1):
  $$\text{ROUGE-N}_{\text{Recall}} = \frac{\sum_{S \in \{\text{Refs}\}} \sum_{\text{gram}_n \in S} \text{Count}_{\text{match}}(\text{gram}_n)}{\sum_{S \in \{\text{Refs}\}} \sum_{\text{gram}_n \in S} \text{Count}(\text{gram}_n)}$$
  $$\text{ROUGE-L} = \frac{(1 + \beta^2) R_{\text{LCS}} P_{\text{LCS}}}{R_{\text{LCS}} + \beta^2 P_{\text{LCS}}}$$
  measuring Longest Common Subsequence (LCS) overlap for long descriptions and marketing copy.

---

### 2.2 Hard Constraint Verification & Gate Rules

The benchmarking suite enforces strict binary pass/fail gates on critical output fields:

| Field | Rule 1: Length Constraint | Rule 2: Casing & Character Set | Target Compliance |
|---|---|---|---|
| `INVOICE_DESC` | $\text{Length}(s) \le 40$ characters | $\text{upper}(s) == s$ (ALL CAPS, no lowercase) | **100.0%** (0 tolerance) |
| `MOBILE_DESC` | $60 \le \text{Length}(s) \le 80$ characters | Proper casing, standard punctuation | **100.0%** (0 tolerance) |
| `SHORT_DESC` | Concise title structure | `[Brand] [Series] [MPN] [Item Type], [Specs]` | $\ge 95.0\%$ |
| `LONG_DESC1` | Detailed spec sentence | Normalized UOMs, comma-separated clauses | $\ge 95.0\%$ |
| UOM Spacing | Mandatory space between number and unit (`24 in`, `120 V`, `15 A`, `47 dBA`) | Standard abbreviations (no `inches`, `IN.`, `amps`, `volts`) | **100.0%** |
| UOM Fractions | Decimal inches converted to hyphenated fractions (`50-1/4 in`, `33-7/16 in`) | No raw decimals for standard fractional inches | **100.0%** |

---

### 2.3 Controlled Vocabulary (LOV) Adherence & Zero Hallucinations

Industrial catalog buyers cannot tolerate hallucinated specs. The evaluation suite validates all extracted attributes against the canonical List of Values (LOV) dictionary:

- **Hallucination Rate Calculation**:
  $$\text{HallucinationRate} = \frac{\sum_{i=1}^N |\{v \in \text{ExtractedValues}(i) : v \notin \text{CanonicalLOV}(\text{Classpath}_i)\}|}{\sum_{i=1}^N |\text{ExtractedValues}(i)|} \times 100\%$$
- **Target**: **0.0% Hallucinations**.
- **LOV Consistency Metric**:
  - Attribute Label validity: $100\%$ match against canonical attribute labels for that Classpath.
  - Attribute Value validity: $100\%$ match against canonical normalized values in LOV.
  - Attribute UOM validity: $100\%$ match against master UOM abbreviations.

---

### 2.4 Dynamic Triplet Attribute Evaluation (Columns 55–204)

In the Unilog standard, attributes are delivered as up to 50 ordered triplets:
`ATTRIBUTE_LABEL i`, `ATTRIBUTE_VALUE i`, `ATTRIBUTE_UOM i` for $i \in [1, 50]$ (150 total columns).

The benchmark evaluates triplet extraction as a structured set-matching problem:
- **Set of Expected Triplets**: $E_i = \{(L_j, V_j, U_j)\}_{j=1}^{K_{e}}$
- **Set of Predicted Triplets**: $P_i = \{(L_m, V_m, U_m)\}_{m=1}^{K_{p}}$
- **Precision**: $\text{Prec} = \frac{|P_i \cap E_i|}{|P_i|}$
- **Recall**: $\text{Rec} = \frac{|P_i \cap E_i|}{|E_i|}$
- **Triplet F1-Score**: $\text{F1} = \frac{2 \cdot \text{Prec} \cdot \text{Rec}}{\text{Prec} + \text{Rec}}$

---

### 2.5 Multi-Factor Composite Confidence Scoring Model

Every processed item receives a deterministic, transparent composite confidence score $C \in [0, 1]$ calculated from 5 sub-scores:

$$C_{\text{composite}} = w_{\text{brand}} C_{\text{brand}} + w_{\text{tax}} C_{\text{tax}} + w_{\text{attr}} C_{\text{attr}} + w_{\text{desc}} C_{\text{desc}} + w_{\text{comp}} C_{\text{comp}}$$

**Default Weight Distribution**:
- $w_{\text{brand}} = 0.20$: Brand & Manufacturer resolution confidence (exact dictionary match = 1.0, high fuzzy match = 0.85–0.95, unresolvable = 0.30).
- $w_{\text{tax}} = 0.20$: Taxonomy & UNSPSC classification confidence (depth of matched leaf node).
- $w_{\text{attr}} = 0.25$: Attribute extraction density and LOV compliance percentage.
- $w_{\text{desc}} = 0.20$: 5-tier description generation completeness and structure validity.
- $w_{\text{comp}} = 0.15$: Hard constraint compliance (length limits, casing, UOM formatting).

---

### 2.6 Automated Anomaly Detection & Flagging Engine

The anomaly detection engine automatically categorizes items into one of 4 workflow statuses:

```
[Raw Input] ---> [Enrichment Pipeline] ---> [Anomaly Detection Engine]
                                                     |
                 +-------------------+---------------+-------------------+
                 |                   |                                   |
                 v                   v                                   v
           [Validated]           [Enriched]                     [Needs Human Review / Flagged]
        (Confidence >= 0.95, (Confidence >= 0.85,             (Confidence < 0.85 OR Anomaly Flags)
         All Rules Pass)      No Hard Errors)                              |
                                                                           v
                                                                 [HITL Review Queue]
```

**Anomaly Triggers**:
1. `LOW_CONFIDENCE`: Composite score $C < 0.85$.
2. `INVOICE_DESC_LENGTH_OVERFLOW`: Length $> 40$ chars.
3. `INVOICE_DESC_CASING_ERROR`: Contains lowercase characters.
4. `MOBILE_DESC_LENGTH_OUT_OF_BOUNDS`: Length $< 60$ or $> 80$ chars.
5. `UNRESOLVED_BRAND`: Raw brand was placeholder (`-- Unbranded --`) and no confident brand could be extracted.
6. `MANUFACTURER_BRAND_MISMATCH`: Brand resolved does not map to Manufacturer code or known distributor affiliate.
7. `UNRECOGNIZED_LOV_VALUE`: Attribute extracted but value fails canonical LOV validation.
8. `MISSING_CORE_ATTRIBUTES`: Missing required attributes for the specific fine category.

---

### 2.7 Benchmark Suite Report Output Schema

The benchmark runner outputs both a machine-readable JSON report and a rich Markdown summary:

```json
{
  "timestamp": "2026-08-16T17:00:00Z",
  "dataset_summary": {
    "total_evaluated": 200,
    "total_columns": 252
  },
  "overall_scores": {
    "exact_match_rate": 0.884,
    "normalized_match_rate": 0.942,
    "average_levenshtein_similarity": 0.931,
    "average_bleu_score": 0.865,
    "average_rouge_l_f1": 0.892,
    "invoice_desc_compliance_rate": 1.000,
    "mobile_desc_compliance_rate": 1.000,
    "lov_adherence_rate": 1.000,
    "triplet_attribute_f1": 0.915,
    "average_confidence": 0.918
  },
  "hard_rule_gates": {
    "invoice_desc_le_40_caps": {"passed": true, "compliance": "100.0%"},
    "mobile_desc_60_to_80": {"passed": true, "compliance": "100.0%"},
    "lov_zero_hallucinations": {"passed": true, "hallucination_rate": "0.0%"}
  },
  "anomaly_summary": {
    "total_flagged": 14,
    "flagged_percentage": 7.0,
    "breakdown": {
      "LOW_CONFIDENCE": 8,
      "UNRESOLVED_BRAND": 4,
      "MISSING_CORE_ATTRIBUTES": 2
    }
  },
  "column_metrics": [
    {
      "column_name": "INVOICE_DESC",
      "exact_match": 0.895,
      "levenshtein": 0.941,
      "length_compliance_rate": 1.000
    },
    {
      "column_name": "MOBILE_DESC",
      "exact_match": 0.870,
      "bleu": 0.882,
      "length_compliance_rate": 1.000
    }
  ]
}
```

---

## 3. Interactive PIM & Product Intelligence Dashboard (R3)

### 3.1 Frontend Architecture & Component Hierarchy

The frontend is a modern, responsive Single-Page Application built with **React 18 + TypeScript + Vite + Tailwind CSS**, styled with sleek dark/light modern aesthetics, high-contrast badges, real-time diff highlighters, and Lucide icons.

```
src/frontend/
├── index.html
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
├── package.json
└── src/
    ├── main.tsx                      # App entry point
    ├── App.tsx                       # Tab navigation & global layout
    ├── types/
    │   ├── product.ts                # RawProduct, EnrichedProduct, TripletAttribute
    │   ├── benchmark.ts              # Metric models, EvaluationSummary
    │   └── api.ts                    # ApiResponse, PaginationParams
    ├── api/
    │   └── client.ts                 # Typed Axios / Fetch REST client
    ├── components/
    │   ├── layout/
    │   │   ├── Navbar.tsx            # Global logo, theme toggle, system status
    │   │   ├── MetricsBanner.tsx     # Live KPI counters (Total, Enriched %, Accuracy, HITL Queue)
    │   │   └── TabNavigation.tsx     # 5 Core tabs navigation
    │   ├── catalog/
    │   │   ├── CatalogExplorer.tsx   # Search, multi-filters, pagination container
    │   │   ├── ProductTable.tsx      # Virtualized / paginated data grid (1,000 items)
    │   │   ├── ProductRow.tsx        # Row with status badges, quick actions
    │   │   ├── StatusBadge.tsx       # Draft, Enriched, Validated, Flagged
    │   │   └── FilterSidebar.tsx     # Dept/Class/Fine tree, Brand filter, Confidence slider
    │   ├── inspector/
    │   │   ├── SideBySideModal.tsx   # Split-screen raw vs enriched inspector modal
    │   │   ├── RawInputViewer.tsx    # Raw distributor card with placeholder callouts
    │   │   ├── DescriptionTiers.tsx  # 5-tier cards with length counters & badge tags
    │   │   ├── DynamicAttributes.tsx # 50-triplet Key-Value-UOM interactive table
    │   │   ├── TaxonomyCard.tsx      # Classpath breadcrumb & UNSPSC tag
    │   │   └── ConfidenceMeter.tsx   # Radial & progress bar confidence breakdown
    │   ├── playground/
    │   │   ├── PlaygroundView.tsx    # Live interactive transformation sandbox
    │   │   ├── RawInputForm.tsx      # Multi-field distributor input form + presets
    │   │   ├── PresetSelector.tsx    # Preloaded sample buttons (Dishwasher, Sanding belt, etc.)
    │   │   ├── StepByStepTimeline.tsx# 6-step transformation pipeline visualizer
    │   │   └── LivePreviewCard.tsx   # Instant 5-tier & 252-column live preview
    │   ├── hitl/
    │   │   ├── ReviewQueueView.tsx   # Dedicated queue for items with confidence < 0.85
    │   │   ├── ReviewCard.tsx        # Compact card showing anomaly reasons
    │   │   ├── EditProductModal.tsx  # In-place editor for descriptions & attributes
    │   │   └── ApprovalToolbar.tsx   # "Approve & Mark Validated", "Re-run AI", "Discard"
    │   ├── benchmark/
    │   │   ├── BenchmarkView.tsx     # QA evaluation analytics dashboard
    │   │   ├── MetricScoreCard.tsx   # BLEU, ROUGE, Exact Match, LOV Adherence cards
    │   │   ├── ComplianceGuages.tsx  # 100% Invoice & Mobile Desc compliance gauges
    │   │   ├── ConfusionMatrix.tsx   # Category classification accuracy matrix
    │   │   └── ColumnMetricTable.tsx # Searchable 252-column accuracy breakdown
    │   ├── export/
    │   │   ├── ExportModal.tsx       # CSV & Excel 252-column export configuration
    │   │   └── DataPreviewTable.tsx  # First 10 rows export preview table
    │   └── ui/                       # Reusable primitives (Buttons, Modals, Badges, Tooltips)
    │       ├── Button.tsx
    │       ├── Card.tsx
    │       ├── Modal.tsx
    │       ├── Badge.tsx
    │       └── Input.tsx
    └── styles/
        └── globals.css
```

---

### 3.2 Key Dashboard Modules & User Experience

#### Tab 1: Catalog Explorer & Product Grid
- Displays all 1,000 items in a lightning-fast data table.
- Search across MPN, Part Description, Manufacturer, and Brand with debounced query.
- Multi-faceted filtering:
  - Workflow Status (`All`, `Validated`, `Enriched`, `Needs Human Review`, `Draft`)
  - Department / Category hierarchy drilldown
  - Brand filter (multi-select)
  - Minimum Confidence threshold slider (0.0 to 1.0)
- Columns shown: SKU / Part Number, MPN, Brand, Canonical Classpath, INVOICE_DESC (with char count), MOBILE_DESC (with char count), Confidence Score, Status Badge, Quick Inspect Action.

#### Tab 2: Side-by-Side Transformation Inspector
- Split-screen comparison:
  - **Left Pane (Raw Supplier Input)**:
    - Raw MPN, Supplier Name, Raw `Part_Desc`.
    - Highlighted dummy placeholders (`-- Unbranded --`, `-- No Unilog Brand --`).
  - **Right Pane (Canonical PIM Enrichment)**:
    - Resolved Manufacturer & Brand with legal casing and `®`/`™` symbols.
    - Classpath breadcrumb + UNSPSC Code.
    - **5-Tier Content Accordion**:
      1. `INVOICE_DESC` (with pill `38/40 chars`, `ALL CAPS` indicator).
      2. `MOBILE_DESC` (with pill `75/80 chars`, `Within 60-80` check).
      3. `SHORT_DESC` (with copy button).
      4. `LONG_DESC1` (full spec sentence).
      5. `RETAIL_DESC` / `MARKETING_DESCRIPTION`.
    - Dynamic Attributes Table (Label, Value, UOM, Filterable flag).
    - Media Assets preview (Product Image filename, Spec sheet link).
  - **Bottom / Drawer Panel**:
    - Multi-factor Confidence Radar / Score Breakdown.
    - Anomaly warnings list (if any).

#### Tab 3: Interactive Playground / Sandbox ("Judge's Testing Arena")
- Allows judges to paste any arbitrary messy distributor string (or click 1-click presets: *Frigidaire Dishwasher*, *Diablo Sanding Belt*, *Milwaukee Blade*, *Trex Decking*).
- Sub-second pipeline execution displaying visual step-by-step cards:
  1. `[Sanitizer]`: Strips placeholder flags, normalizes whitespace.
  2. `[Entity Resolver]`: Resolves canonical Brand and Manufacturer.
  3. `[Taxonomy Classifier]`: Assigns Classpath and UNSPSC code.
  4. `[Attribute Extractor]`: Extracts key specs constrained to LOV and normalizes UOMs.
  5. `[Description Generator]`: Constructs all 5 tiers of descriptions.
  6. `[Delivery Serializer]`: Compiles the record into the 252-column schema.

#### Tab 4: Human-in-the-Loop (HITL) Review Queue
- Automatically populates with products where Confidence $< 0.85$ or Anomaly Flags are present.
- Shows clear reason pills (e.g. `[Unresolved Brand]`, `[Low Confidence 0.72]`, `[Missing Spec]`).
- Inline modal editor allowing content managers to:
  - Override resolved Brand or Manufacturer.
  - Tweak generated descriptions (with live character counter feedback).
  - Add or correct dynamic attribute values with LOV autocomplete.
  - Click **"Approve for Delivery"** (updates status to `Validated` and logs HITL audit trail).

#### Tab 5: Ground-Truth QA Benchmark Center
- Executive dashboard summarizing model accuracy against the 200 ground-truth rows.
- Visual gauges for 100% Invoice Desc and Mobile Desc compliance.
- Interactive per-column accuracy table across all 252 delivery headers.
- Downloadable benchmark evaluation report in JSON and Markdown formats.

#### Global: 252-Column Delivery Exporter
- Header action button accessible from anywhere in the app.
- Exports the active or filtered catalog into the exact 252-column CSV or Excel file matching Unilog specifications.

---

## 4. FastAPI Backend Architecture & REST API Specification

### 4.1 Backend Architecture

The backend is built with **FastAPI** (Python 3.12) running under **Uvicorn**, providing asynchronous endpoint handling, automatic Pydantic v2 validation, OpenAPI/Swagger documentation (`/docs`), and streaming export capabilities.

```
src/backend/
├── __init__.py
├── main.py                     # FastAPI application factory, CORS, router inclusion
├── config.py                   # App settings, file paths, CORS origins
├── schemas/
│   ├── __init__.py
│   ├── product.py              # RawProduct, EnrichedProduct252, ProductListItem
│   ├── playground.py           # TransformRequest, TransformStepResult, TransformResponse
│   ├── hitl.py                 # ProductUpdateRequest, ApprovalResponse
│   └── benchmark.py            # BenchmarkSummaryResponse, ColumnMetricResponse
├── services/
│   ├── __init__.py
│   ├── catalog_service.py      # In-memory fast index, pagination, filtering, search
│   ├── pipeline_service.py     # Invocation bridge to src.pipeline modules
│   ├── benchmark_service.py    # Ground truth evaluator and metric cache
│   └── export_service.py       # 252-column CSV / Excel stream builder
└── api/
    ├── __init__.py
    ├── catalog.py              # /api/catalog endpoints
    ├── playground.py           # /api/playground endpoints
    ├── hitl.py                 # /api/hitl endpoints
    ├── benchmark.py            # /api/benchmark endpoints
    └── export.py               # /api/export endpoints
```

---

### 4.2 Complete REST API Endpoints Specification

| Endpoint | Method | Purpose | Request Body | Response Payload |
|---|---|---|---|---|
| `/api/health` | `GET` | System health, environment, dataset stats | None | `{"status": "ok", "total_records": 1000, "enriched": 1000, "flagged": 14}` |
| `/api/catalog` | `GET` | Paginated catalog list with search & filters | Query params: `page`, `page_size`, `q`, `status`, `dept`, `brand`, `min_confidence` | `{"items": [...], "total": 1000, "page": 1, "page_size": 25, "pages": 40}` |
| `/api/catalog/{id}` | `GET` | Single product full 252-column detail | Path param: `id` (SKU or index) | Complete 252-column object + raw input + confidence breakdown + anomaly flags |
| `/api/catalog/{id}` | `PUT` | HITL edit product attributes/descriptions | `ProductUpdateRequest` | Updated product record |
| `/api/catalog/{id}/approve` | `POST` | Approve flagged item -> `Validated` | `{"notes": "optional reviewer comment"}` | `{"success": true, "status": "Validated", "id": "..."}` |
| `/api/catalog/{id}/flag` | `POST` | Manually flag product for review | `{"reason": "string"}` | `{"success": true, "status": "Flagged", "id": "..."}` |
| `/api/playground/transform` | `POST` | Real-time pipeline execution for arbitrary text | `{"part_desc": "...", "mfg_part_num": "...", "part_manuf": "..."}` | Step-by-step intermediate output + 5 tiers + 252-col output + confidence |
| `/api/pipeline/run-batch` | `POST` | Trigger batch enrichment of full 1,000 items | None | `{"job_id": "...", "status": "completed", "processed": 1000}` |
| `/api/benchmark/summary` | `GET` | Ground-truth QA benchmark metrics summary | None | `BenchmarkSummaryResponse` (Exact match, BLEU, ROUGE, compliance rates) |
| `/api/benchmark/field-breakdown`| `GET` | Per-column metrics across all 252 headers | None | `{"columns": [{"name": "INVOICE_DESC", "exact_match": 0.89, ...}]}` |
| `/api/export/csv` | `GET` | Stream 252-column CSV download | Query params: `status`, `search` (optional) | `text/csv` attachment `unilog_enriched_catalog_252.csv` |
| `/api/export/excel` | `GET` | Stream 252-column Excel (.xlsx) download | Query params: `status`, `search` (optional) | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |

---

### 4.3 High-Performance In-Memory Data Store & Search

To ensure sub-second response times for the 1,000-item catalog grid without requiring external database dependencies (like PostgreSQL), the backend utilizes an in-memory indexed Python data store:
- **Indexing**: Inverted token index for fuzzy substring search over `Mfg_Part_Num`, `Part_Desc`, `BRAND_NAME`, and `MANUFACTURER_NAME`.
- **Filtering**: Multi-index sets on `status`, `Dept`, `Class`, `Fine`, and `BRAND_NAME` for $O(1)$ set-intersection filtering.
- **Persistence**: Loads precomputed enrichment results from `data/output/enriched_catalog_252.csv` on boot, with atomic in-memory mutation on HITL updates and background file sync.

---

## 5. System Environment & Runtime Capabilities

### 5.1 Host Environment Audit

An automated environment check was conducted on the host system:

| Component | Installed Version | Status | Notes |
|---|---|---|---|
| **Operating System** | Linux (x86_64) | Ready | Full shell / bash execution access |
| **Python** | `Python 3.12.3` | Ready | Available at `/usr/bin/python3` |
| **Python Virtual Environment** | `uv 0.12.3` | Ready | Ultra-fast package management via `/home/abhishek-vishwakarma/.local/bin/uv` |
| **Node.js** | `v24.19.0` | Ready | Modern LTS Node environment |
| **npm** | `11.17.0` | Ready | Fast package installer and runner |
| **Git** | `git 2.43.0` | Ready | Available at `/usr/bin/git` |

### 5.2 Network Ports & Process Isolation

Port availability was tested and verified:
- **Port 8000**: **Free** (designated for FastAPI backend).
- **Port 5173**: **Free** (designated for Vite React frontend dev server).
- **Port 3000**: **Free** (alternative frontend port).

### 5.3 Unified Single-Command Startup Strategy

To fulfill the acceptance criterion *"Web application runs locally with a single command and loads cleanly"*, a unified runner script `scripts/start_all.sh` will orchestrate the startup:
1. Initializes Python environment via `uv venv` and installs dependencies.
2. Installs frontend npm packages (`npm install`).
3. Launches FastAPI backend on port 8000.
4. Launches Vite frontend on port 5173 with API proxying to `http://localhost:8000`.
5. Outputs clean console instructions and URL access points.

---

## 6. Recommended Directory & Modular Codebase Layout

```
/home/abhishek-vishwakarma/Documents/Hackathons/Unilog/
├── data/
│   ├── raw/
│   │   └── Unihack_ Sample Dataset - Input.csv               # 1,000 raw supplier records
│   ├── ground_truth/
│   │   └── Unihack_ Expected Output - Delivery Format.csv    # 252-column ground truth
│   ├── master_data/
│   │   ├── brands_manufacturers.json                         # Canonical brand/mfr lookup
│   │   ├── taxonomy_unspsc.json                              # Dept > Class > Fine & UNSPSC
│   │   ├── lov_dictionaries.json                             # Canonical attribute List of Values
│   │   └── uom_standards.json                                # Approved abbreviations & fractions
│   └── output/
│       ├── enriched_catalog_252.csv                          # 1,000 processed 252-column catalog
│       ├── benchmark_report.json                             # QA metrics JSON
│       └── benchmark_summary.md                              # QA summary report
├── src/
│   ├── pipeline/                                             # R1: Multi-Stage Enrichment Engine
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── models.py                                         # Pydantic schemas for products & attributes
│   │   ├── preprocessor.py                                   # Placeholder cleaner & sanitizer
│   │   ├── entity_resolver.py                                # Canonical brand/mfr entity resolution
│   │   ├── taxonomy_classifier.py                            # Classpath & UNSPSC classifier
│   │   ├── attribute_extractor.py                            # Spec extractor constrained to LOV
│   │   ├── uom_normalizer.py                                 # Decimal-to-fraction & UOM standardizer
│   │   ├── description_generator.py                          # 5-tier description builders
│   │   ├── confidence_scorer.py                              # Multi-factor confidence & anomaly detector
│   │   ├── exporter_252.py                                   # 252-column serializer
│   │   └── orchestrator.py                                   # Full pipeline runner
│   ├── benchmark/                                            # R2: Ground-Truth QA Suite
│   │   ├── __init__.py
│   │   ├── metrics.py                                        # BLEU, ROUGE, Levenshtein, exact match, compliance
│   │   ├── evaluator.py                                      # Evaluator against 252-col ground truth
│   │   └── report_generator.py                               # JSON & Markdown report generator
│   ├── backend/                                              # R3: FastAPI REST API
│   │   ├── __init__.py
│   │   ├── main.py                                           # FastAPI application entrypoint
│   │   ├── config.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── product.py
│   │   │   ├── playground.py
│   │   │   └── benchmark.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── catalog_service.py
│   │   │   ├── pipeline_service.py
│   │   │   └── export_service.py
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── catalog.py
│   │       ├── playground.py
│   │       ├── hitl.py
│   │       ├── benchmark.py
│   │       └── export.py
│   └── frontend/                                             # R3: React + TypeScript UI
│       ├── package.json
│       ├── vite.config.ts
│       ├── tsconfig.json
│       ├── tailwind.config.js
│       ├── index.html
│       └── src/
│           ├── main.tsx
│           ├── App.tsx
│           ├── types/
│           ├── api/
│           ├── components/
│           │   ├── layout/
│           │   ├── catalog/
│           │   ├── inspector/
│           │   ├── playground/
│           │   ├── hitl/
│           │   ├── benchmark/
│           │   ├── export/
│           │   └── ui/
│           └── styles/
├── tests/                                                    # Comprehensive 4-Tier Test Suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_preprocessor.py
│   │   ├── test_entity_resolver.py
│   │   ├── test_attribute_extractor.py
│   │   ├── test_uom_normalizer.py
│   │   └── test_description_generator.py
│   ├── integration/
│   │   ├── test_pipeline_orchestrator.py
│   │   ├── test_benchmark_suite.py
│   │   └── test_backend_api.py
│   ├── e2e/
│   │   ├── test_full_catalog_enrichment.py
│   │   └── test_export_delivery_252.py
│   └── adversarial/
│       ├── test_malformed_inputs.py
│       └── test_character_overflow_gates.py
├── scripts/
│   ├── run_pipeline.py                                       # CLI: Run pipeline on 1,000 items
│   ├── run_benchmark.py                                      # CLI: Run QA benchmark & write reports
│   ├── start_backend.sh                                      # Launch FastAPI server
│   ├── start_frontend.sh                                     # Launch Vite dev server
│   └── start_all.sh                                          # Single-command stack launcher
├── pyproject.toml / requirements.txt
├── README.md
└── PROJECT.md
```

---

## 7. Implementation Roadmap & Integration Milestones

```
+---------------------------------------------------------------------------------------+
| PHASE 0: Survey & Specification (Complete)                                            |
|   - Explorer 1: Schema & Data Mapping                                                 |
|   - Explorer 2: Transformation Rules & LOV Logic                                      |
|   - Explorer 3: System Architecture, QA Suite & Dashboard UI                          |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| PHASE 1: Core Enrichment Pipeline Engine (M1)                                         |
|   - Preprocessor -> Entity Resolver -> Taxonomy -> Attribute Extractor ->             |
|     UOM Normalizer -> 5-Tier Description Generator -> 252-Column Serializer            |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| PHASE 2: Ground-Truth QA & Benchmarking Suite (M2)                                    |
|   - Exact Match, Levenshtein, BLEU, ROUGE-L, 100% Hard Gate Evaluators,               |
|     0% LOV Hallucination Gate, Anomaly Detector, Report Serializer                    |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| PHASE 3: FastAPI Backend & Interactive React Dashboard UI (M3)                        |
|   - FastAPI REST Endpoints (Catalog, Playground, HITL, Export, Benchmark)             |
|   - React/TS UI (Grid, Side-by-Side Inspector, Playground, Review Queue, Exporter)    |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
| PHASE 4: 100% E2E Verification & Hardening (M4)                                       |
|   - Run full 1,000 items, verify 252 columns, verify 100% character limits,           |
|     execute test suite, verify single-command startup                                 |
+---------------------------------------------------------------------------------------+
```

---

## 8. Conclusion

The system architecture, evaluation suite, backend services, and interactive dashboard specified in this survey provide a robust, mathematically sound, and user-centric foundation for the UniHack Industrial Product Intelligence platform. With verified environment capabilities (Python 3.12, Node v24, uv, npm, free ports 8000/5173), the project is primed for seamless implementation across all milestones.
