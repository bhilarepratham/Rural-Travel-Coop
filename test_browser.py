"""Real-browser check of both regions with no login. Needs backend + Streamlit running and Playwright:
   FRONTEND_URL=http://localhost:8501 python test_browser.py"""
import os, sys
from playwright.sync_api import sync_playwright

URL = os.environ.get("FRONTEND_URL", "http://localhost:8501")

def ok(c, l):
    print(("PASS " if c else "FAIL ") + l)
    if not c: sys.exit(1)

def body(page): return page.inner_text("body")

def run_region(browser, region, operator_text, expect_link):
    ctx = browser.new_context()          # fresh browser, no cookies, no sign-in
    page = ctx.new_page(); page.set_default_timeout(30000)
    page.goto(URL); page.wait_for_selector("text=Where are you travelling?")
    txt = body(page).lower()
    ok(not any(w in txt for w in ("log in", "sign in", "password")), f"{region}: no login text on the first page")
    if region != "Alaska":
        page.get_by_role("combobox", name="Where are you travelling?").click()
        page.get_by_role("option", name=region).click()
        page.wait_for_timeout(1500)
    tiles = page.get_by_role("button", name="See trips")
    ok(tiles.count() >= 3, f"{region}: three popular trips shown")
    tiles.nth(1 if region == "Ohio" else 0).click()
    page.wait_for_selector("text=options found")
    ok(operator_text in body(page), f"{region}: results show {operator_text}")
    # choose the card containing operator text
    block = page.locator("[data-testid='stVerticalBlock']").filter(has_text=operator_text).filter(has=page.get_by_role("button", name="Select")).last
    block.get_by_role("button", name="Select").first.click()
    page.wait_for_selector("text=Review your trip")
    ok(operator_text in body(page), f"{region}: review page names {operator_text}")
    page.get_by_role("button", name="Continue to operator site").click()
    page.wait_for_selector("text=Referral saved")
    link = page.get_by_role("link", name="Open operator site")
    href = link.get_attribute("href")
    ok(href and "ref=coop-" in href and expect_link in href, f"{region}: operator link carries tracking code ({href[:60]})")
    ok(not any(w in body(page).lower() for w in ("log in", "sign in", "password")), f"{region}: still no login")
    ctx.close()

with sync_playwright() as p:
    b = p.chromium.launch()
    run_region(b, "Alaska", "Alaska Railroad", "alaskarailroad")
    run_region(b, "Ohio", "GoBus Green Line (Ohio)", "ridegobus")
    b.close()
print("browser checks done")
