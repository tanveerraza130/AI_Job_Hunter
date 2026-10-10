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
        self._registry = None
        self._candidate_gate = None

        # Execution-local cache.
        #
        # LinkedIn profile searches can surface the same job under
        # multiple keywords. Cache normalized jobs by source job ID
        # so an already-fetched detail page is not requested again
        # during the same connector execution.
        self._job_cache: dict[str, Job] = {}

    def set_registry(self, registry) -> None:
        """Set the central job registry for early candidate filtering."""
        self._registry = registry

    def set_candidate_gate(self, gate) -> None:
        """Set the engine-owned early candidate filter."""
        self._candidate_gate = gate

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

        candidates: list[tuple[str, str]] = []

        for card in cards:
            source_job_id = str(card.get("job_id") or "").strip()
            job_url = str(card.get("job_url") or "").strip()
            posted_date = card.get("posted_date")

            if not source_job_id or not job_url:
                continue

            # Deduplicate BEFORE any detail fetch or registry lookup.
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

            candidates.append((source_job_id, job_url))

        if not candidates:
            return (
                jobs[:request.max_jobs]
                if request.max_jobs is not None
                else jobs
            )

        # Early registry/profile gate.
        # Only candidates that still require processing proceed to
        # LinkedIn detail-page requests.
        fetch_candidates = candidates

        if self._candidate_gate is not None:
            candidate_ids = [
                source_job_id
                for source_job_id, _ in candidates
            ]

            allowed_ids = self._candidate_gate(
                portal=self.PORTAL.value,
                portal_job_ids=candidate_ids,
            )

            fetch_candidates = [
                item
                for item in candidates
                if item[0] in allowed_ids
            ]

        # Respect max_jobs before issuing expensive detail requests.
        if request.max_jobs is not None:
            remaining = request.max_jobs - len(jobs)
            if remaining <= 0:
                return jobs[:request.max_jobs]
            fetch_candidates = fetch_candidates[:remaining]

        pending: list[tuple[str, str]] = list(fetch_candidates)

        def fetch_detail(item: tuple[str, str]):
            source_job_id, job_url = item
            payload = self._api.fetch_job_page(job_url)
            return source_job_id, job_url, payload

        if pending:
            with ThreadPoolExecutor(max_workers=24) as executor:
                for source_job_id, job_url, payload in executor.map(
                    fetch_detail, pending
                ):
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

        return (
            jobs[:request.max_jobs]
            if request.max_jobs is not None
            else jobs
        )
