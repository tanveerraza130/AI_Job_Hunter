"""
Network Inspector

Purpose:
- Open Naukri
- Perform a manual search
- Print interesting requests
- Print JSON API responses
"""

import json

from playwright.sync_api import sync_playwright


KEYWORDS = (
    "jobs",
    "search",
    "keyword",
    "location",
    "recommend",
    "list",
)


def is_interesting(url: str) -> bool:
    url = url.lower()
    return any(word in url for word in KEYWORDS)


def log_request(request):
    if not is_interesting(request.url):
        return

    print("\n" + "=" * 120)
    print("REQUEST")
    print("=" * 120)
    print(request.method)
    print(request.url)


def log_response(response):
    if not is_interesting(response.url):
        return

    print("\n" + "=" * 120)
    print("RESPONSE")
    print("=" * 120)
    print(response.status)
    print(response.url)

    content_type = response.headers.get("content-type", "")

    if "application/json" not in content_type:
        return

    try:
        data = response.json()

        print("-" * 120)
        print(json.dumps(data, indent=2)[:5000])
        print("-" * 120)

    except Exception:
        pass


def main():

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False,
        )

        page = browser.new_page()

        page.on("request", log_request)
        page.on("response", log_response)

        page.goto(
            "https://www.naukri.com",
            wait_until="networkidle",
        )

        print("\n")
        print("=" * 120)
        print("MANUAL STEPS")
        print("=" * 120)
        print("1. Login if required")
        print("2. Search CRM")
        print("3. Select Delhi NCR")
        print("4. Wait until results load")
        print("5. Press ENTER")
        print("=" * 120)

        input()

        browser.close()


if __name__ == "__main__":
    main()