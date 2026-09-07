"""
LinkedIn Jobs connector.

This is initially isolated for feasibility validation.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
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

        pending: list[tuple[str, str]] = []

        def fetch_detail(item: tuple[str, str]):
            source_job_id, job_url = item
            payload = self._api.fetch_job_page(job_url)
            return source_job_id, job_url, payload

        def process_pending(items: list[tuple[str, str]]) -> None:
            with ThreadPoolExecutor(max_workers=5) as executor:
                results = executor.map(fetch_detail, items)

                for source_job_id, job_url, payload in results:
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
                jobs.append(self._job_cache[source_job_id])

                if (
                    request.max_jobs is not None
                    and len(jobs) >= request.max_jobs
                ):
                    break

                continue

            pending.append((source_job_id, job_url))

            # Fetch a bounded batch as soon as five candidates are ready,
            # or when only the remaining max_jobs capacity is available.
            if len(pending) >= 5 or (
                request.max_jobs is not None
                and len(pending) >= request.max_jobs - len(jobs)
            ):
                process_pending(pending)
                pending.clear()

                if (
                    request.max_jobs is not None
                    and len(jobs) >= request.max_jobs
                ):
                    break

        # Continue through remaining candidates in bounded batches.
        while pending:
            if request.max_jobs is not None:
                remaining = request.max_jobs - len(jobs)
                if remaining <= 0:
                    break
                batch_size = min(5, remaining)
            else:
                batch_size = 5

            batch = pending[:batch_size]
            pending = pending[batch_size:]

            process_pending(batch)

            if (
                request.max_jobs is not None
                and len(jobs) >= request.max_jobs
            ):
                break

        return (
            jobs[:request.max_jobs]
            if request.max_jobs is not None
            else jobs
        )
