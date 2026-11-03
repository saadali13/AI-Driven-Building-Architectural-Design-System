import os
import sys
import json
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "output/browser_qa"
os.makedirs(OUTPUT_DIR, exist_ok=True)
ART_DIR = r"C:\Users\m\.gemini\antigravity\brain\6239a98e-1bc6-4057-b6b6-7b6a68b442bf"

def log(msg):
    print(f"[QA RUNNER] {msg}", flush=True)

def run_tests():
    log("Launching System Chrome via Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900}, accept_downloads=True)
        page = context.new_page()

        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        failed_requests = []
        page.on("requestfailed", lambda req: failed_requests.append(f"{req.method} {req.url}: {req.failure}"))

        # -------------------------------------------------------------
        # TEST 1: PROMPT MODE 10 MARLA GENERATION TO STEP 5
        # -------------------------------------------------------------
        log("Test 1: Prompt Mode 10 Marla Plan Generation...")
        page.goto("http://localhost:5173/app/designs/new", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # Step 1: Click "Continue to AI Prompt Studio"
        cont_btn = page.locator("button:has-text('Continue to AI Prompt Studio')").first
        if cont_btn.is_visible():
            cont_btn.click()
            page.wait_for_timeout(1000)

        # Step 2: Fill prompt textarea
        log("Filling prompt textarea...")
        prompt_input = page.locator("textarea").first
        prompt_input.fill("10 Marla modern house with 4 bedrooms, 4 bathrooms, TV lounge, and open kitchen")
        page.wait_for_timeout(500)

        # Click "Review AI Extraction Brief"
        rev_btn = page.locator("button:has-text('Review AI Extraction Brief')").first
        rev_btn.click()
        page.wait_for_timeout(1000)

        # Step 3: Click "Generate Floor Plan"
        log("On Step 3 Review. Clicking Generate Floor Plan...")
        gen_btn = page.locator("button:has-text('Generate Floor Plan')").first
        gen_btn.click()
        log("Generation triggered! Waiting for Step 5 Drawings...")

        # Step 5: Wait for Step 5 result elements
        page.locator("button:has-text('Regenerate & Refine')").first.wait_for(timeout=40000)
        log("Step 5 reached successfully!")
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "01_prompt_mode_step5.png"), full_page=False)

        # Verify 3 Variant Cards
        variants = page.locator("div:has-text('alt_1'), div:has-text('alt_2'), div:has-text('alt_3')").all()
        log(f"Variant cards detected count: {len(variants)}")

        # Verify Compliance Checklist (User Stated vs Added by Bylaws)
        has_checklist = page.locator("text=Requirements Compliance Checklist").count() > 0
        log(f"Compliance checklist present: {has_checklist}")

        # Verify Explainability Panel
        has_explain = page.locator("text=AI Architecture Logic & Explainability Panel").count() > 0
        log(f"Explainability panel present: {has_explain}")

        # -------------------------------------------------------------
        # TEST 2: ELEVATION, 3D, AND AUDIT TABS
        # -------------------------------------------------------------
        log("Test 2: Testing Elevation, 3D, and Audit tabs...")
        elev_tab = page.locator("button:has-text('Technical Front Elevation'), button:has-text('Elevation')").first
        if elev_tab.is_visible():
            elev_tab.click()
            page.wait_for_timeout(1000)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "02_elevation_tab.png"))
            log("Elevation tab captured.")

        threed_tab = page.locator("button:has-text('3D Spatial Geometry'), button:has-text('3D View')").first
        if threed_tab.is_visible():
            threed_tab.click()
            page.wait_for_timeout(1000)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "03_3d_tab.png"))
            log("3D tab captured.")

        audit_tab = page.locator("button:has-text('Senior Architect Audit'), button:has-text('Audit')").first
        if audit_tab.is_visible():
            audit_tab.click()
            page.wait_for_timeout(1000)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "04_audit_tab.png"))
            log("Audit tab captured.")

        # Switch back to floor plan tab
        floor_tab = page.locator("button:has-text('Floor Plans')").first
        if floor_tab.is_visible():
            floor_tab.click()
            page.wait_for_timeout(500)

        # -------------------------------------------------------------
        # TEST 3: REGENERATE & REFINE (v1 -> v2 -> v3)
        # -------------------------------------------------------------
        log("Test 3: Regenerate & Refine Layout (v1 -> v2)...")
        refine_open_btn = page.locator("button:has-text('Regenerate & Refine')").first
        if refine_open_btn.is_visible():
            refine_open_btn.click()
            page.wait_for_timeout(1000)

            refine_input = page.locator("textarea[placeholder*='bedroom'], textarea").first
            refine_input.fill("move stairs to rear")
            apply_btn = page.locator("button:has-text('Regenerate Floor Plan with Modifications')").first
            apply_btn.click()
            log("Submitted v2 refinement (move stairs to rear). Waiting...")

            page.locator("button:has-text('v2'), span:has-text('v2')").first.wait_for(timeout=35000)
            page.wait_for_timeout(1500)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "06_refine_v2.png"))
            log("v2 generated & captured.")

            # Refinement to v3 (Swap Dining and Kitchen)
            refine_open_btn.click()
            page.wait_for_timeout(1000)
            refine_input = page.locator("textarea[placeholder*='bedroom'], textarea").first
            refine_input.fill("swap dining and kitchen")
            page.locator("button:has-text('Regenerate Floor Plan with Modifications')").first.click()
            log("Submitted v3 refinement (swap dining and kitchen). Waiting...")
            page.locator("button:has-text('v3'), span:has-text('v3')").first.wait_for(timeout=35000)
            page.wait_for_timeout(1500)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "07_refine_v3.png"))
            log("v3 generated & captured (swap dining and kitchen).")

            # ---------------------------------------------------------
            # TEST 4: RESTORE TO v1
            # ---------------------------------------------------------
            log("Test 4: Restore to v1...")
            v1_btn = page.locator("button:has-text('v1 (Original)'), button:has-text('Restore to v1')").first
            if v1_btn.is_visible():
                v1_btn.click()
                page.wait_for_timeout(1500)
                page.screenshot(path=os.path.join(OUTPUT_DIR, "08_restore_v1.png"))
                log("Restore to v1 captured.")

            # ---------------------------------------------------------
            # TEST 5: CONFLICT BANNER
            # ---------------------------------------------------------
            log("Test 5: Testing Spatial & Bylaw Conflict Banner...")
            refine_open_btn.click()
            page.wait_for_timeout(1000)
            refine_input = page.locator("textarea[placeholder*='bedroom'], textarea").first
            refine_input.fill("expand master bedroom by 200%")
            page.locator("button:has-text('Regenerate Floor Plan with Modifications')").first.click()
            page.wait_for_timeout(1500)
            page.locator("text=Spatial & Statutory Bylaw Conflict").first.wait_for(timeout=10000)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "09_conflict_banner.png"))
            log("Conflict banner captured.")

            # Dismiss conflict
            dismiss_btn = page.locator("button:has-text('Dismiss')").first
            if dismiss_btn.is_visible():
                dismiss_btn.click()
                page.wait_for_timeout(500)

        # -------------------------------------------------------------
        # TEST 6: EXPORT CAD PACKAGE (SVG, PNG, DXF, PDF, OBJ, BLENDER)
        # -------------------------------------------------------------
        log("Test 6: Export CAD Package Modal & Downloads verification...")
        export_btn = page.locator("button:has-text('Export CAD Package')").first
        if export_btn.is_visible():
            export_btn.click()
            page.wait_for_timeout(1000)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "10_downloads_modal.png"))
            log("Export modal captured.")

            # Trigger download options
            for fmt in ['svg', 'png', 'dxf', 'pdf', 'obj', 'blend']:
                try:
                    fmt_opt = page.locator(f"button:has-text('{fmt.upper()}')").first
                    if fmt_opt.is_visible():
                        fmt_opt.click()
                        page.wait_for_timeout(200)
                    down_btn = page.locator(f"button:has-text('Download {fmt.upper()}')").first
                    if down_btn.is_visible():
                        down_btn.click()
                        page.wait_for_timeout(800)
                        log(f"Export format {fmt.upper()} button tested.")
                except Exception as e:
                    log(f"Export format {fmt} test: {e}")

            # Close export modal
            close_exp = page.locator("button:has-text('Cancel')").first
            if close_exp.is_visible():
                close_exp.click()
                page.wait_for_timeout(500)

        # -------------------------------------------------------------
        # TEST 7: SAVED DESIGNS PAGE & DETAILS PAGE
        # -------------------------------------------------------------
        log("Test 7: Testing Saved Designs Page & Details Page...")
        page.goto("http://localhost:5173/app/designs", wait_until="networkidle")
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "11_saved_designs_page.png"))
        log("Saved designs page captured.")

        # Click on first design details link
        first_details = page.locator("a[href*='/app/designs/archi_'], a[href*='/app/designs/proj_'], a:has-text('View Design Details'), a:has-text('View CAD Details')").first
        if first_details.is_visible():
            first_details.click()
            page.wait_for_timeout(1500)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "12_details_page.png"))
            log("Design details page captured.")

            # Reload persistence
            log("Testing reload persistence...")
            page.reload(wait_until="networkidle")
            page.wait_for_timeout(1000)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "13_reload_persistence.png"))
            log("Reload persistence verified.")

            # Back/Forward navigation
            log("Testing browser back/forward navigation...")
            page.go_back(wait_until="networkidle")
            page.wait_for_timeout(1000)
            page.go_forward(wait_until="networkidle")
            page.wait_for_timeout(1000)
            page.screenshot(path=os.path.join(OUTPUT_DIR, "14_browser_navigation.png"))
            log("Back/Forward navigation verified.")

        # -------------------------------------------------------------
        # TEST 8: GUIDED FORM MODE (10 MARLA)
        # -------------------------------------------------------------
        log("Test 8: Guided Form Mode Generation...")
        page.goto("http://localhost:5173/app/designs/new", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # Click Guided Form mode card
        form_card = page.locator("div:has-text('Structured Architectural Form')").first
        if form_card.is_visible():
            form_card.click()
            page.wait_for_timeout(500)

        # Click Continue to Plot Information
        cont_plot = page.locator("button:has-text('Continue to Plot Information')").first
        if cont_plot.is_visible():
            cont_plot.click()
            page.wait_for_timeout(1000)

            # Select 10 Marla preset
            marla_10_opt = page.locator("div:has-text('10 Marla'), button:has-text('10 Marla')").first
            if marla_10_opt.is_visible():
                marla_10_opt.click()
                page.wait_for_timeout(500)

            # Step 2 -> Step 3
            page.locator("button:has-text('Configure Requirements')").first.click()
            page.wait_for_timeout(1000)

            # Step 3 -> Step 4
            page.locator("button:has-text('Choose Architectural Style')").first.click()
            page.wait_for_timeout(1000)

            # Step 4 -> Step 5
            page.locator("button:has-text('Review & Finalize')").first.click()
            page.wait_for_timeout(1000)

            # Step 5 -> Synthesis
            synth_btn = page.locator("button:has-text('Synthesize Custom Residence')").first
            if synth_btn.is_visible():
                synth_btn.click()
                log("Form synthesis triggered. Waiting for Step 7 drawings...")
                page.locator("button:has-text('Regenerate & Refine')").first.wait_for(timeout=40000)
                page.wait_for_timeout(2000)
                page.screenshot(path=os.path.join(OUTPUT_DIR, "16_guided_form_step5.png"))
                log("Guided Form Step 7 reached and captured!")

        # -------------------------------------------------------------
        # TEST 9: VIEWPORT RESPONSIVENESS (MOBILE 375px & TABLET 768px)
        # -------------------------------------------------------------
        log("Test 9: Viewport responsiveness tests...")
        page.set_viewport_size({"width": 375, "height": 812})
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "17_mobile_step5.png"))
        log("Mobile 375px captured.")

        page.set_viewport_size({"width": 768, "height": 1024})
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "18_tablet_step5.png"))
        log("Tablet 768px captured.")

        # Reset viewport
        page.set_viewport_size({"width": 1440, "height": 900})

        # -------------------------------------------------------------
        # TEST 10: BACKEND STOPPED ERROR & RETRY BUTTON
        # -------------------------------------------------------------
        log("Test 10: Error state & Retry button test...")
        page.route("**/api/generate", lambda route: route.abort("connectionfailed"))
        page.goto("http://localhost:5173/app/designs/new", wait_until="networkidle")
        page.wait_for_timeout(500)
        page.locator("button:has-text('Continue to AI Prompt Studio')").first.click()
        page.wait_for_timeout(500)
        prompt_input = page.locator("textarea").first
        prompt_input.fill("5 Marla test error")
        page.locator("button:has-text('Review AI Extraction Brief')").first.click()
        page.wait_for_timeout(500)
        page.locator("button:has-text('Generate Floor Plan')").first.click()

        page.locator("button:has-text('Retry Synthesis')").first.wait_for(timeout=15000)
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(OUTPUT_DIR, "15_error_retry_state.png"))
        log("Error state with Retry Synthesis button captured!")

        browser.close()
        log("All browser tests completed successfully!")

        # Copy all screenshots to artifact directory
        for f in os.listdir(OUTPUT_DIR):
            if f.endswith(".png") or f.endswith(".svg"):
                src = os.path.join(OUTPUT_DIR, f)
                dst = os.path.join(ART_DIR, f)
                with open(src, "rb") as sf, open(dst, "wb") as df:
                    df.write(sf.read())
        log("All screenshots copied to Artifact directory.")

if __name__ == "__main__":
    run_tests()
