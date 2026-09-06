"""
Foundit connector.

Uses Foundit's structured public JSON search endpoint rather than
the HTML search pages.
"""

from __future__ import annotations

import logging
from typing import Any

from jobs.base import BaseConnector
from jobs.enums.connector_type import ConnectorType
from jobs.enums.portal import Portal
from jobs.job import Job
from jobs.search import SearchRequest

from .api import FounditAPI
from .mapper import map_job

logger = logging.getLogger(__name__)


class FounditConnector(BaseConnector):
    PORTAL = Portal.FOUNDIT
    CONNECTOR_TYPE = ConnectorType.API
    VERSION = "0.2.0"

    SEARCH_LIMIT = 50
    MAX_SEARCH_PAGES = 50

    def __init__(self, session=None) -> None:
        self._api = FounditAPI(session=session)

    @property
    def name(self) -> str:
        return "Foundit"

    def set_repositories(
        self,
        raw_repo: Any,
        session_id,
    ) -> None:
        self.raw_repo = raw_repo
        self.session_id = session_id

    @staticmethod
    def _extract_search_items(
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        response = payload.get("jobSearchResponse")

        if not isinstance(response, dict):
            return []

        data = response.get("data")

        if not isinstance(data, list):
            return []

        return [
            item
            for item in data
            if isinstance(item, dict)
            and item.get("jobId") is not None
            and item.get("type") not in {"adsense", "banner"}
        ]

    @staticmethod
    def _extract_paging(
        payload: dict[str, Any],
    ) -> tuple[int, int]:
        response = payload.get("jobSearchResponse")

        if not isinstance(response, dict):
            return 0, 0

        meta = response.get("meta")

        if not isinstance(meta, dict):
            return 0, 0

        paging = meta.get("paging")

        if not isinstance(paging, dict):
            return 0, 0

        try:
            total = int(paging.get("total") or 0)
            limit = int(paging.get("limit") or 0)
            return total, limit
        except (TypeError, ValueError):
            return 0, 0

    def fetch_jobs(
        self,
        request: SearchRequest,
    ) -> list[Job]:
        keyword = request.keyword.strip()

        if not keyword:
            return []

        location = (
            request.location.strip()
            if request.location
            else None
        )

        max_jobs = request.max_jobs

        if max_jobs is not None and max_jobs <= 0:
            return []

        limit = self.SEARCH_LIMIT
        jobs: list[Job] = []
        seen_ids: set[str] = set()
        start = 0

        for page_number in range(
            1,
            self.MAX_SEARCH_PAGES + 1,
        ):
            if max_jobs is not None and len(jobs) >= max_jobs:
                break

            payload = self._api.fetch_search_page(
                keyword=keyword,
                location=location,
                start=start,
                limit=limit,
            )

            if payload is None:
                logger.warning(
                    "Foundit search failed at start=%s "
                    "keyword=%r location=%r",
                    start,
                    keyword,
                    location,
                )
                break

            items = self._extract_search_items(payload)

            if not items:
                break

            total, response_limit = self._extract_paging(payload)

            if response_limit > 0:
                limit = response_limit

            added_this_page = 0

            for item in items:
                job_id = str(
                    item.get("jobId")
                    or item.get("id")
                )

                if not job_id or job_id in seen_ids:
                    continue

                seen_ids.add(job_id)

                # Enrich the search result with Foundit's detail record.
                # Detail enrichment is best-effort: if the detail request
                # fails, retain the original search result and continue.
                try:
                    detail = self._api.fetch_detail(job_id)
                except Exception as exc:
                    logger.warning(
                        "Foundit detail fetch failed for job %s: %s",
                        job_id,
                        exc,
                    )
                    detail = None

                if isinstance(detail, dict):
                    enriched_item = dict(item)
                    enriched_item.update(detail)
                    item = enriched_item

                try:
                    job = map_job(
                    item,
                    discovery_keyword=keyword,
                )
                except ValueError as exc:
                    logger.warning(
                        "Skipping malformed Foundit job %s: %s",
                        job_id,
                        exc,
                    )
                    continue

                jobs.append(job)
                added_this_page += 1

                if (
                    max_jobs is not None
                    and len(jobs) >= max_jobs
                ):
                    break

            logger.info(
                "Foundit page=%s start=%s received=%s "
                "added=%s total=%s",
                page_number,
                start,
                len(items),
                added_this_page,
                total,
            )

            if max_jobs is not None and len(jobs) >= max_jobs:
                break

            if total > 0:
                next_start = start + limit

                if next_start >= total:
                    break

                start = next_start
            else:
                if len(items) < limit:
                    break

                start += limit

        if max_jobs is not None:
            jobs = jobs[:max_jobs]

        logger.info(
            "Foundit normalized %s jobs for "
            "keyword=%r location=%r",
            len(jobs),
            keyword,
            location,
        )

        return jobs
