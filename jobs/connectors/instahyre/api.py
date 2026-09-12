"""
Instahyre public job-search API and public job-page client.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import requests
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class InstahyreAPIError(RuntimeError):
    """Raised when Instahyre cannot be queried successfully."""


class InstahyreAPI:
    BASE_URL = "https://www.instahyre.com"
    SEARCH_PATH = "/api/v1/job_search"

    PAGE_SIZE = 20
    TIMEOUT = 30

    MAX_RETRIES = 4
    REQUEST_DELAY = 1.5
    MAX_BACKOFF = 30

    def __init__(self):
        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/149.0 Safari/537.36"
                ),
                "Accept": (
                    "application/json, text/plain, "
                    "application/xhtml+xml, text/html;q=0.9,*/*;q=0.8"
                ),
                "Referer": "https://www.instahyre.com/search-jobs/",
            }
        )

    def fetch_page(self, offset: int = 0) -> dict[str, Any]:
        """Fetch one public Instahyre job-search page."""

        params = {
            "company_size": 0,
            "isLandingPage": "true",
            "job_type": 0,
            "offset": offset,
            "source": "opportunities",
        }

        url = f"{self.BASE_URL}{self.SEARCH_PATH}"

        for attempt in range(1, self.MAX_RETRIES + 1):
            if attempt > 1:
                delay = min(
                    self.MAX_BACKOFF,
                    self.REQUEST_DELAY * (2 ** (attempt - 1)),
                )
                time.sleep(delay)

            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.TIMEOUT,
                )
            except requests.RequestException as exc:
                logger.warning(
                    "Instahyre request failed "
                    "(offset=%s attempt=%s): %s",
                    offset,
                    attempt,
                    exc,
                )

                if attempt == self.MAX_RETRIES:
                    raise InstahyreAPIError(
                        f"Instahyre request failed: {exc}"
                    ) from exc

                continue

            if response.status_code == 200:
                try:
                    payload = response.json()
                except ValueError as exc:
                    raise InstahyreAPIError(
                        "Instahyre returned invalid JSON"
                    ) from exc

                if not isinstance(payload, dict):
                    raise InstahyreAPIError(
                        "Instahyre returned an unexpected payload"
                    )

                time.sleep(self.REQUEST_DELAY)

                return payload

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")

                if retry_after:
                    try:
                        delay = min(
                            self.MAX_BACKOFF,
                            max(1, int(retry_after)),
                        )
                    except ValueError:
                        delay = min(
                            self.MAX_BACKOFF,
                            self.REQUEST_DELAY * (2 ** attempt),
                        )
                else:
                    delay = min(
                        self.MAX_BACKOFF,
                        self.REQUEST_DELAY * (2 ** attempt),
                    )

                logger.warning(
                    "Instahyre rate limited "
                    "(offset=%s attempt=%s), waiting %.1fs",
                    offset,
                    attempt,
                    delay,
                )

                time.sleep(delay)
                continue

            if response.status_code in {
                408,
                500,
                502,
                503,
                504,
            }:
                logger.warning(
                    "Instahyre temporary HTTP %s "
                    "(offset=%s attempt=%s)",
                    response.status_code,
                    offset,
                    attempt,
                )
                continue

            raise InstahyreAPIError(
                "Instahyre returned HTTP "
                f"{response.status_code} for offset={offset}"
            )

        raise InstahyreAPIError(
            f"Instahyre request failed after {self.MAX_RETRIES} attempts "
            f"(offset={offset})"
        )

    def fetch_job_page(self, job_url: str) -> str:
        """Fetch a public Instahyre job page."""

        if not job_url:
            return ""

        try:
            response = self.session.get(
                job_url,
                timeout=self.TIMEOUT,
                headers={
                    "Accept": (
                        "text/html,application/xhtml+xml,"
                        "application/xml;q=0.9,*/*;q=0.8"
                    ),
                    "Referer": "https://www.instahyre.com/search-jobs/",
                },
            )
        except requests.RequestException as exc:
            logger.warning(
                "Instahyre job-page request failed: %s",
                exc,
            )
            return ""

        if response.status_code != 200:
            logger.warning(
                "Instahyre job page returned HTTP %s: %s",
                response.status_code,
                job_url,
            )
            return ""

        return response.text

    @staticmethod
    def _clean_text(value: Any) -> str:
        if value is None:
            return ""

        if not isinstance(value, str):
            value = str(value)

        soup = BeautifulSoup(value, "html.parser")

        return " ".join(
            soup.get_text(" ", strip=True).split()
        )

    def extract_job_page_data(
        self,
        html: str,
    ) -> dict[str, Any]:
        """
        Extract structured JobPosting data from the public page.

        JSON-LD is preferred because the page exposes a structured
        JobPosting object containing the full description.
        """

        if not html:
            return {}

        soup = BeautifulSoup(html, "html.parser")

        for script in soup.find_all(
            "script",
            attrs={"type": "application/ld+json"},
        ):
            raw = script.string or script.get_text()

            if not raw:
                continue

            try:
                payload = json.loads(raw)
            except (TypeError, ValueError):
                continue

            candidates: list[dict[str, Any]] = []

            if isinstance(payload, dict):
                candidates.append(payload)

                graph = payload.get("@graph")

                if isinstance(graph, list):
                    candidates.extend(
                        item
                        for item in graph
                        if isinstance(item, dict)
                    )

            elif isinstance(payload, list):
                candidates.extend(
                    item
                    for item in payload
                    if isinstance(item, dict)
                )

            for item in candidates:
                if item.get("@type") == "JobPosting":
                    result = dict(item)

                    description = self._clean_text(
                        result.get("description")
                    )

                    if description:
                        result["description"] = description

                    return result

        # Fallback: public page's actual job-description block.
        description_node = soup.select_one(
            "#job-description .job-description"
        )

        if description_node:
            return {
                "description": self._clean_text(
                    str(description_node)
                )
            }

        return {}
