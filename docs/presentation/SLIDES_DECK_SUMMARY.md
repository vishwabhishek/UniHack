# 🎯 UniHack 2026 Final Presentation Deck Summary

**Project**: UniHack Simplifi — Evidence-First Industrial Product Intelligence & PIM  
**Team**: Error 404 (`Abhishek Vishwakarma`)  
**Deck File**: [`Error_404_UniHack_Product_Intelligence.pptx`](file:///home/abhishek-vishwakarma/Documents/Hackathons/Unilog/docs/presentation/Error_404_UniHack_Product_Intelligence.pptx)  
**Slide Count**: 15 Slides (16:9 Widescreen)  

---

## 📑 Slide-by-Slide Outline & Talking Points

### Slide 1: Title & Vision
- **Header**: `UNI HACK 2026 | Evidence-First Product Intelligence`
- **Subtitle**: *Turning fragmented industrial product data into structured, traceable, commerce-ready intelligence.*
- **Key Visual**: Supplier Data → Official Evidence → Gemini Extraction → Human Validation → Verified Record.
- **Presenter**: Abhishek Vishwakarma · Team Error 404.

### Slide 2: The Opportunity & Market Context
- **Title**: `THE OPPORTUNITY`
- **Core Friction**: Industrial distributor catalogs receive noisy, sparse supplier feeds with dummy placeholders (`-- Unbranded --`), missing specs, and conflicting brand names.
- **Business Impact**: Manual cataloging takes weeks, leads to misordered parts, customer returns, and poor search discovery.

### Slide 3: Problem Statement & Delivery Schema
- **Title**: `PROBLEM STATEMENT: 6 Raw Fields to 252 Delivery Standard`
- **Supplier Feed**: 1,000 raw rows across 6 noisy columns (`Mfg_Part_Num`, `Part_Desc`, `E1_Brand`, `Unilog_Brand`, `DIB_Brand`, `Part_Manuf`).
- **Target Schema**: 252 standardized columns, 50 attribute triplets (`LABEL / VALUE / UOM`), 5 description tiers, and strict length/casing hard gates.

### Slide 4: Our Solution — UniHack Simplifi
- **Title**: `OUR SOLUTION: Provenance-First Enrichment Workbench`
- **Core Thesis**: An operational workbench for data specialists, not a black-box text generator.
- **5-Step Core Flow**:
  1. *Ingest*: Clean raw tokens, strip placeholders.
  2. *Ground*: Register official manufacturer PDF/HTML spec sheets.
  3. *Extract*: Gemini structured extraction constrained to official source chunks.
  4. *Validate*: Deterministic LOV, UOM, and citation cross-verification.
  5. *Promote*: Field-level Human-in-the-Loop review queue.

### Slide 5: End-to-End Traceability Workflow
- **Title**: `END-TO-END WORKFLOW: Immutable Chain of Trust`
- **Architecture Flow**: Raw Input → Source Registry → Gemini Candidates → Deterministic Gates → Review Queue → 252-Column Export.
- **Truth Guarantee**: If evidence is missing, fields remain intentionally blank instead of hallucinating.

### Slide 6: System Architecture & Tech Stack
- **Title**: `SYSTEM ARCHITECTURE`
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Lucide icons, Dark Industrial UI.
- **Backend API**: FastAPI, Python 3.12, Pydantic v2, SQLite WAL mode, asynchronous batch workers.
- **Search & Evaluation**: Hybrid Lexical (BM25) + Semantic Vector RAG (FastEmbed), 252-column ground-truth benchmark suite.

### Slide 7: Constrained AI — Gemini's Role
- **Title**: `GEMINI'S ROLE: Candidate Extractor with Hard Gates`
- **Guardrails**:
  - Temperature 0.0 deterministic schema extraction.
  - Constrained strictly to official manufacturer text chunks.
  - Mandatory page/section citations for every extracted attribute.
  - Deterministic post-processing rejects unsupported or out-of-dictionary claims.

### Slide 8: Field-Level Provenance Model
- **Title**: `EVIDENCE & PROVENANCE: Every Field Has a Paper Trail`
- **Interactive Example**:
  - Attribute: `Pressure Rating`
  - Value: `200 psi`
  - Source: *SharkBite Brass Coupling Technical Specification Sheet (Page 2)*
  - SHA-256 Hash: `5734924d...`
  - Reviewer Action: 1-Click Approve / Edit / Reject / Mark Unknown.

### Slide 9: Human-in-the-Loop Governance Queue
- **Title**: `HUMAN-IN-THE-LOOP QUALITY GATE`
- **Specialist Authority**: High-risk identity fields (`MPN`, `Brand`, `Manufacturer`, `Taxonomy`, `Invoice Description`) require explicit review before promotion.
- **Visual**: Embedded screenshot of the live interactive **Review Queue** with confidence badges and audit history.

### Slide 10: Product Experience & Workbench UI
- **Title**: `PRODUCT EXPERIENCE: Industrial Catalog Specialist Workbench`
- **Key Modules**:
  - *Catalog Explorer*: 1,000-SKU grid with hybrid BM25/Semantic search.
  - *Transformation Inspector*: Side-by-side raw input vs. 5 description tiers and attribute triplets.
  - *Evidence Inbox*: Source document registry with chunk inspection.
- **Visuals**: Embedded live UI screenshots of the Transformation Inspector and Catalog Explorer.

### Slide 11: Commerce-Ready 252-Column Delivery
- **Title**: `COMMERCE-READY DELIVERY`
- **Outputs**: Single-click 252-column CSV / Excel export matching Unilog ground truth.
- **Integrity**: Formula injection sanitization (`=`, `+`, `-`, `@`), SHA-256 export checksums, and audit trail.

### Slide 12: Trust & Security by Design
- **Title**: `TRUST & SECURITY BY DESIGN`
- **Security Hardening**:
  - Server-side evidence acquisition with SSRF & private IP blocking.
  - HttpOnly JWT session cookies, CSRF protection, and token versioning.
  - Role-Based Access Control (Admin, Specialist, Reviewer, Viewer).

### Slide 13: Truthful Benchmarking & QA
- **Title**: `TRUTHFUL EVALUATION`
- **Hard Gate Compliance**:
  - `INVOICE_DESC` ≤ 40 chars & 100% ALL CAPS: **100% Pass**.
  - `MOBILE_DESC` 60–80 chars: **100% Pass**.
  - LOV Hallucination Rate: **0.0%**.
  - 252 Delivery Column Sequence: **100% Match**.
- **Automated Test Suite**: **449/449 tests passed (100%)**.

### Slide 14: Path to Enterprise Scale
- **Title**: `PATH TO SCALE`
- **Phased Roadmap**:
  - *Phase 1 (Current)*: 1,000-SKU prototype, SQLite WAL, Gemini + deterministic pipeline, HITL review queue.
  - *Phase 2 (Near-Term)*: Multi-tenant distributor ingestion, async job queues, source re-crawling.
  - *Phase 3 (Enterprise)*: Multi-modal visual spec validation, ERP connectors (SAP, Epicor, NetSuite).

### Slide 15: Conclusion & Live Demo Flow
- **Title**: `ERROR 404: Build Explainable Product Intelligence`
- **Demo Script (3 Minutes)**:
  1. Search catalog & inspect raw supplier noise.
  2. Ingest official manufacturer spec sheet in Evidence Inbox.
  3. Trigger real-time Gemini extraction & deterministic LOV/UOM gating in Playground.
  4. Triage high-risk attributes in Review Queue with audit trail.
  5. Export validated 252-column master deliverable.

---

## 🔗 File Locations
- **PowerPoint File**: [`docs/presentation/Error_404_UniHack_Product_Intelligence.pptx`](file:///home/abhishek-vishwakarma/Documents/Hackathons/Unilog/docs/presentation/Error_404_UniHack_Product_Intelligence.pptx)
- **Organizer Template**: [`docs/presentation/[EXT] UniHack-Protoype Template  (1).pptx`](file:///home/abhishek-vishwakarma/Documents/Hackathons/Unilog/docs/presentation/[EXT] UniHack-Protoype Template  (1).pptx)
- **Repository Root Copy**: [`Error_404_UniHack_Product_Intelligence.pptx`](file:///home/abhishek-vishwakarma/Documents/Hackathons/Unilog/Error_404_UniHack_Product_Intelligence.pptx)
