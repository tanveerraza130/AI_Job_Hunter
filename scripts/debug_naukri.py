#!/usr/bin/env python3
"""
Manual debug script for Naukri Playwright testing.

This is a manual debugging script, NOT an automated test.
It should not be collected by pytest.

Run with:
    python scripts/debug_naukri.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> int:
    """
    Debug Naukri Playwright connection.

    Opens a browser window, navigates to Naukri, and waits for user input.
    """
    print("\n" + "=" * 60)
    print("NAUKRI PLAYWRIGHT DEBUG SCRIPT")
    print("=" * 60)
    print("This is a manual debugging tool, not an automated test.")
    print("=" * 60 + "\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            print("Opening Naukri...")
            page.goto("https://www.naukri.com/", wait_until="networkidle")

            print(f"Current URL: {page.url}")
            print(f"Page title: {page.title()}")

            debug_dir = Path("debug")
            debug_dir.mkdir(parents=True, exist_ok=True)

            screenshot_path = debug_dir / "debug_naukri.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"Screenshot saved: {screenshot_path}")

            print("\nPress Enter to close the browser...")
            input()

        finally:
            browser.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())