"""
File:
    pagination.py

Version:
    6.0.0

Status:
    FROZEN

Modified:
    2026-07-31

Reason:
    Production Ready - Pagination Manager for Naukri

Purpose:
    Collect remaining search result pages (Page 2+) from Naukri.

Responsibilities:
    - Click Next button for each subsequent page
    - Capture Search API response using expect_response
    - Yield raw JSON payload for each page
    - Stop when Next button disappears or is disabled

Dependencies:
    - playwright.sync_api: Page, Response
    - jobs.connectors.naukri.constants: NETWORK_RESPONSE_TIMEOUT_MS, SEARCH_API_PATH
    - jobs.connectors.naukri.selectors: NAUKRI_NEXT_BUTTON
    - jobs.connectors.naukri.session: NaukriSession
    - utils.logger: get_logger

This module does NOT:
    - Fetch Page 1 (Connector owns Page 1)
    - Validate JSON
    - Map jobs
    - Deduplicate
    - Write debug files
    - Track anything
    - Retry
    - Inspect response content

PEP8:     Yes
SOLID:    Yes (Single Responsibility)
DRY:      Yes
KISS:     Yes
"""

from __future__ import annotations

import logging
from typing import Iterator

from playwright.sync_api import Page, Response

from jobs.connectors.naukri.constants import (
    NETWORK_RESPONSE_TIMEOUT_MS,
    SEARCH_API_PATH,
)
from jobs.connectors.naukri.selectors import NAUKRI_NEXT_BUTTON
from jobs.connectors.naukri.session import NaukriSession
from utils.logger import get_logger

# Type alias for JSON payloads
JsonDict = dict[str, object]

# Module logger
logger: logging.Logger = get_logger(__name__)


class PaginationManager:
    """
    Manages pagination for Naukri search results (Page 2+).

    Simple pagination handler that clicks Next and captures API responses
    using the same expect_response pattern as connector.py.

    Attributes:
        session (NaukriSession): Authenticated browser session.
    """

    def __init__(self, session: NaukriSession) -> None:
        """
        Initialize PaginationManager with a Naukri session.

        Args:
            session: Authenticated NaukriSession with browser context.

        Raises:
            ValueError: If session is None.
        """
        if session is None:
            raise ValueError("session cannot be None")

        self._session: NaukriSession = session

    def collect_remaining_pages(self) -> Iterator[JsonDict]:
        """
        Collect Page 2+ search result pages and yield raw JSON.

        Starts from the current page (which should be Page 1) and
        continues clicking Next until the button disappears or is disabled.

        Yields:
            Iterator[JsonDict]: Raw JSON payload from each subsequent page.

        Raises:
            RuntimeError: If API response is not captured during Next click.
        """
        page: Page = self._session.page

        while True:
            # Check if Next button exists and is enabled
            next_button = page.locator(NAUKRI_NEXT_BUTTON)

            if not next_button.is_visible():
                logger.debug("Next button not visible, stopping")
                break

            if next_button.is_disabled():
                logger.debug("Next button disabled, stopping")
                break

            # Click Next and capture API response
            # The action MUST be inside expect_response context
            with page.expect_response(
                lambda response: (
                    SEARCH_API_PATH in response.url
                    and response.request.method == "GET"
                    and response.ok
                ),
                timeout=NETWORK_RESPONSE_TIMEOUT_MS,
            ) as response_info:
                next_button.click()
                logger.debug("Next button clicked")

            # Extract JSON from captured response
            response: Response = response_info.value

            if not response.ok:
                logger.error(
                    "Naukri Search API returned status %s",
                    response.status,
                )
                raise RuntimeError(f"API responded with status {response.status}")

            payload: JsonDict = response.json()
            logger.debug("API response captured")

            # Yield the raw JSON - no validation, no inspection
            yield payload


# =============================================================================
# END OF FILE
# =============================================================================