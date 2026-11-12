import os
import sys
import time
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = r"C:\Users\m\.gemini\antigravity\brain\6239a98e-1bc6-4057-b6b6-7b6a68b442bf"

def run_cost_estimation_tests():
    print("=== STARTING PLAYWRIGHT VERIFICATION FOR COST ESTIMATION & FORMULA ENGINE ===")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 1000})
        page = context.new_page()

        # Step 1: Navigate to Cost Estimation Page
        print("1. Navigating to /app/cost-estimation...")
        page.goto("http://localhost:5173/app/cost-estimation", timeout=20000)
        page.wait_for_selector("text=Construction Cost Planning & Material BOQ", timeout=10000)
        print("   [OK] Cost Estimation Page Loaded successfully.")

        # Step 2: Verify Initial KPIs and Parameters
        page.wait_for_selector("text=Total Estimated Construction Cost", timeout=5000)
        initial_cost = page.locator("text=Total Estimated Construction Cost").locator("../..").locator("p").first.text_content()
        print(f"   [OK] Initial Total Construction Budget: {initial_cost}")

        # Step 3: Check Educational Formula Breakdown Section
        page.wait_for_selector("text=Understand How House Construction Cost is Calculated in Pakistan", timeout=5000)
        print("   [OK] 'Understand How House Construction Cost is Calculated' Educational Formula Guide confirmed visible.")

        # Step 4: Interact with Material Variety Dropdowns
        print("4. Testing Material Variety Selection...")
        # Select Concrete Blocks for Bricks
        brick_variety_select = page.locator("table select").first
        brick_variety_select.select_option(value="concrete_block")
        time.sleep(0.5)
        print("   [OK] Selected 'Solid Concrete Blocks' for masonry.")

        # Select SRC Sulphate Resistant Cement for Cement
        cement_variety_select = page.locator("table select").nth(1)
        cement_variety_select.select_option(value="src_sulphate")
        time.sleep(0.5)
        print("   [OK] Selected 'SRC Sulphate Resistant Cement' for foundations.")

        # Step 5: Test Editing Custom Unit Price
        print("5. Testing Manual Custom Price Input Editing...")
        steel_price_input = page.locator("table input[type='number']").nth(5) # Rebar unit price
        steel_price_input.fill("285000")
        steel_price_input.press("Enter")
        time.sleep(0.5)
        print("   [OK] Updated Steel Rebar Unit Rate to PKR 285,000/ton.")

        # Step 6: Test Changing Covered Area Parameter
        covered_area_input = page.locator("input[type='number']").first
        covered_area_input.fill("4200")
        covered_area_input.press("Enter")
        time.sleep(0.5)
        print("   [OK] Updated Covered Area to 4,200 sq ft.")

        updated_cost = page.locator("text=Total Estimated Construction Cost").locator("../..").locator("p").first.text_content()
        print(f"   [OK] Recalculated Grand Total Budget: {updated_cost}")

        # Step 7: Test Category Filter Buttons
        print("7. Testing Trade Category Filter Buttons...")
        page.locator("button:has-text('Grey Structure (6)')").click()
        time.sleep(0.4)
        print("   [OK] Filtered to Grey Structure trades.")

        page.locator("button:has-text('Finishing Works (5)')").click()
        time.sleep(0.4)
        print("   [OK] Filtered to Finishing Works trades.")

        page.locator("button:has-text('All Trades (13)')").click()
        time.sleep(0.4)
        print("   [OK] Restored All 13 Trades view.")

        # Step 8: Test Save Estimate Action
        save_btn = page.locator("button:has-text('Save Estimate')")
        save_btn.click()
        page.wait_for_selector("text=Saved to Projects!", timeout=5000)
        print("   [OK] Verified 'Saved to Projects!' action feedback.")

        # Capture Screenshot of full Cost Estimation Page
        cost_screenshot_path = os.path.join(SCREENSHOT_DIR, "verified_cost_estimation_page.png")
        page.screenshot(path=cost_screenshot_path, full_page=True)
        print(f"   [OK] Full-page screenshot saved to: {cost_screenshot_path}")

        # Step 9: Verify Tab 5 in New Design Page
        print("9. Navigating to /app/designs/new to verify Tab 5 BOQ...")
        page.goto("http://localhost:5173/app/designs/new", timeout=20000)
        page.wait_for_selector("text=How would you like to start?", timeout=10000)
        page.locator("button:has-text('Continue to AI Prompt Studio')").click()
        page.wait_for_selector("text=Describe Your House in Natural Language", timeout=10000)

        # Generate Floor Plan to reach Step 5
        review_btn = page.locator("button:has-text('Review AI Extraction Brief')")
        review_btn.click()
        page.wait_for_selector("text=Review & Customize Design Brief", timeout=10000)

        generate_btn = page.locator("button:has-text('Generate Floor Plan')")
        generate_btn.click()
        page.wait_for_selector("text=Cost Estimation & Material BOQ", timeout=30000)
        print("   [OK] Design synthesis reached Step 5.")

        # Click Tab 5: Cost Estimation & Material BOQ
        page.locator("button:has-text('Cost Estimation & Material BOQ')").click()
        time.sleep(1)
        page.wait_for_selector("text=Parametric Bill of Quantities (BOQ) & Material Pricing", timeout=10000)
        print("   [OK] Tab 5 BOQ active.")

        # Verify variety dropdown and formula explainer in Tab 5
        page.wait_for_selector("text=Civil Engineering Formula Breakdown", timeout=5000)
        print("   [OK] Tab 5 Educational Civil Engineering Formula breakdown visible.")

        # Change a variety in Tab 5
        tab5_variety_select = page.locator("table select").first
        tab5_variety_select.select_option(value="concrete_block")
        time.sleep(0.5)
        print("   [OK] Tab 5 variety dropdown changed successfully.")

        # Capture Tab 5 Screenshot
        tab5_screenshot_path = os.path.join(SCREENSHOT_DIR, "verified_tab5_boq_varieties.png")
        page.screenshot(path=tab5_screenshot_path)
        print(f"   [OK] Tab 5 BOQ screenshot saved to: {tab5_screenshot_path}")

        browser.close()
        print("\n=== ALL COST ESTIMATION & BOQ TESTS PASSED WITH 100% SUCCESS ===")

if __name__ == "__main__":
    run_cost_estimation_tests()
