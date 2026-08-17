"""
Automated Visual & Pixel-Layout Verification Suite for UniHack PIM Dashboard
"""

import sys
import time
import os
from playwright.sync_api import sync_playwright

VIEWPORTS = [
    {"name": "Desktop_FHD_1920x1080", "width": 1920, "height": 1080},
    {"name": "Desktop_HD_1440x900", "width": 1440, "height": 900},
    {"name": "Laptop_1280x800", "width": 1280, "height": 800},
    {"name": "Tablet_1024x768", "width": 1024, "height": 768},
    {"name": "Mobile_375x812", "width": 375, "height": 812},
]

OUTPUT_DIR = "/home/abhishek-vishwakarma/.gemini/antigravity/brain/0569232d-6be4-48f9-a26e-1baa81a043b8/ui_audit"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def audit_page_layout():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        print("="*70)
        print("🔍 Starting Comprehensive UI & Viewport Pixel-Layout Audit")
        print("="*70)
        
        for vp in VIEWPORTS:
            print(f"\n📱 Testing Viewport: {vp['name']} ({vp['width']}x{vp['height']})")
            context = browser.new_context(viewport={"width": vp["width"], "height": vp["height"]})
            page = context.new_page()
            
            # Navigate to local dashboard
            page.goto("http://localhost:8000")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1000)
            
            # Check horizontal overflow
            scroll_width = page.evaluate("document.documentElement.scrollWidth")
            client_width = page.evaluate("document.documentElement.clientWidth")
            overflow_diff = scroll_width - client_width
            
            if overflow_diff > 1:
                print(f"  ❌ Horizontal Overflow Detected: scrollWidth={scroll_width}, clientWidth={client_width} (+{overflow_diff}px)")
            else:
                print(f"  ✅ No Horizontal Overflow: scrollWidth={scroll_width} == clientWidth={client_width}")
            
            # Take screenshot of Catalog
            screenshot_path = os.path.join(OUTPUT_DIR, f"{vp['name']}_catalog.png")
            page.screenshot(path=screenshot_path, full_page=False)
            print(f"  📸 Saved screenshot: {screenshot_path}")
            
            # If desktop, test interactive features
            if vp["width"] >= 1024:
                # 1. Inspect first product
                inspect_btn = page.locator("button:has-text('Inspect')").first
                if inspect_btn.is_visible():
                    inspect_btn.click()
                    page.wait_for_timeout(600)
                    modal_path = os.path.join(OUTPUT_DIR, f"{vp['name']}_inspector_modal.png")
                    page.screenshot(path=modal_path)
                    print(f"  📸 Saved modal screenshot: {modal_path}")
                    
                    # Test Schema 252 Tab
                    tab_252 = page.locator("button:has-text('All 252 Delivery Columns')")
                    if tab_252.is_visible():
                        tab_252.click()
                        page.wait_for_timeout(400)
                        schema_path = os.path.join(OUTPUT_DIR, f"{vp['name']}_schema252_tab.png")
                        page.screenshot(path=schema_path)
                        print(f"  📸 Saved 252-column schema tab screenshot: {schema_path}")
                    
                    # Close modal with Esc
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(300)
                
                # 2. Test Playground Tab
                page.keyboard.press("2")
                page.wait_for_timeout(600)
                pg_path = os.path.join(OUTPUT_DIR, f"{vp['name']}_playground.png")
                page.screenshot(path=pg_path)
                print(f"  📸 Saved playground screenshot: {pg_path}")
                
                # 3. Test Benchmark Tab
                page.keyboard.press("4")
                page.wait_for_timeout(600)
                bm_path = os.path.join(OUTPUT_DIR, f"{vp['name']}_benchmark.png")
                page.screenshot(path=bm_path)
                print(f"  📸 Saved benchmark screenshot: {bm_path}")
                
                # 4. Test Delivery Exporter Tab
                page.keyboard.press("5")
                page.wait_for_timeout(600)
                exp_path = os.path.join(OUTPUT_DIR, f"{vp['name']}_exporter.png")
                page.screenshot(path=exp_path)
                print(f"  📸 Saved exporter screenshot: {exp_path}")
                
            context.close()
            
        browser.close()
        print("\n" + "="*70)
        print("✅ UI & Layout Audit Completed Successfully!")
        print("="*70)

if __name__ == "__main__":
    audit_page_layout()
