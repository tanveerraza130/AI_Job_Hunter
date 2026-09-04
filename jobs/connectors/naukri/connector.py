"""
Naukri connector.

Flow

Profile SearchRequest
        ↓
Naukri browser session
        ↓
Open search page
        ↓
Capture Search API response
        ↓
Browser-native pagination
        ↓
Deduplicate by Job ID
        ↓
Mapper
        ↓
List[Job]

This connector contains no profile-specific logic.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, urlencode, urlparse, urlunparse
from uuid import UUID

from playwright.sync_api import BrowserContext, Page, Response

from jobs.base import BaseConnector
from jobs.enums import ConnectorType, Portal
from jobs.job import Job
from jobs.search import SearchRequest

from .constants import BASE_URL, SEARCH_API_PATH, WAIT_UNTIL
from .mapper import map_jobs
from .session import NaukriSession

logger = logging.getLogger(__name__)


API_CAPTURE_TIMEOUT_SECONDS = 15
PAGE_NAVIGATION_TIMEOUT_SECONDS = 30

# Diagnostic experiment: bounded relevance pagination.
# Naukri sorting/filtering is not changed.
NAUKRI_EXPERIMENT_MAX_PAGES = 5
MAX_TOTAL_JOBS = 5000


class NaukriConnector(BaseConnector):
    """
    Naukri connector.

    Uses the Playwright browser session for both initial search
    and pagination. No requests-based API replay is performed.

    Responsibilities
    ----------------
    • Open search page
    • Capture Search API responses
    • Navigate pagination through browser
    • Deduplicate jobs by Job ID
    • Map responses into Job objects
    """

    PORTAL = Portal.NAUKRI
    CONNECTOR_TYPE = ConnectorType.API
    VERSION = "1.1.0"

    def __init__(self, context: BrowserContext) -> None:
        self.session = NaukriSession(context)
        self._raw_repo = None

        # Overall engine execution/session ID.
        self._session_id: UUID | None = None

        # Unique ID for the current SearchRequest.
        # Used only for raw-data persistence.
        self._raw_search_id: UUID | None = None

    @property
    def name(self) -> str:
        return "Naukri"

    @property
    def page(self) -> Page:
        """Return the active Playwright page."""
        return self.session.browser_page

    def set_repositories(
        self,
        raw_repo,
        session_id: UUID,
    ) -> None:
        """
        Set repository context for the overall engine execution.
        """
        self._raw_repo = raw_repo
        self._session_id = session_id

    def set_raw_search_id(
        self,
        raw_search_id: UUID,
    ) -> None:
        """
        Set the unique raw-search ID for the current SearchRequest.

        The overall execution/session ID is intentionally preserved
        separately from this per-request raw-data identifier.
        """
        self._raw_search_id = raw_search_id

    def _save_raw_data(
        self,
        page_no: int,
        request_url: str,
        request_method: str,
        request_headers: dict[str, str],
        request_query: dict[str, list[str]],
        response_data: dict[str, object],
        response_status: int = 200,
    ) -> None:
        """
        Save captured request/response data.

        Raw storage failures must not stop job collection.
        """
        if (
            self._raw_repo is None
            or self._session_id is None
            or self._raw_search_id is None
        ):
            return

        try:
            keyword = ""

            if request_query.get("keyword"):
                keyword = request_query["keyword"][0]

            location = ""

            if request_query.get("location"):
                location = request_query["location"][0]

            jobs = response_data.get("jobDetails", [])

            jobs_count = (
                len(jobs)
                if isinstance(jobs, list)
                else 0
            )

            self._raw_repo.save(
                search_id=str(self._raw_search_id),
                portal=self.PORTAL.value,
                keyword=keyword,
                location=location,
                page_no=page_no,
                request_url=request_url,
                request_method=request_method,
                request_headers=request_headers,
                request_query=request_query,
                response_json=response_data,
                response_status=response_status,
                jobs_count=jobs_count,
            )

            logger.debug(
                "Saved raw Naukri data for page %s.",
                page_no,
            )

        except Exception as exc:
            logger.warning(
                "Failed to save raw Naukri data for page %s: %s",
                page_no,
                exc,
            )

    @staticmethod
    def _save_debug_response(
        payload: dict[str, object],
        page_no: int,
    ) -> None:
        """
        Save a response payload for debugging.
        """
        debug_dir = Path("debug")
        debug_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        debug_file = (
            debug_dir
            / f"naukri_page_{page_no}.json"
        )

        with debug_file.open(
            "w",
            encoding="utf-8",
        ) as fp:
            json.dump(
                payload,
                fp,
                indent=2,
                ensure_ascii=False,
            )

        logger.info(
            "Saved API response -> %s",
            debug_file.resolve(),
        )

    def _build_search_url(
        self,
        request: SearchRequest,
    ) -> str:
        """
        Build the public Naukri search URL.

        Search URL generation remains driven entirely by
        SearchRequest.
        """
        keyword_slug = quote(
            request.keyword.strip().replace(" ", "-")
        )

        url = (
            f"{BASE_URL}/"
            f"{keyword_slug}-jobs"
        )

        if request.location:
            location_slug = quote(
                request.location.strip().replace(" ", "-")
            )

            url += (
                f"-in-{location_slug}"
            )

        return url

    @staticmethod
    def _build_page_url(
        search_url: str,
        page_no: int,
    ) -> str:
        """
        Build a browser navigation URL for a page.

        This does not construct an API request. It only changes
        the browser search-page pagination parameter.
        """
        parsed = urlparse(search_url)

        query = parse_qs(
            parsed.query,
            keep_blank_values=True,
        )

        query["pageNo"] = [str(page_no)]

        encoded_query = urlencode(
            query,
            doseq=True,
        )

        return urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                encoded_query,
                parsed.fragment,
            )
        )

    def _capture_search_response(
        self,
        navigation_url: str,
        page_no: int,
    ) -> tuple[
        dict[str, object],
        dict[str, object],
    ]:
        """
        Navigate with Playwright and capture the Search API response.

        This is the core browser-native pagination mechanism.

        No requests.Session is used here.
        """
        captured_payload: dict[str, object] | None = None
        captured_request: dict[str, object] | None = None
        parse_error: Exception | None = None

        def on_response(
            response: Response,
        ) -> None:
            nonlocal captured_payload
            nonlocal captured_request
            nonlocal parse_error

            if captured_payload is not None:
                return

            parsed_url = urlparse(
                response.url
            )

            if parsed_url.path != SEARCH_API_PATH:
                return

            if not response.ok:
                logger.warning(
                    "Naukri Search API returned HTTP %s: %s",
                    response.status,
                    response.url,
                )
                return

            request = response.request

            try:
                payload = response.json()
            except Exception as exc:
                parse_error = exc
                return

            if not isinstance(
                payload,
                dict,
            ):
                logger.warning(
                    "Unexpected Naukri response type: %s",
                    type(payload),
                )
                return

            captured_payload = payload

            captured_request = {
                "url": request.url,
                "method": request.method,
                "headers": dict(request.headers),
                "query": parse_qs(
                    urlparse(
                        request.url
                    ).query,
                    keep_blank_values=True,
                ),
                "status": response.status,
            }

        self.page.on(
            "response",
            on_response,
        )

        try:
            logger.info(
                "Opening Naukri search page %s: %s",
                page_no,
                navigation_url,
            )

            self.page.goto(
                navigation_url,
                wait_until=WAIT_UNTIL,
                timeout=(
                    PAGE_NAVIGATION_TIMEOUT_SECONDS
                    * 1000
                ),
            )

            deadline = (
                time.monotonic()
                + API_CAPTURE_TIMEOUT_SECONDS
            )

            while time.monotonic() < deadline:

                if captured_payload is not None:
                    break

                self.page.wait_for_timeout(100)

            if parse_error is not None:
                raise RuntimeError(
                    "Naukri Search API returned "
                    f"invalid JSON on page {page_no}: "
                    f"{parse_error}"
                ) from parse_error

            if captured_payload is None:
                debug_dir = Path("debug")

                debug_dir.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                screenshot_path = (
                    debug_dir
                    / f"naukri_page_{page_no}_not_found.png"
                )

                self.page.screenshot(
                    path=str(
                        screenshot_path
                    ),
                    full_page=True,
                )

                html_path = (
                    debug_dir
                    / f"naukri_page_{page_no}_not_found.html"
                )

                html_path.write_text(
                    self.page.content(),
                    encoding="utf-8",
                )

                raise RuntimeError(
                    "Naukri Search API response was "
                    f"not detected for page {page_no}. "
                    f"See {screenshot_path}."
                )

            request_data = (
                captured_request
                or {}
            )

            return (
                captured_payload,
                request_data,
            )

        finally:
            self.page.remove_listener(
                "response",
                on_response,
            )

    @staticmethod
    def _extract_job_ids(
        jobs: list[Job],
    ) -> set[str]:
        """
        Return normalized Job IDs.
        """
        return {
            str(job.job_id).strip()
            for job in jobs
            if getattr(
                job,
                "job_id",
                None,
            )
            and str(job.job_id).strip()
        }

    @staticmethod
    def _deduplicate_jobs(
        jobs: list[Job],
        seen_ids: set[str],
    ) -> tuple[list[Job], int]:
        """
        Deduplicate jobs by Job ID.

        Returns:
            tuple[list[Job], int]:
                New jobs and duplicate count.
        """
        unique_jobs: list[Job] = []
        duplicates = 0

        for job in jobs:

            job_id = getattr(
                job,
                "job_id",
                None,
            )

            if job_id is None:
                # Jobs without an ID cannot participate in
                # ID-based deduplication. Keep them rather than
                # silently discarding potentially valid data.
                unique_jobs.append(job)
                continue

            normalized_id = str(
                job_id
            ).strip()

            if not normalized_id:
                unique_jobs.append(job)
                continue

            if normalized_id in seen_ids:
                duplicates += 1
                continue

            seen_ids.add(
                normalized_id
            )

            unique_jobs.append(job)

        return (
            unique_jobs,
            duplicates,
        )

    def fetch_jobs(
        self,
        request: SearchRequest,
    ) -> list[Job]:
        """
        Fetch jobs from Naukri using browser-native pagination.

        The SearchRequest is the only source of search criteria.
        No profile-specific values exist in this connector.
        """
        logger.info(
            "Searching Naukri: keyword='%s', location='%s'",
            request.keyword,
            request.location,
        )

        if not getattr(self, "_session_initialized", False):
            self.session.load_cookies()
            self._session_initialized = True

        search_url = self._build_search_url(
            request
        )

        logger.debug(
            "Naukri search URL: %s",
            search_url,
        )

        all_jobs: list[Job] = []
        seen_job_ids: set[str] = set()

        current_page = 1
        max_pages = NAUKRI_EXPERIMENT_MAX_PAGES

        while True:

            if len(all_jobs) >= MAX_TOTAL_JOBS:
                logger.info(
                    "Global job limit reached: %s",
                    MAX_TOTAL_JOBS,
                )
                break

            if (
                request.max_jobs is not None
                and len(all_jobs)
                >= request.max_jobs
            ):
                logger.info(
                    "Requested job limit reached: %s",
                    request.max_jobs,
                )
                break

            if current_page == 1:
                navigation_url = search_url
            else:
                navigation_url = (
                    self._build_page_url(
                        search_url,
                        current_page,
                    )
                )

            payload, request_data = (
                self._capture_search_response(
                    navigation_url,
                    current_page,
                )
            )

            self._save_raw_data(
                page_no=current_page,
                request_url=str(
                    request_data.get(
                        "url",
                        navigation_url,
                    )
                ),
                request_method=str(
                    request_data.get(
                        "method",
                        "GET",
                    )
                ),
                request_headers=dict(
                    request_data.get(
                        "headers",
                        {},
                    )
                ),
                request_query=dict(
                    request_data.get(
                        "query",
                        {},
                    )
                ),
                response_data=payload,
                response_status=int(
                    request_data.get(
                        "status",
                        200,
                    )
                ),
            )

            self._save_debug_response(
                payload,
                current_page,
            )

            page_jobs = map_jobs(
            payload,
            discovery_keyword=request.keyword,
        )

            logger.info(
                "Page %s mapped: %s jobs.",
                current_page,
                len(page_jobs),
            )

            unique_jobs, duplicates = (
                self._deduplicate_jobs(
                    page_jobs,
                    seen_job_ids,
                )
            )

            all_jobs.extend(
                unique_jobs
            )

            logger.info(
                "Page %s: added=%s duplicates=%s total=%s",
                current_page,
                len(unique_jobs),
                duplicates,
                len(all_jobs),
            )

            if not page_jobs:
                logger.info(
                    "No jobs returned on page %s. "
                    "Pagination complete.",
                    current_page,
                )
                break

            if (
                len(page_jobs) < request.page_size
            ):
                logger.info(
                    "Page %s returned fewer jobs "
                    "than page size (%s < %s). "
                    "Pagination complete.",
                    current_page,
                    len(page_jobs),
                    request.page_size,
                )
                break

            if (
                request.max_jobs is not None
                and len(all_jobs)
                >= request.max_jobs
            ):
                break

            if len(all_jobs) >= MAX_TOTAL_JOBS:
                break

            if current_page >= max_pages:
                logger.info(
                    "Naukri diagnostic page limit reached: %s pages. "
                    "Stopping without applying freshness/relevance filters.",
                    max_pages,
                )
                break

            current_page += 1

        if request.max_jobs is not None:
            all_jobs = all_jobs[
                : request.max_jobs
            ]

        all_jobs = all_jobs[
            : MAX_TOTAL_JOBS
        ]

        logger.info(
            "Naukri search complete. "
            "Pages fetched=%s, jobs=%s, unique IDs=%s.",
            current_page,
            len(all_jobs),
            len(
                self._extract_job_ids(
                    all_jobs
                )
            ),
        )

        return all_jobs


# =============================================================================
# END OF FILE
# =============================================================================
