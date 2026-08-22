from pathlib import Path
from playwright.sync_api import sync_playwright
import json

COOKIE_FILE = Path("data/sessions/naukri_cookies.json")

COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    print("Opening Naukri...")
    page.goto("https://www.naukri.com", wait_until="domcontentloaded")

    print("\n===================================================")
    print("1. Login manually")
    print("2. Complete OTP if asked")
    print("3. Wait until your profile is visible")
    print("4. Press ENTER here")
    print("===================================================\n")

    input()

    cookies = context.cookies()

    COOKIE_FILE.write_text(
        json.dumps(cookies, indent=2),
        encoding="utf-8",
    )

    print(f"\nSaved {len(cookies)} cookies")
    print(f"Location: {COOKIE_FILE}")

    browser.close()