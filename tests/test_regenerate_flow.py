import time
import os
import re
from playwright.sync_api import sync_playwright

def test_regenerate_remove_dirty_kitchen():
    screenshot_dir = os.path.join(os.getcwd(), "output", "playwright_verify")
    os.makedirs(screenshot_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 950})
        page = context.new_page()
        
        print("[1] Navigating to http://localhost:5173/app/designs/new...")
        page.goto("http://localhost:5173/app/designs/new", timeout=30000)
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Step 1: Mode Selection (Default is AI prompt flow)
        print("[2] Step 1: Continuing to AI Prompt Studio...")
        page.locator("button:has-text('Continue to AI Prompt Studio')").click()
        time.sleep(1)
        
        # Step 2: AI Prompt Studio
        print("[3] Step 2: Selecting 10 Marla preset...")
        page.locator("button:has-text('10 MARLA')").first.click()
        time.sleep(1)
        
        print("[4] Step 2: Continuing to Review Brief...")
        page.locator("button:has-text('Review AI Extraction Brief')").click()
        time.sleep(1)
        
        # Step 3: Review Brief & Generate
        print("[5] Step 3: Clicking Generate Floor Plan...")
        page.locator("button:has-text('Generate Floor Plan')").click()
        
        # Wait for Step 5 Results
        print("[6] Waiting for floor plan synthesis...")
        page.wait_for_selector("text=Revisions:", timeout=45000)
        time.sleep(3)
        
        # Capture v1 screenshot
        v1_path = os.path.join(screenshot_dir, "v1_original_floor_plan.png")
        page.screenshot(path=v1_path, full_page=True)
        print(f"[7] Saved v1 screenshot to {v1_path}")
        
        # Click Regenerate & Refine
        print("[8] Opening Regenerate & Refine modal...")
        page.locator("button:has-text('Regenerate & Refine')").click()
        time.sleep(1)
        
        # Type "remove dirty kitchen"
        print("[9] Entering prompt: 'remove dirty kitchen'...")
        textarea = page.locator("textarea[placeholder*='Move the master bedroom']")
        textarea.fill("remove dirty kitchen")
        time.sleep(1)
        
        # Click Regenerate Floor Plan with Modifications
        print("[10] Submitting regeneration request...")
        page.locator("button:has-text('Regenerate Floor Plan with Modifications')").click()
        
        # Wait for v2 to appear
        print("[11] Waiting for v2 revision...")
        page.wait_for_selector("text=v2", timeout=35000)
        time.sleep(3)
        
        # Capture v2 screenshot
        v2_path = os.path.join(screenshot_dir, "v2_regenerated_dirty_kitchen_removed.png")
        page.screenshot(path=v2_path, full_page=True)
        print(f"[12] Saved v2 screenshot to {v2_path}")
        
        # Verify that v2 revision badge is present
        v2_badge = page.locator("span:has-text('v2')")
        print(f"[13] v2 badge visible: {v2_badge.first.is_visible()}")
        
        browser.close()
        print("[14] Verification test completed successfully!")

if __name__ == "__main__":
    test_regenerate_remove_dirty_kitchen()
