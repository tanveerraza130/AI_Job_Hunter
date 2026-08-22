from __future__ import annotations

from typing import Any

from playwright.sync_api import Page, TimeoutError


class NetworkInterceptor:
    """Capture JSON responses from browser network traffic."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def wait_for_json(
        self,
        *,
        url_contains: str,
        timeout: int = 30_000,
    ) -> dict[str, Any]:
        """
        Wait for a JSON response matching the URL.
        """

        try:
            with self.page.expect_response(
                lambda response: (
                    url_contains in response.url
                    and response.ok
                ),
                timeout=timeout,
            ) as response_info:

                pass

            response = response_info.value

        except TimeoutError as exc:
            raise RuntimeError(
                f"Timed out waiting for '{url_contains}'."
            ) from exc

        try:
            return response.json()

        except Exception as exc:
            raise RuntimeError(
                f"Invalid JSON received from '{response.url}'."
            ) from exc