#!/usr/bin/env python3
"""
Standalone test to determine whether Naukri blocks deep-link navigation.

This test uses pure Playwright with no cookies, no project imports,
and no API interception. It simply navigates to Naukri and checks
if deep-link navigation works.

Requirements:
    1. Launch Chromium (headless=False)
    2. Open https://www.naukri.com/
    3. Print current URL and page title
    4. Wait 3 seconds
    5. Navigate to https://www.naukri.com/python-developer-jobs-in-bangalore
    6. Print current URL and page title
    7. Save debug/standalone_home.png and debug/standalone_search.png
    8. Save debug/standalone_search.html
    9. Keep browser open until Enter is pressed
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> int:
    """
    Main entry point for the standalone test.
    """
    # Create debug directory
    debug_dir = Path("debug")
    debug_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 80)
    print("STANDALONE NAUKRI NAVIGATION TEST")
    print("=" * 80)
    print("No cookies, no project imports, pure Playwright only.")
    print("=" * 80 + "\n")

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # Step 1: Navigate to homepage
            print("Step 1: Navigating to https://www.naukri.com/")
            page.goto("https://www.naukri.com/", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)

            home_url = page.url
            home_title = page.title()

            print("\n" + "-" * 40)
            print("HOME PAGE")
            print("-" * 40)
            print(f"Current URL: {home_url}")
            print(f"Page title: {home_title}")

            # Save homepage screenshot
            screenshot_path = debug_dir / "standalone_home.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"Saved screenshot: {screenshot_path}")

            # Wait 3 seconds
            print("\nWaiting 3 seconds...")
            page.wait_for_timeout(3000)

            # Step 2: Navigate to search page
            search_url = "https://www.naukri.com/python-developer-jobs-in-bangalore"
            print("\n" + "-" * 40)
            print(f"Step 2: Navigating to {search_url}")
            print("-" * 40)
            page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)

            search_page_url = page.url
            search_page_title = page.title()

            print("\n" + "-" * 40)
            print("SEARCH PAGE")
            print("-" * 40)
            print(f"Current URL: {search_page_url}")
            print(f"Page title: {search_page_title}")

            # Save search page screenshot
            screenshot_path = debug_dir / "standalone_search.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"Saved screenshot: {screenshot_path}")

            # Save search page HTML
            html_path = debug_dir / "standalone_search.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(page.content())
            print(f"Saved HTML: {html_path}")

            print("\n" + "=" * 80)
            print("TEST COMPLETE")
            print("=" * 80)
            print(f"Home URL   : {home_url}")
            print(f"Home Title : {home_title}")
            print(f"Search URL : {search_page_url}")
            print(f"Search Title: {search_page_title}")
            print("=" * 80)

            # Keep browser open
            print("\nPress Enter to close the browser...")
            input()

        finally:
            browser.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())


# =============================================================================
# END OF FILE
# =============================================================================