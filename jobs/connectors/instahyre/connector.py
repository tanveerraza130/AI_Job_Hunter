"""
Instahyre connector.

Uses Instahyre's public job-search feed as a progressively cached
inventory. Pages fetched during one connector lifecycle are reused
for subsequent SearchRequest calls.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any

from jobs.base import BaseConnector
from jobs.enums.connector_type import ConnectorType
from jobs.enums.portal import Portal
from jobs.job import Job
from jobs.search import SearchRequest

from .api import InstahyreAPI, InstahyreAPIError
from .mapper import map_job

logger = logging.getLogger(__name__)


class InstahyreConnector(BaseConnector):
    PORTAL = Portal.INSTAHYRE
    CONNECTOR_TYPE = ConnectorType.API
    VERSION = "0.3.0"

    PAGE_SIZE = 35
    MAX_PAGES = 50

    # Never hammer the public endpoint.
    MIN_REQUEST_INTERVAL = 2.0

    # Maximum time spent waiting for a source response during
    # one connector request.
    MAX_TOTAL_BACKOFF = 60

    def __init__(self, context: Any = None) -> None:
        self.context = context
        self._api = InstahyreAPI()

        # Request pacing is shared across searches, but search results
        # are no longer stored as a broad global inventory.
        self._last_request_at = 0.0

    @property
    def name(self) -> str:
        return "Instahyre"

    def set_repositories(
        self,
        raw_repo: Any,
        session_id,
    ) -> None:
        self.raw_repo = raw_repo
        self.session_id = session_id

    @staticmethod
    def _normalize(value: Any) -> str:
        return re.sub(
            r"\s+",
            " ",
            str(value or "").lower(),
        ).strip()

    @staticmethod
    def _job_id(item: dict[str, Any]) -> str:
        value = item.get("id")

        if value is not None:
            value = str(value).strip()
            if value:
                return value

        resource_uri = str(
            item.get("resource_uri") or ""
        ).strip()

        if resource_uri:
            return resource_uri.rstrip("/").split("/")[-1]

        return ""

    @classmethod
    def _keyword_match(
        cls,
        item: dict[str, Any],
        keyword: str,
    ) -> bool:
        keyword = cls._normalize(keyword)

        if not keyword:
            return True

        title = cls._normalize(
            " ".join(
                [
                    str(item.get("title") or ""),
                    str(item.get("candidate_title") or ""),
                ]
            )
        )

        if not title:
            return False

        # Exact phrase match in the job title.
        if keyword in title:
            return True

        tokens = [
            token
            for token in re.findall(
                r"[a-z0-9+#.-]+",
                keyword,
            )
            if len(token) >= 3
        ]

        if not tokens:
            return False

        title_tokens = set(
            re.findall(
                r"[a-z0-9+#.-]+",
                title,
            )
        )

        # Multi-word searches must be represented entirely
        # by the job title. Do not construct a role from skills.
        if len(tokens) > 1:
            return all(
                token in title_tokens
                for token in tokens
            )

        # Single-word searches are also title-only.
        return tokens[0] in title_tokens

    @classmethod
    def _location_match(
        cls,
        item: dict[str, Any],
        location: str,
    ) -> bool:
        location = cls._normalize(location)

        if not location:
            return True

        raw_locations = item.get("locations")

        if isinstance(raw_locations, list):
            source = ", ".join(
                str(value)
                for value in raw_locations
            )
        else:
            source = str(raw_locations or "")

        source = cls._normalize(source)

        if not source:
            return True

        # Common NCR naming variants.
        aliases = {
            "gurugram": ["gurugram", "gurgaon"],
            "gurgaon": ["gurgaon", "gurugram"],
            "delhi": [
                "delhi",
                "new delhi",
                "gurgaon",
                "gurugram",
                "noida",
                "greater noida",
                "faridabad",
            ],
            "delhi ncr": [
                "delhi",
                "new delhi",
                "gurgaon",
                "gurugram",
                "noida",
                "greater noida",
                "faridabad",
            ],
        }

        accepted = aliases.get(
            location,
            [location],
        )

        return any(
            candidate in source
            for candidate in accepted
        )

    def _pace(self) -> None:
        elapsed = time.monotonic() - self._last_request_at

        if elapsed < self.MIN_REQUEST_INTERVAL:
            time.sleep(
                self.MIN_REQUEST_INTERVAL - elapsed
            )

    def _fetch_page(
        self,
        request: SearchRequest,
        offset: int,
    ) -> list[dict[str, Any]]:
        """Fetch one server-filtered Instahyre search page."""

        self._pace()

        try:
            payload = self._api.fetch_page(
                keyword=str(request.keyword or "").strip(),
                location=str(request.location or "").strip(),
                offset=offset,
            )
        except InstahyreAPIError as exc:
            logger.warning(
                "Instahyre search temporarily unavailable "
                "(keyword=%r location=%r offset=%s): %s",
                request.keyword,
                request.location,
                offset,
                exc,
            )
            return []

        self._last_request_at = time.monotonic()

        objects = payload.get("objects")

        if not isinstance(objects, list):
            logger.warning(
                "Instahyre returned invalid objects "
                "(keyword=%r location=%r offset=%s)",
                request.keyword,
                request.location,
                offset,
            )
            return []

        return [
            item
            for item in objects
            if isinstance(item, dict)
        ]

    def _find_matches(
        self,
        request: SearchRequest,
        items: list[dict[str, Any]],
    ) -> list[Job]:
        """Enrich and map server-filtered Instahyre search results."""

        keyword = str(
            request.keyword or ""
        ).strip()

        result: list[Job] = []
        seen: set[str] = set()

        for item in items:
            job_id = self._job_id(item)

            if not job_id or job_id in seen:
                continue

            seen.add(job_id)

            try:
                detail: dict[str, Any] = {}

                job_url = str(
                    item.get("public_url")
                    or item.get("publicUrl")
                    or item.get("url")
                    or ""
                ).strip()

                if job_url:
                    try:
                        html = self._api.fetch_job_page(
                            job_url
                        )

                        if html:
                            detail = (
                                self._api.extract_job_page_data(
                                    html
                                )
                            )

                            if detail.get("description"):
                                logger.debug(
                                    "Enriched Instahyre job %s "
                                    "with full public JD",
                                    job_id,
                                )
                            else:
                                logger.debug(
                                    "No full JD extracted "
                                    "for Instahyre job %s",
                                    job_id,
                                )

                    except Exception as exc:
                        logger.warning(
                            "Instahyre JD enrichment failed "
                            "for job %s: %s",
                            job_id,
                            exc,
                        )

                result.append(
                    map_job(
                        item,
                        discovery_keyword=keyword,
                        detail=detail,
                    )
                )

            except ValueError as exc:
                logger.warning(
                    "Skipping malformed Instahyre job %s: %s",
                    job_id,
                    exc,
                )

            if (
                request.max_jobs is not None
                and len(result) >= request.max_jobs
            ):
                break

        return result

    def fetch_jobs(
        self,
        request: SearchRequest,
    ) -> list[Job]:
        """Fetch jobs using Instahyre's public server-side search."""

        if not request.keyword:
            return []

        if (
            request.max_jobs is not None
            and request.max_jobs <= 0
        ):
            return []

        # Instahyre's public endpoint currently returns 35 objects
        # per search page. Fetch only the requested keyword/location
        # inventory instead of downloading the broad global feed.
        page_size = self.PAGE_SIZE
        offset = 0
        pages_fetched = 0
        all_items: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        while pages_fetched < self.MAX_PAGES:
            items = self._fetch_page(
                request,
                offset,
            )

            if not items:
                break

            for item in items:
                job_id = self._job_id(item)

                if not job_id or job_id in seen_ids:
                    continue

                seen_ids.add(job_id)
                all_items.append(item)

            pages_fetched += 1

            # We can stop as soon as we have enough candidates to
            # satisfy max_jobs. Final profile relevance remains the
            # responsibility of the existing Engine pipeline.
            if (
                request.max_jobs is not None
                and len(all_items) >= request.max_jobs
            ):
                break

            if len(items) < page_size:
                break

            offset += page_size

        return self._find_matches(
            request,
            all_items,
        )
