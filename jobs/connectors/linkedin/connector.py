"""
LinkedIn Jobs connector.

This is initially isolated for feasibility validation.
"""

from __future__ import annotations

from dataclasses import replace

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
        urls = self._api.search_jobs(
            keyword=request.keyword,
            location=request.location,
        )

        jobs: list[Job] = []
        seen_ids: set[str] = set()

        # Do not slice the discovered URLs before checking the cache.
        #
        # LinkedIn search results can contain jobs already discovered by
        # previous profile keywords. We should walk the complete cheap
        # search-result list and continue past cache hits until the
        # requested number of final jobs has been collected.
        for url in urls:
            # LinkedIn job IDs are embedded in /jobs/view/<id>/ URLs.
            source_job_id = url.rstrip("/").rsplit("/", 1)[-1]

            if not source_job_id or source_job_id in seen_ids:
                continue

            if source_job_id in self._job_cache:
                cached_job = self._job_cache[source_job_id]

                job = replace(
                    cached_job,
                    discovery_keyword=request.keyword,
                )

                if job.job_id:
                    seen_ids.add(job.job_id)
                    jobs.append(job)

                if (
                    request.max_jobs is not None
                    and len(jobs) >= request.max_jobs
                ):
                    break

                continue

            payload = self._api.fetch_job_page(url)

            if not payload:
                continue

            job = map_job(
                payload,
                job_url=url,
                discovery_keyword=request.keyword,
            )

            if not job.job_id or job.job_id in seen_ids:
                continue

            self._job_cache[source_job_id] = replace(job)

            seen_ids.add(job.job_id)
            jobs.append(job)

            if (
                request.max_jobs is not None
                and len(jobs) >= request.max_jobs
            ):
                break

        if request.max_jobs is not None:
            jobs = jobs[:request.max_jobs]

        return jobs
