"""
Foundit structured JSON API client.

Foundit's HTML search pages may return Access Denied while the public
structured search middleware remains available. This client therefore
uses the structured JSON layer directly.

All Foundit-specific HTTP behavior stays inside this module.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class FounditAPIError(RuntimeError):
    """Raised for unrecoverable Foundit API errors."""


class FounditAPI:
    BASE_URL = "https://www.foundit.in"
    SEARCH_PATH = "/middleware/jobsearch"
    DETAIL_PATH = "/middleware/jobdetail/{job_id}"

    REQUEST_TIMEOUT = 8
    MAX_RETRIES = 2

    def __init__(
        self,
        session: requests.Session | None = None,
    ) -> None:
        self.session = session or requests.Session()

        self.session.headers.update(
            {
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-IN,en;q=0.9",
                "Referer": f"{self.BASE_URL}/",
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/139.0.0.0 Safari/537.36"
                ),
            }
        )

    def _get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any | None:
        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            logger.warning(
                "Foundit request failed: %s",
                exc,
            )
            return None

        if response.status_code >= 400:
            logger.warning(
                "Foundit HTTP %s: %s",
                response.status_code,
                response.url,
            )
            return None

        try:
            return response.json()
        except ValueError:
            logger.warning(
                "Foundit returned non-JSON response: %s",
                response.url,
            )
            return None

    def fetch_search_page(
        self,
        *,
        keyword: str,
        location: str | None,
        start: int,
        limit: int,
    ) -> dict[str, Any] | None:
        """
        Fetch one complete Foundit search response.

        The full payload is intentionally returned so the connector can
        consume both job data and pagination metadata.
        """

        params: dict[str, Any] = {
            "start": start,
            "limit": limit,
            "query": keyword,
        }

        if location:
            params["locations"] = location

        url = f"{self.BASE_URL}{self.SEARCH_PATH}"

        payload = self._get_json(
            url,
            params=params,
        )

        if not isinstance(payload, dict):
            logger.warning(
                "Foundit search returned unexpected payload type: %s",
                type(payload).__name__,
            )
            return None

        response = payload.get("jobSearchResponse")

        if not isinstance(response, dict):
            logger.warning(
                "Foundit search response missing jobSearchResponse"
            )
            return None

        data = response.get("data")

        if not isinstance(data, list):
            logger.warning(
                "Foundit search response missing data list"
            )
            return None

        return payload

    def fetch_detail(
        self,
        job_id: str,
    ) -> dict[str, Any] | None:
        """
        Fetch one Foundit job detail record.

        Foundit returns a transport envelope containing
        ``jobDetailResponse``. This method unwraps that envelope so
        callers receive the actual job record.

        Individual detail failures are isolated and do not terminate
        the complete connector run.
        """

        clean_id = str(job_id).strip()

        if not clean_id:
            return None

        url = (
            f"{self.BASE_URL}"
            f"{self.DETAIL_PATH.format(job_id=clean_id)}"
        )

        payload = self._get_json(url)

        if not isinstance(payload, dict):
            return None

        detail = payload.get("jobDetailResponse")

        if isinstance(detail, dict):
            return detail

        return None
