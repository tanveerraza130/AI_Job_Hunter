"""
IIMJobs API client.

Handles source-specific HTTP access only.
No normalization, filtering, scoring, storage, or business logic belongs here.
"""

from __future__ import annotations

import random
import time
from typing import Any

import requests


BASE_URL = "https://gladiator.iimjobs.com"

KEYWORD_PATH = "/job/keyword/"
DETAIL_PATH = "/job/detail"

REQUEST_TIMEOUT_SECONDS = 30

MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0
MAX_BACKOFF_SECONDS = 8.0
JITTER_MIN_SECONDS = 0.0
JITTER_MAX_SECONDS = 0.5

RETRYABLE_STATUS_CODES = {
    408,
    429,
    500,
    502,
    503,
    504,
}


class IIMJobsAPIError(RuntimeError):
    """Raised when an IIMJobs API request cannot be completed."""


class IIMJobsAPI:
    """Small HTTP client for the public IIMJobs job APIs."""

    def __init__(
        self,
        *,
        session: requests.Session | None = None,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout

        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/139.0 Safari/537.36"
                ),
            }
        )

    @staticmethod
    def _backoff_seconds(attempt: int) -> float:
        exponential_delay = (
            INITIAL_BACKOFF_SECONDS * (2 ** (attempt - 1))
        )

        bounded_delay = min(
            exponential_delay,
            MAX_BACKOFF_SECONDS,
        )

        return bounded_delay + random.uniform(
            JITTER_MIN_SECONDS,
            JITTER_MAX_SECONDS,
        )

    @staticmethod
    def _is_retryable_status(status_code: int) -> bool:
        return status_code in RETRYABLE_STATUS_CODES

    def _get_json(
        self,
        *,
        path: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        url = f"{BASE_URL}{path}"
        last_error: Exception | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout,
                    allow_redirects=True,
                )

                if response.status_code == 200:
                    try:
                        payload = response.json()
                    except ValueError as exc:
                        raise IIMJobsAPIError(
                            "IIMJobs returned HTTP 200 but "
                            "the response was not valid JSON."
                        ) from exc

                    if not isinstance(payload, dict):
                        raise IIMJobsAPIError(
                            "Unexpected IIMJobs response type."
                        )

                    return payload

                if not self._is_retryable_status(
                    response.status_code
                ):
                    raise IIMJobsAPIError(
                        "IIMJobs returned non-retryable "
                        f"HTTP {response.status_code} "
                        f"for {path}."
                    )

                last_error = IIMJobsAPIError(
                    "IIMJobs returned retryable "
                    f"HTTP {response.status_code} "
                    f"for {path}."
                )

                if attempt >= MAX_RETRIES:
                    break

                time.sleep(
                    self._backoff_seconds(attempt)
                )

            except IIMJobsAPIError:
                raise

            except requests.RequestException as exc:
                last_error = exc

                if attempt >= MAX_RETRIES:
                    break

                time.sleep(
                    self._backoff_seconds(attempt)
                )

        raise IIMJobsAPIError(
            f"Unable to fetch IIMJobs endpoint {path} "
            f"after {MAX_RETRIES} attempts."
        ) from last_error

    def fetch_keyword(
        self,
        *,
        page: int,
        keyword_id: int,
        location_id: int,
        ref_pool: str,
    ) -> dict[str, Any]:
        """
        Fetch one IIMJobs keyword/search page.

        This mirrors the verified public keyword-feed request
        used by the IIMJobs CRM keyword page.
        """
        return self._get_json(
            path=KEYWORD_PATH,
            params={
                "minexp": 0,
                "maxexp": 0,
                "query": keyword_id,
                "page": page,
                "concat": "false",
                "catOrTagId": keyword_id,
                "loc": location_id,
                "keywordId": keyword_id,
                "refPool": ref_pool,
            },
        )

    def fetch_detail(
        self,
        *,
        job_code: str | int,
    ) -> dict[str, Any]:
        """Fetch one complete IIMJobs job detail payload."""
        return self._get_json(
            path=DETAIL_PATH,
            params={
                "jobcode": job_code,
            },
        )
