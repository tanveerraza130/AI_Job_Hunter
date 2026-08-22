"""
Naukri session.

Responsibilities
----------------
• Launch browser
• Create context
• Load cookies
• Validate login
• Return page
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from playwright.sync_api import BrowserContext, Page

from .api import NaukriAPI
from .constants import BASE_URL, COOKIE_FILE
from .selectors import LOGIN_BUTTON, PROFILE_ICON

logger = logging.getLogger(__name__)


class NaukriSession:
    """
    Authenticated Naukri session.

    Attributes
    ----------
    context : BrowserContext
        Playwright browser context.
    api : NaukriAPI | None
        API client for pagination.
    """

    def __init__(self, context: BrowserContext) -> None:
        self.context: BrowserContext = context
        self.api: NaukriAPI | None = None
        self._page: Page | None = None

    @property
    def browser_page(self) -> Page:
        """
        Get or create the browser page.
        """
        if self._page is None:
            self._page = self.context.new_page()
        return self._page

    def initialize_api(self, first_request: dict[str, Any]) -> None:
        """
        Initialize the API client with captured browser request.

        Args:
            first_request: Captured request data containing url, headers, query.
        """
        logger.info(">>> initialize_api entered")
        logger.info(">>> first_request keys: %s", list(first_request.keys()))
        logger.info(">>> first_request contains 'url': %s", "url" in first_request)
        logger.info(">>> first_request contains 'headers': %s", "headers" in first_request)
        logger.info(">>> first_request contains 'query': %s", "query" in first_request)

        cookies = self.get_cookies()
        logger.info(">>> Retrieved %s cookies for API client", len(cookies))

        self.api = NaukriAPI(
            first_request=first_request,
            cookies=cookies,
        )

        logger.info(">>> self.api assigned: %s", self.api)
        logger.info(">>> self.api type: %s", type(self.api) if self.api else "None")
        logger.info("API client initialized from captured browser request")

    def load_cookies(self) -> None:
        """
        Load cookies from file into browser context.

        Raises
        ------
        RuntimeError
            If no cookies are loaded.
        """
        cookie_path = Path(COOKIE_FILE)

        if not cookie_path.exists():
            logger.warning("No cookies found at %s", cookie_path)
            return

        with open(cookie_path, "r", encoding="utf-8") as f:
            cookies_data: list[dict[str, Any]] = json.load(f)

        if not cookies_data:
            logger.warning("Cookie file is empty.")
            return

        logger.info("Loaded %s cookies from file", len(cookies_data))

        # Filter out invalid cookies
        filtered_cookies = []
        skipped_cookies = 0

        for cookie in cookies_data:
            if "name" not in cookie or "value" not in cookie:
                skipped_cookies += 1
                continue

            valid_cookie = {
                "name": cookie["name"],
                "value": cookie["value"],
            }

            if "domain" in cookie and cookie["domain"]:
                valid_cookie["domain"] = cookie["domain"]
            elif "domain" in cookie:
                valid_cookie["domain"] = ".naukri.com"

            if "path" in cookie and cookie["path"]:
                valid_cookie["path"] = cookie["path"]
            if "expires" in cookie and cookie["expires"]:
                valid_cookie["expires"] = cookie["expires"]
            if "httpOnly" in cookie:
                valid_cookie["httpOnly"] = cookie["httpOnly"]
            if "secure" in cookie:
                valid_cookie["secure"] = cookie["secure"]
            if "sameSite" in cookie and cookie["sameSite"]:
                valid_cookie["sameSite"] = cookie["sameSite"]

            filtered_cookies.append(valid_cookie)

        if skipped_cookies > 0:
            logger.info("Skipped %s invalid cookies", skipped_cookies)

        if not filtered_cookies:
            logger.warning("No valid cookies after filtering.")
            return

        logger.info("Adding %s cookies to context", len(filtered_cookies))
        self.context.add_cookies(filtered_cookies)

    def is_logged_in(self) -> bool:
        """
        Check if session is logged in.

        Navigates to the homepage and checks for profile icon.
        Returns True if logged in, False otherwise.
        """
        page = self.browser_page

        # Navigate to homepage
        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(1000)

        # Check for profile icon
        if page.locator(PROFILE_ICON).count() > 0:
            logger.debug("Profile icon found - logged in")
            return True

        # Check for login button
        if page.locator(LOGIN_BUTTON).count() > 0:
            logger.debug("Login button found - not logged in")
            return False

        # Check URL for login indicators
        if "login" in page.url.lower():
            logger.debug("URL contains 'login' - not logged in")
            return False

        return False

    def get_cookies(self) -> list[dict]:
        """
        Get current cookies from browser context.
        """
        return self.context.cookies()


# =============================================================================
# END OF FILE
# =============================================================================