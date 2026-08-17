## 2026-08-16T11:41:36Z
You are Worker 3 (Full-Stack FastAPI & React Dashboard Engineer) for the Industrial Product Intelligence & PIM Enrichment project.
Your working directory is /home/abhishek-vishwakarma/Documents/Hackathons/Unilog/.agents/worker_dashboard_m3.
Create your working directory if needed.

Read:
1. /home/abhishek-vishwakarma/Documents/Hackathons/Unilog/ORIGINAL_REQUEST.md
2. /home/abhishek-vishwakarma/Documents/Hackathons/Unilog/PROJECT.md
3. /home/abhishek-vishwakarma/Documents/Hackathons/Unilog/.agents/explorer_survey_3/survey_system_and_ui.md
4. /home/abhishek-vishwakarma/Documents/Hackathons/Unilog/.agents/worker_pipeline_m1/handoff.md
5. /home/abhishek-vishwakarma/Documents/Hackathons/Unilog/.agents/worker_benchmark_m2/handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

You have exclusive write ownership of:
- `src/backend/` (`__init__.py`, `main.py`, `config.py`, `state.py`, `schemas.py`, `routes/`)
- `src/frontend/` (Vite + React + TypeScript + Tailwind CSS application)
- `scripts/start_dashboard.sh`
- `tests/integration/test_api_endpoints.py`

Your tasks:
1. Implement `src/backend/`:
   - `config.py`: Settings, paths to `data/` and dictionaries.
   - `schemas.py`: Pydantic request/response schemas for catalog, product details, playground, review queue, benchmarks, export.
   - `state.py`: In-memory catalog index pre-loaded with all 1,000 items from `Unihack_ Sample Dataset - Input.csv` / `data/output/enriched_catalog_252_columns.csv`. Handles search, filters, pagination, review queue triage, inline edits, and approvals.
   - `routes/catalog.py`: `GET /api/products`, `GET /api/products/{id}`, `GET /api/stats`.
   - `routes/playground.py`: `POST /api/playground/transform` (live sub-second transformation of arbitrary supplier text using `EnrichmentEngine`).
   - `routes/review.py`: `GET /api/review/queue`, `POST /api/review/{id}/approve`, `PUT /api/review/{id}`, `POST /api/review/{id}/reject`.
   - `routes/benchmark.py`: `GET /api/benchmark/results`, `POST /api/benchmark/run`.
   - `routes/export.py`: `GET /api/export/csv`, `GET /api/export/xlsx` (generating full 252-column files).
   - `main.py`: FastAPI app with CORS, API routers, static file mounting for frontend build, and lifespan startup event.
2. Implement `src/frontend/`:
   - Setup React 18 + TypeScript + Vite + Tailwind CSS + Lucide React in `src/frontend/`.
   - Build a gorgeous, modern, high-performance UI with tabs/views:
     a. **Header / Navbar**: Brand, Live status indicator, KPI cards (Total Items: 1,000, 100% Enriched, 0 Hard Gate Violations, Mean Confidence).
     b. **Catalog Explorer & Product Grid**: Search by MPN/Title/Brand, filter by Category / Brand / Status (Draft, Enriched, Validated, Flagged), table view with status badges, pagination, confidence scores, click-to-inspect.
     c. **Side-by-Side Transformation Inspector**: Visual comparison showing raw distributor strings on the left vs all 5 description tiers (`INVOICE_DESC`, `MOBILE_DESC`, `SHORT_DESC`, `LONG_DESC1`, `MARKETING_DESCRIPTION`), extracted 50 triplet attributes with LOV tags, UOM standardization badges, and 5-factor confidence radar breakdown.
     d. **Interactive Playground / Sandbox**: Preset test buttons (Dishwasher, Miter Saw Blade, Deck Board, Recessed LED, Brass Fitting) + custom text input box, live/instant transform button with sub-second execution, showing step-by-step stage outputs (Sanitized -> Entity -> Taxonomy -> Attributes -> 5-Tier Descriptions).
     e. **Human-in-the-Loop Review Queue**: Dedicated queue for items with confidence < 0.85 or flagged status, inline editor for attributes/descriptions, live re-scoring, and one-click "Approve for Production" button.
     f. **Full 252-Column Delivery Exporter**: Preview table of all 252 columns, group toggles, and one-click CSV and Excel download buttons.
     g. **QA Benchmarks & Evaluation Analytics**: Visual cards for Hard-Gate compliance (100% Invoice <=40, 100% Mobile 60-80, 0% LOV Hallucinations, 252/252 schema), BLEU/ROUGE/Levenshtein metrics, confidence distributions.
   - Build the frontend bundle (`npm run build` -> `src/frontend/dist/`).
3. Implement `scripts/start_dashboard.sh`:
   - Single executable script that starts backend and serves frontend.
4. Verify backend endpoints and UI build with automated tests:
   - Run `pytest tests/` and verify all tests pass.
   - Test starting the backend, hitting endpoints, verifying responses, and checking clean frontend build.

Write your handoff report to /home/abhishek-vishwakarma/Documents/Hackathons/Unilog/.agents/worker_dashboard_m3/handoff.md.
Send a message back to parent (ccd71a4e-664b-41b5-b4c0-b843693a438e) when done.
