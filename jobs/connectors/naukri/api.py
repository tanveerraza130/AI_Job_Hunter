
"""
Naukri API client for AI Job Hunter.

Responsibilities
----------------
- Reuse the exact browser-captured Naukri API request.
- Preserve Naukri's original query parameters.
- Paginate by changing only the page number.
- Retry only transient failures.
- Stop immediately on non-retryable HTTP errors.
- Deduplicate jobs by Job ID within a search.
- Return mapper-compatible response data.

This module contains no profile-specific logic.
"""

from __future__ import annotations

import logging
import random
import time
from typing import Any
from urllib.parse import parse_qs, urlparse

import requests

from .constants import DEFAULT_MAX_JOBS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MAX_RETRIES = 3
REQUEST_TIMEOUT_SECONDS = 30

INITIAL_BACKOFF_SECONDS = 1.5
MAX_BACKOFF_SECONDS = 12.0

JITTER_MIN_SECONDS = 0.25
JITTER_MAX_SECONDS = 0.75

RETRYABLE_STATUS_CODES = frozenset(
    {
        408,
        425,
        429,
        500,
        502,
        503,
        504,
    }
)


class NaukriAPI:
    """
    Naukri search API client.

    The browser captures the first successful search request.
    Pagination reuses that exact request structure and changes
    only the page number.
    """

    def __init__(
        self,
        first_request: dict[str, Any],
        cookies: list[dict],
    ) -> None:
        """
        Initialize the API client.

        Args:
            first_request: Browser-captured request information.
            cookies: Browser cookies from the active session.
        """
        request_url = str(
            first_request.get("url", "")
        ).strip()

        if not request_url:
            raise ValueError(
                "Captured Naukri request URL is missing."
            )

        parsed = urlparse(request_url)

        if not parsed.scheme or not parsed.netloc:
            raise ValueError(
                "Captured Naukri request URL is invalid."
            )

        self.base_url = (
            f"{parsed.scheme}://"
            f"{parsed.netloc}"
            f"{parsed.path}"
        )

        # IMPORTANT:
        # Preserve the exact captured query structure.
        #
        # We intentionally do NOT reconstruct this from
        # keyword/location because Naukri's API request may
        # contain additional internal/search parameters.
        self.query: dict[str, str] = {}

        for key, values in parse_qs(
            parsed.query,
            keep_blank_values=True,
        ).items():

            if values:
                self.query[key] = values[0]

        self.headers = dict(
            first_request.get("headers", {})
        )

        self.cookies = cookies

        self.session = self._create_session()

        logger.debug(
            "Naukri API initialized: base_url=%s",
            self.base_url,
        )

        logger.debug(
            "Captured query parameters: %s",
            sorted(self.query.keys()),
        )

    # ------------------------------------------------------------------
    # Session
    # ------------------------------------------------------------------

    def _create_session(self) -> requests.Session:
        """
        Create one requests session for the captured browser session.
        """
        session = requests.Session()

        session.headers.update(
            self.headers
        )

        for cookie in self.cookies:

            name = cookie.get("name")
            value = cookie.get("value")

            if not name or value is None:
                continue

            domain = cookie.get("domain")

            if domain:
                session.cookies.set(
                    name,
                    value,
                    domain=domain,
                )
            else:
                session.cookies.set(
                    name,
                    value,
                )

        return session

    # ------------------------------------------------------------------
    # Retry helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _backoff_seconds(attempt: int) -> float:
        """
        Calculate bounded exponential backoff with jitter.
        """
        exponential_delay = (
            INITIAL_BACKOFF_SECONDS
            * (2 ** (attempt - 1))
        )

        bounded_delay = min(
            exponential_delay,
            MAX_BACKOFF_SECONDS,
        )

        jitter = random.uniform(
            JITTER_MIN_SECONDS,
            JITTER_MAX_SECONDS,
        )

        return bounded_delay + jitter

    @staticmethod
    def _is_retryable_status(
        status_code: int,
    ) -> bool:
        """
        Return True when an HTTP status is transient.
        """
        return status_code in RETRYABLE_STATUS_CODES

    # ------------------------------------------------------------------
    # Page request
    # ------------------------------------------------------------------

    def _request_page(
        self,
        *,
        page: int,
        per_page: int,
    ) -> dict[str, Any]:
        """
        Fetch one page using the captured Naukri request.

        IMPORTANT
        ---------
        The captured query is preserved.

        Only:
            pageNo

        is changed for pagination.

        If the captured request contains:
            noOfResults

        it is updated to the requested page size.

        We intentionally do not inject:
            keyword
            location
            other reconstructed parameters

        because the browser-captured request is the source of truth.
        """

        params = self.query.copy()

        # Naukri's captured request already defines the correct
        # search parameters. Pagination changes only pageNo.
        params["pageNo"] = str(page)

        # Preserve the captured pagination parameter name.
        # If it exists, update its value to the requested page size.
        if "noOfResults" in params:
            params["noOfResults"] = str(per_page)

        logger.debug(
            "Naukri page %s request params: %s",
            page,
            params,
        )

        last_error: Exception | None = None

        for attempt in range(
            1,
            MAX_RETRIES + 1,
        ):

            try:

                response = self.session.get(
                    self.base_url,
                    params=params,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                    allow_redirects=True,
                )

                status_code = response.status_code

                # ------------------------------------------------------
                # Success
                # ------------------------------------------------------

                if status_code == 200:

                    try:
                        payload = response.json()
                    except ValueError as exc:
                        raise RuntimeError(
                            "Naukri returned HTTP 200 but "
                            "the response was not valid JSON."
                        ) from exc

                    if not isinstance(
                        payload,
                        dict,
                    ):
                        raise RuntimeError(
                            "Unexpected Naukri response type."
                        )

                    return payload

                # ------------------------------------------------------
                # Non-retryable errors
                # ------------------------------------------------------

                if not self._is_retryable_status(
                    status_code
                ):

                    # 400 is deliberately NOT retried.
                    #
                    # A 400 means the request itself needs fixing,
                    # not that another immediate retry will help.
                    raise RuntimeError(
                        "Naukri returned non-retryable "
                        f"HTTP {status_code} for page {page}."
                    )

                # ------------------------------------------------------
                # Retryable HTTP error
                # ------------------------------------------------------

                last_error = RuntimeError(
                    "Naukri returned retryable "
                    f"HTTP {status_code} for page {page}."
                )

                if attempt >= MAX_RETRIES:
                    break

                delay = self._backoff_seconds(
                    attempt
                )

                logger.warning(
                    "Naukri page %s returned HTTP %s "
                    "(attempt %s/%s). "
                    "Retrying in %.2fs.",
                    page,
                    status_code,
                    attempt,
                    MAX_RETRIES,
                    delay,
                )

                time.sleep(delay)

            except RuntimeError:
                raise

            except requests.RequestException as exc:

                last_error = exc

                if attempt >= MAX_RETRIES:
                    break

                delay = self._backoff_seconds(
                    attempt
                )

                logger.warning(
                    "Naukri page %s request failed "
                    "(attempt %s/%s): %s. "
                    "Retrying in %.2fs.",
                    page,
                    attempt,
                    MAX_RETRIES,
                    exc,
                    delay,
                )

                time.sleep(delay)

        raise RuntimeError(
            "Unable to fetch Naukri page "
            f"{page} after {MAX_RETRIES} attempts."
        ) from last_error

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_jobs(
        self,
        *,
        keyword: str,
        location: str | None = None,
        page: int = 1,
        per_page: int = 20,
        max_pages: int | None = None,
        max_jobs: int = DEFAULT_MAX_JOBS,
    ) -> dict[str, Any]:
        """
        Fetch Naukri search pages.

        Args:
            keyword:
                Original search keyword for logging/context only.

            location:
                Original search location for logging/context only.

            page:
                Starting page.

            per_page:
                Requested number of results per page.

            max_pages:
                Optional maximum number of pages.

            max_jobs:
                Maximum number of jobs to return.

        Returns:
            Mapper-compatible dictionary.
        """

        logger.info(
            "Starting Naukri API pagination: "
            "keyword=%s location=%s start_page=%s "
            "per_page=%s max_pages=%s max_jobs=%s",
            keyword,
            location,
            page,
            per_page,
            max_pages,
            max_jobs,
        )

        all_jobs: list[dict[str, Any]] = []
        seen_job_ids: set[str] = set()

        current_page = page
        pages_fetched = 0
        total_count = 0

        while True:

            logger.info(
                "Fetching Naukri page %s.",
                current_page,
            )

            response = self._request_page(
                page=current_page,
                per_page=per_page,
            )

            response_total = response.get(
                "totalCount"
            )

            if response_total is not None:
                total_count = response_total

            jobs = response.get(
                "jobDetails",
                [],
            )

            if not isinstance(
                jobs,
                list,
            ):
                raise RuntimeError(
                    "Unexpected Naukri response: "
                    "'jobDetails' is not a list."
                )

            pages_fetched += 1

            logger.info(
                "Naukri page %s returned %s jobs.",
                current_page,
                len(jobs),
            )

            if not jobs:
                logger.info(
                    "Naukri returned no jobs on page %s. "
                    "Pagination complete.",
                    current_page,
                )
                break

            added = 0
            duplicates = 0

            for job in jobs:

                if not isinstance(
                    job,
                    dict,
                ):
                    continue

                job_id = job.get(
                    "jobId"
                )

                if job_id is not None:

                    normalized_job_id = str(
                        job_id
                    ).strip()

                    if normalized_job_id:

                        if (
                            normalized_job_id
                            in seen_job_ids
                        ):
                            duplicates += 1
                            continue

                        seen_job_ids.add(
                            normalized_job_id
                        )

                all_jobs.append(job)
                added += 1

                # Exact max-jobs limit.
                if (
                    max_jobs is not None
                    and len(all_jobs)
                    >= max_jobs
                ):
                    all_jobs = all_jobs[
                        :max_jobs
                    ]

                    logger.info(
                        "Maximum job limit reached: %s",
                        max_jobs,
                    )

                    return {
                        "jobDetails": all_jobs,
                        "totalCount": (
                            total_count
                            if total_count
                            else len(all_jobs)
                        ),
                        "pagesFetched": pages_fetched,
                        "pageSize": per_page,
                        "jobsFetched": len(
                            all_jobs
                        ),
                        "limitReached": True,
                    }

            logger.info(
                "Page %s complete: "
                "added=%s duplicates=%s",
                current_page,
                added,
                duplicates,
            )

            # If fewer results than requested were returned,
            # this is normally the final page.
            if len(jobs) < per_page:
                logger.info(
                    "Naukri page %s contained fewer "
                    "than %s jobs. Pagination complete.",
                    current_page,
                    per_page,
                )
                break

            if (
                max_pages is not None
                and pages_fetched >= max_pages
            ):
                logger.info(
                    "Maximum page limit reached: %s",
                    max_pages,
                )
                break

            current_page += 1

            # Small pacing delay between normal pages.
            # This is separate from retry backoff.
            time.sleep(
                random.uniform(
                    0.5,
                    1.25,
                )
            )

        logger.info(
            "Naukri pagination completed: "
            "pages=%s jobs=%s total_count=%s",
            pages_fetched,
            len(all_jobs),
            total_count,
        )

        return {
            "jobDetails": all_jobs,
            "totalCount": (
                total_count
                if total_count
                else len(all_jobs)
            ),
            "pagesFetched": pages_fetched,
            "pageSize": per_page,
            "jobsFetched": len(all_jobs),
            "limitReached": False,
        }


# =============================================================================
# END OF FILE
# =============================================================================
