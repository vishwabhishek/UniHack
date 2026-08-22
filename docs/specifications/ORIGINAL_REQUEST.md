# Original User Request

## 2026-08-16T11:22:03Z

<USER_REQUEST>
Build an end-to-end AI-powered Industrial Product Intelligence & PIM (Product Information Management) enrichment pipeline, ground-truth evaluation suite, and interactive web dashboard for industrial distributor catalogs (UniHack).

Working directory: /home/abhishek-vishwakarma/Documents/Hackathons/Unilog
Integrity mode: development

## Requirements

### R1. Multi-Stage Product Catalog Enrichment Engine (Python)
- **Ingestion & Placeholder Sanitizer**: Clean noisy input from `Unihack_ Sample Dataset - Input.csv`, remove dummy placeholders (`-- Unbranded --`, `-- No Unilog Brand --`, `-- No DIB Brand --`), and extract core identifiers.
- **Canonical Brand & Manufacturer Entity Resolution**: Fuzzy and rule-based resolver mapping supplier strings to canonical manufacturer names and brands with legal casing, suffixes (Inc, LLC, Ltd), and trademark symbols (`®`, `™`).
- **Taxonomy & UNSPSC Classification**: Classify raw items into hierarchical Classpaths (`Dept > Class > Fine`) and appropriate UNSPSC codes.
- **Attribute Extractor & Controlled Vocabulary (LOV) Engine**: Extract key technical specifications (Mounting, Voltage, Amperage, Wash Cycles, Dimensions, Connection Types, Sound Level, Material Construction) strictly constrained to canonical List of Values (LOV) dictionaries.
- **UOM & Fraction Standardization**: Convert decimal inches to fractions (e.g. `50.25 in` → `50-1/4 in`), enforce mandatory space between number and unit (`24 in`, `120 V`, `15 A`, `47 dBA`), and normalize all unit abbreviations to Unilog standard.
- **5-Tier Content & Description Generator**:
  - `INVOICE_DESC` (≤ 40 chars, ALL CAPS, e.g. `DISHWASHER LEG 5 SST 120V 15A 50-1/4IN`)
  - `MOBILE_DESC` (60–80 chars concise mobile title)
  - `SHORT_DESC` / `Product Title` (`[Brand] + [Series] + [MPN] + [Item Type] + [Key Specs]`)
  - `LONG_DESC1` (Full technical specification sentence with normalized units)
  - `MARKETING_DESCRIPTION` / Feature bullet points.

### R2. Ground-Truth Benchmarking & Quality Assurance Suite
- Score enrichment outputs against `Unihack_ Expected Output - Delivery Format.csv` across all 252 target columns.
- Measure and report:
  - Exact match and token similarity for generated descriptions.
  - Character limit compliance rate (100% for `INVOICE_DESC` ≤ 40, `MOBILE_DESC` 60–80).
  - LOV adherence percentage (0% hallucinated values).
  - Missing field rate and confidence scoring.
- Automated anomaly detection flagging products with low confidence (< 0.85) or data conflicts for "Needs Human Review".

### R3. Interactive PIM & Product Intelligence Dashboard (React + TypeScript / Modern UI + FastAPI Backend)
- **Catalog Explorer & Product Grid**: Paginated, searchable, filterable grid displaying all 1,000 items with status badges (Draft → Enriched → Validated → Flagged).
- **Side-by-Side Transformation Inspector**: Visual diff comparing raw supplier input against all 5 description tiers, normalized attributes, and confidence breakdown.
- **Interactive Playground / Sandbox**: Real-time input box allowing judges to paste any arbitrary messy distributor string and view instant, step-by-step pipeline transformations.
- **Human-in-the-Loop Review Queue**: Dedicated tab for reviewing low-confidence items, editing attributes/descriptions, and approving them for production.
- **Full 252-Column Delivery Exporter**: One-click export of the processed catalog into the exact Unilog 252-column CSV/Excel format.

## Acceptance Criteria

### Pipeline & Data Integrity
- [ ] Successfully processes all 1,000 items from `Unihack_ Sample Dataset - Input.csv`.
- [ ] 100% of generated `INVOICE_DESC` fields are ≤ 40 characters and uppercase.
- [ ] 100% of generated `MOBILE_DESC` fields are within 60–80 characters.
- [ ] Extracted attributes conform strictly to canonical LOVs without hallucinations.
- [ ] All units of measurement strictly follow Unilog UOM standards (proper spacing, abbreviations, fraction formatting).
- [ ] Benchmarking script runs cleanly and outputs comprehensive accuracy metrics comparing against the delivery ground truth.

### Dashboard & Experience
- [ ] Web application runs locally with a single command and loads cleanly.
- [ ] UI provides real-time search, category filtering, and status filtering across all 1,000 products.
- [ ] Real-time interactive playground transforms input text with sub-second feedback.
- [ ] Export functionality produces a valid 252-column CSV file matching `Unihack_ Expected Output - Delivery Format.csv` headers.
- [ ] Human review workflow enables approving or correcting flagged records.
</USER_REQUEST>
