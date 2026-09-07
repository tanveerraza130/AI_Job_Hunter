"""
LinkedIn Jobs connector.

This is initially isolated for feasibility validation.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta

from jobs.base import BaseConnector
from jobs.enums import ConnectorType, Portal
from jobs.job import Job
from jobs.search import SearchRequest

from .api import LinkedInAPI
from .mapper import map_job


class LinkedInConnector(BaseConnector):
    """Fetch public LinkedIn Jobs into the canonical Job contract."""

    PORTAL = Portal.LINKEDIN
    CONNECTOR_TYPE = ConnectorType.API
    VERSION = "0.1.0"

    def __init__(self, context=None) -> None:
        self.context = context
        self._api = LinkedInAPI()

        # Execution-local cache.
        #
        # LinkedIn profile searches can surface the same job under
        # multiple keywords. Cache normalized jobs by source job ID
        # so an already-fetched detail page is not requested again
        # during the same connector execution.
        self._job_cache: dict[str, Job] = {}

    @property
    def name(self) -> str:
        return "LinkedIn"

    def fetch_jobs(self, request: SearchRequest) -> list[Job]:
        """Fetch only unique LinkedIn jobs posted within 15 days."""

        cards = self._api.search_job_cards(
            keyword=request.keyword,
            location=request.location,
        )

        jobs: list[Job] = []
        seen_ids: set[str] = set()

        # LinkedIn-specific freshness window.
        cutoff = date.today() - timedelta(days=15)

        for card in cards:
            source_job_id = str(card.get("job_id") or "").strip()
            job_url = str(card.get("job_url") or "").strip()
            posted_date = card.get("posted_date")

            if not source_job_id or not job_url:
                continue

            # Deduplicate BEFORE detail fetch.
            if source_job_id in seen_ids:
                continue

            seen_ids.add(source_job_id)

            # Missing/invalid dates are excluded.
            if not posted_date:
                continue

            try:
                posted = date.fromisoformat(posted_date)
            except ValueError:
                continue

            # Never open an old LinkedIn detail page.
            if posted < cutoff:
                continue

            # Existing connector cache.
            if source_job_id in self._job_cache:
                job = self._job_cache[source_job_id]
                jobs.append(job)

                if (
                    request.max_jobs is not None
                    and len(jobs) >= request.max_jobs
                ):
                    break

                continue

            # Expensive detail request happens only here,
            # after deduplication and the 15-day filter.
            payload = self._api.fetch_job_page(job_url)

            if not payload:
                continue

            job = map_job(
                payload,
                job_url=job_url,
                discovery_keyword=request.keyword,
            )

            if not job.job_id:
                continue

            self._job_cache[source_job_id] = job
            jobs.append(job)

            if (
                request.max_jobs is not None
                and len(jobs) >= request.max_jobs
            ):
                break

        return jobs
