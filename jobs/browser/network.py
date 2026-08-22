"""
Reusable Playwright network helper.

Every connector (Naukri, LinkedIn, Indeed, Foundit, etc.)
uses this class to capture authenticated JSON responses.
"""

from __future__ import annotations

from typing import Any

from playwright.sync_api import Page, TimeoutError


class BrowserNetwork:
    """Capture browser network responses."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def capture_json(
        self,
        *,
        navigate_to: str,
        url_contains: str,
        timeout: int = 30_000,
        wait_until: str = "domcontentloaded",
    ) -> dict[str, Any]:
        """
        Navigate and capture the first matching JSON response.
        """

        try:
            with self.page.expect_response(
                lambda response: (
                    response.ok
                    and url_contains in response.url
                ),
                timeout=timeout,
            ) as response_info:

                self.page.goto(
                    navigate_to,
                    wait_until=wait_until,
                )

            return response_info.value.json()

        except TimeoutError as exc:
            raise RuntimeError(
                f"Timed out waiting for '{url_contains}'."
            ) from exc

        except Exception as exc:
            raise RuntimeError(
                "Unable to capture browser JSON response."
            ) from exc