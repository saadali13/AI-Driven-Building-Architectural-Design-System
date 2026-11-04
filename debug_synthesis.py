from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    logs = []
    page.on("console", lambda m: logs.append(f"[{m.type}] {m.text}"))
    page.on("pageerror", lambda e: logs.append(f"[PAGE ERROR] {e}"))

    page.goto("http://localhost:5173/app/designs/new", wait_until="networkidle")
    page.locator("button:has-text('Continue to AI Prompt Studio')").first.click()
    page.wait_for_timeout(500)
    page.locator("textarea").first.fill("10 Marla modern house with 4 bedrooms, 4 bathrooms, TV lounge, and open kitchen")
    page.locator("button:has-text('Review AI Extraction Brief')").first.click()
    page.wait_for_timeout(500)
    page.locator("button:has-text('Generate Floor Plan')").first.click()
    print("Clicked generate floor plan...")

    for i in range(12):
        page.wait_for_timeout(2000)
        page.screenshot(path=f"output/browser_debug_{i}.png")
        txt = page.locator("h1, h2, h3, p, span").all_text_contents()
        relevant = [t.strip() for t in txt if any(w in t.lower() for w in ['step', '100%', 'loading', 'drawing', 'error', 'complete', 'synthesiz']) if t.strip()]
        print(f"Second {i*2}:")
        print(f"  Snippets: {relevant[:5]}")
        if any("drawing" in t.lower() for t in relevant):
            print("DRAWINGS FOUND!")
            break

    print("Console logs:", logs[-15:])
    browser.close()

