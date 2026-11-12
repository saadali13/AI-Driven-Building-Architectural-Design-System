import asyncio
import os
from playwright.async_api import async_playwright

ARTIFACT_DIR = r"C:\Users\m\.gemini\antigravity\brain\6239a98e-1bc6-4057-b6b6-7b6a68b442bf"

async def run_browser_tests():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 950})
        page = await context.new_page()

        print("[Step 1] Navigating to http://localhost:5173/app/designs/new")
        await page.goto("http://localhost:5173/app/designs/new", timeout=60000)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # Select Guided Structured Form
        print("[Step 2] Selecting 'Guided Structured Form'")
        await page.click("text='Guided Structured Form'")
        await asyncio.sleep(1)

        # Click Continue to Plot Information (Step 1 -> Step 2)
        print("[Step 3] Clicking Continue to Plot Information")
        await page.click("button:has-text('Continue to Plot Information')")
        await asyncio.sleep(1)

        # Select 10 Marla (35x65) in Step 2
        print("[Step 4] Selecting 10 Marla (35x65)")
        await page.click("text='10 Marla'")
        await asyncio.sleep(1)

        # Click Continue to Room Schedule (Step 2 -> Step 3)
        print("[Step 5] Navigating to Room Schedule")
        await page.click("button:has-text('Continue to Room Schedule')")
        await asyncio.sleep(2)

        # Screenshot the Room Schedule & Itemized Dimensions Editor
        sched_shot = os.path.join(ARTIFACT_DIR, "verified_room_schedule_itemized_dimensions.png")
        await page.screenshot(path=sched_shot, full_page=True)
        print(f"[Step 6] Room schedule screenshot saved: {sched_shot}")

        # Continue to Style & Priorities (Step 3 -> Step 4)
        print("[Step 7] Clicking Continue to Style & Priorities")
        await page.click("button:has-text('Continue to Style & Priorities')")
        await asyncio.sleep(1)

        # Continue to Technical Review (Step 4 -> Step 5)
        print("[Step 8] Clicking Continue to Technical Review")
        await page.click("button:has-text('Continue to Technical Review')")
        await asyncio.sleep(1)

        # Click Generate Floor Plan (Step 5 -> Synthesis)
        print("[Step 9] Clicking Generate Floor Plan")
        await page.click("button:has-text('Generate Floor Plan')")
        
        # Wait for floor plan synthesis to complete
        print("[Step 10] Waiting for synthesis completion...")
        await page.wait_for_selector("button:has-text('Regenerate & Refine')", timeout=60000)
        await asyncio.sleep(3)

        v1_shot = os.path.join(ARTIFACT_DIR, "verified_initial_v1_floor_plan.png")
        await page.screenshot(path=v1_shot, full_page=False)
        print(f"[Step 11] Initial v1 plan screenshot saved: {v1_shot}")

        # Click "Regenerate & Refine"
        print("[Step 12] Opening Regenerate & Refine modal for prompt 1")
        await page.click("button:has-text('Regenerate & Refine')")
        await asyncio.sleep(1)

        # Type User Prompt 1
        p1_text = "why dirty kitchen is connect to the formal drawing room and diry kichen is only door connect to the main kitchen and door connect to main kitchen and right side area of house set right are and also grand entry is why separate to the tv lounge"
        prompt_input = page.locator("textarea[placeholder*='Move the master bedroom']")
        await prompt_input.fill(p1_text)
        await asyncio.sleep(1)

        # Click Regenerate Floor Plan with Modifications
        print("[Step 13] Submitting refinement prompt 1")
        await page.click("button:has-text('Regenerate Floor Plan with Modifications')")

        # Wait for completion
        await asyncio.sleep(3)
        await page.wait_for_selector("button:has-text('Regenerate & Refine')", timeout=60000)
        await asyncio.sleep(2)

        # Verify NO conflict banner
        conflict_banner = page.locator("text='Spatial & Statutory Bylaw Conflict'")
        conflict_visible = await conflict_banner.count() > 0
        print(f"[Step 14] Conflict banner visible: {conflict_visible} (Must be False!)")
        assert not conflict_visible, "Conflict banner should NOT be visible on valid prompt!"

        v2_shot = os.path.join(ARTIFACT_DIR, "verified_user_prompt1_regenerated_v2.png")
        await page.screenshot(path=v2_shot, full_page=False)
        print(f"[Step 15] Prompt 1 regenerated v2 plan saved: {v2_shot}")

        # Test User Prompt 2: "remove the grand entrance this ocup the area and this not look good in floor plan"
        print("[Step 16] Opening Regenerate & Refine modal for prompt 2")
        await page.click("button:has-text('Regenerate & Refine')")
        await asyncio.sleep(1)

        p2_text = "remove the grand entrance this ocup the area and this not look good in floor plan"
        prompt_input2 = page.locator("textarea[placeholder*='Move the master bedroom']")
        await prompt_input2.fill(p2_text)
        await asyncio.sleep(1)

        print("[Step 17] Submitting refinement prompt 2")
        await page.click("button:has-text('Regenerate Floor Plan with Modifications')")

        await asyncio.sleep(3)
        await page.wait_for_selector("button:has-text('Regenerate & Refine')", timeout=60000)
        await asyncio.sleep(2)

        conflict_visible2 = await conflict_banner.count() > 0
        print(f"[Step 18] Conflict banner visible: {conflict_visible2} (Must be False!)")
        assert not conflict_visible2, "Conflict banner should NOT be visible on prompt 2!"

        v3_shot = os.path.join(ARTIFACT_DIR, "verified_user_prompt2_regenerated_v3.png")
        await page.screenshot(path=v3_shot, full_page=False)
        print(f"[Step 19] Prompt 2 regenerated v3 plan saved: {v3_shot}")

        await browser.close()
        print("\n==============================================")
        print("ALL BROWSER VERIFICATION TESTS PASSED 100%!")
        print("==============================================")

if __name__ == "__main__":
    asyncio.run(run_browser_tests())
