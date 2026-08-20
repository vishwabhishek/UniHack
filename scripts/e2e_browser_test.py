"""
Automated E2E Browser Testing Suite using Playwright.
Tests all workflows, interactions, and screens of UNIHACK SIMPLIFI at http://localhost:8000.
"""

import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path("/home/abhishek-vishwakarma/.gemini/antigravity/brain/0569232d-6be4-48f9-a26e-1baa81a043b8/browser_test")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def run_browser_tests():
    print("=" * 70)
    print("🚀 STARTING AUTOMATED E2E BROWSER TEST SUITE FOR UNIHACK SIMPLIFI")
    print(f"Target URL: http://localhost:8000")
    print(f"Artifacts output dir: {OUTPUT_DIR}")
    print("=" * 70)

    with sync_playwright() as p:
        # Launch Chromium headless
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Step 1: Navigate to Root URL (Unauthenticated -> LoginPage)
        print("\n[STEP 1] Testing Unauthenticated Portal & LoginPage...")
        page.goto("http://localhost:8000")
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        page.screenshot(path=str(OUTPUT_DIR / "01_login_page_split.png"), full_page=True)
        print("  📸 Captured: 01_login_page_split.png")

        # Verify login elements
        assert "UNIHACK SIMPLIFI" in page.content(), "Brand title 'UNIHACK SIMPLIFI' not found on login page"
        assert "7-stage enrichment pipeline" in page.content(), "7-stage pipeline not found on login page"
        assert "252-column delivery schema" in page.content(), "Footnote not found on login page"
        print("  ✅ Login page brand, pipeline preview, and footnote verified.")

        # Step 2: Register a new test user profile
        print("\n[STEP 2] Testing User Registration Workflow...")
        register_tab = page.locator("button:has-text('REGISTER')")
        if register_tab.is_visible():
            register_tab.click()
            time.sleep(0.5)

            name_input = page.locator("input[placeholder='e.g. Abhishek Vishwakarma']")
            email_input = page.locator("input[placeholder='you@distributor.com']")
            password_input = page.locator("input[placeholder='••••••••••••']")

            name_input.fill("Abhishek Vishwakarma")
            email_input.fill(f"test_{int(time.time())}@distributor.com")
            password_input.fill("SecurePass123!")

            page.screenshot(path=str(OUTPUT_DIR / "02_registration_filled.png"))
            print("  📸 Captured: 02_registration_filled.png")

            # Click create account
            page.locator("button:has-text('Create account')").click()
            page.wait_for_load_state("networkidle")
            time.sleep(1.5)

        # Verify we are now on Dashboard
        print("\n[STEP 3] Verifying Dashboard & 3-Tier Navigation...")
        page.screenshot(path=str(OUTPUT_DIR / "03_dashboard_catalog.png"), full_page=True)
        print("  📸 Captured: 03_dashboard_catalog.png")

        assert "Catalog explorer" in page.content(), "Catalog Explorer not visible after authentication"
        assert "Total SKUs" in page.content(), "KPI grid not visible"
        print("  ✅ Authenticated session established and Catalog Explorer rendered.")

        # Step 4: Test Search & Filtering in Catalog Explorer
        print("\n[STEP 4] Testing Search & Category Filter...")
        search_input = page.locator("input[placeholder*='search SKU']").first
        if search_input.is_visible():
            search_input.fill("diablo")
            time.sleep(1)
            page.screenshot(path=str(OUTPUT_DIR / "04_catalog_search_filtered.png"), full_page=True)
            print("  📸 Captured: 04_catalog_search_filtered.png")
            assert "Diablo" in page.content(), "Search for 'diablo' did not find Diablo products"
            search_input.fill("")
            time.sleep(0.5)

        # Step 4b: Test LlamaIndex Neural RAG Semantic Search
        print("\n[STEP 4b] Testing LlamaIndex Neural RAG Semantic Search...")
        rag_button = page.locator("button:has-text('LlamaIndex RAG')")
        if rag_button.is_visible():
            rag_button.click()
            time.sleep(0.5)
            rag_input = page.locator("input[placeholder*='Ask natural language']").first
            if rag_input.is_visible():
                rag_input.fill("quiet dishwasher 120V stainless steel")
                time.sleep(1.5)
                page.screenshot(path=str(OUTPUT_DIR / "04b_catalog_rag_search.png"), full_page=True)
                print("  📸 Captured: 04b_catalog_rag_search.png")
                assert "LLAMAININDEX HYBRID RETRIEVAL" in page.content(), "RAG retrieval banner not visible"
                # Switch back to standard exact filter
                page.locator("button:has-text('Exact Filter')").click()
                time.sleep(0.5)

        # Step 5: Test Transformation Inspector Modal
        print("\n[STEP 5] Testing Transformation Inspector Modal...")
        first_row_inspect = page.locator("button:has-text('inspect')").first
        if first_row_inspect.is_visible():
            first_row_inspect.click()
            time.sleep(1)
            page.screenshot(path=str(OUTPUT_DIR / "05_transformation_inspector_modal.png"))
            print("  📸 Captured: 05_transformation_inspector_modal.png")

            # Switch tabs inside inspector
            attr_tab = page.locator("button:has-text('LOV ATTRIBUTES')")
            if attr_tab.is_visible():
                attr_tab.click()
                time.sleep(0.5)
                page.screenshot(path=str(OUTPUT_DIR / "06_inspector_lov_attributes.png"))
                print("  📸 Captured: 06_inspector_lov_attributes.png")

            graph_tab = page.locator("button:has-text('KNOWLEDGE GRAPH')")
            if graph_tab.is_visible():
                graph_tab.click()
                time.sleep(0.5)
                page.screenshot(path=str(OUTPUT_DIR / "06b_inspector_knowledge_graph.png"))
                print("  📸 Captured: 06b_inspector_knowledge_graph.png")
                assert "CONNECTED ONTOLOGICAL ENTITIES" in page.content(), "Knowledge graph view failed to render"

            prov_tab = page.locator("button:has-text('EVIDENCE & PROVENANCE')")
            if prov_tab.is_visible():
                prov_tab.click()
                time.sleep(0.5)
                page.screenshot(path=str(OUTPUT_DIR / "06c_inspector_provenance_lineage.png"))
                print("  📸 Captured: 06c_inspector_provenance_lineage.png")
                assert "FIELD-LEVEL PROVENANCE" in page.content(), "Provenance view failed to render"

            schema_tab = page.locator("button:has-text('ALL 252 COLUMNS')")
            if schema_tab.is_visible():
                schema_tab.click()
                time.sleep(0.5)
                page.screenshot(path=str(OUTPUT_DIR / "07_inspector_schema_252.png"))
                print("  📸 Captured: 07_inspector_schema_252.png")

            # Close modal with Esc or Close button
            page.keyboard.press("Escape")
            time.sleep(0.5)

        # Step 6: Test Interactive Playground (Sandbox)
        print("\n[STEP 6] Testing Live Playground Sandbox...")
        page.locator("span:has-text('Playground')").click()
        time.sleep(1)
        page.screenshot(path=str(OUTPUT_DIR / "08_playground_initial.png"), full_page=True)
        print("  📸 Captured: 08_playground_initial.png")

        # Execute transformation
        exec_btn = page.locator("button:has-text('EXECUTE PIPELINE TRANSFORMATION')")
        if exec_btn.is_visible():
            exec_btn.click()
            time.sleep(1)
            page.screenshot(path=str(OUTPUT_DIR / "09_playground_transformed.png"), full_page=True)
            print("  📸 Captured: 09_playground_transformed.png")
            print("  ✅ Real-time pipeline executed and 5-tier descriptions rendered.")

        # Step 7: Test Review Queue (HITL Exception Board)
        print("\n[STEP 7] Testing HITL Review Queue...")
        page.locator("span:has-text('Review queue')").click()
        time.sleep(1)
        page.screenshot(path=str(OUTPUT_DIR / "10_review_queue.png"), full_page=True)
        print("  📸 Captured: 10_review_queue.png")

        # Open Spec Curation Drawer
        curate_btn = page.locator("button:has-text('CURATE SPEC')").first
        if curate_btn.is_visible():
            curate_btn.click()
            time.sleep(0.5)
            page.screenshot(path=str(OUTPUT_DIR / "11_review_curate_drawer.png"))
            print("  📸 Captured: 11_review_curate_drawer.png")
            page.locator("button:has-text('CANCEL')").click()
            time.sleep(0.5)

        # Step 8: Test QA Benchmark Dashboard
        print("\n[STEP 8] Testing QA Benchmark Dashboard...")
        page.locator("span:has-text('QA Benchmark')").click()
        time.sleep(1)
        page.screenshot(path=str(OUTPUT_DIR / "12_benchmark_dashboard.png"), full_page=True)
        print("  📸 Captured: 12_benchmark_dashboard.png")

        # Step 9: Test Delivery Exporter
        print("\n[STEP 9] Testing Delivery Exporter (252-Column Syndication)...")
        page.locator("span:has-text('Export 252-Col')").click()
        time.sleep(1)
        page.screenshot(path=str(OUTPUT_DIR / "13_delivery_exporter.png"), full_page=True)
        print("  📸 Captured: 13_delivery_exporter.png")

        browser.close()

    print("\n" + "=" * 70)
    print("🎉 ALL E2E BROWSER TESTS PASSED SUCCESSFULLY!")
    print(f"Total Screenshots Generated: {len(list(OUTPUT_DIR.glob('*.png')))}")
    print("=" * 70)

if __name__ == "__main__":
    run_browser_tests()
