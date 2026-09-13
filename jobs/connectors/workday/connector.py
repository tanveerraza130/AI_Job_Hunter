from __future__ import annotations

from pathlib import Path

from jobs.base import BaseConnector
from jobs.enums.connector_type import ConnectorType
from jobs.enums.portal import Portal
from jobs.search import SearchRequest

from .api import WorkdayAPI, WorkdayAPIError
from .discovery import WorkdayDiscovery
from .mapper import map_job


class WorkdayConnector(BaseConnector):
    PORTAL = Portal.WORKDAY
    CONNECTOR_TYPE = ConnectorType.API
    VERSION = "0.1.0"

    DISCOVERY_FILE = Path(
        "output/workday/discovered_boards.txt"
    )

    def __init__(self, context=None) -> None:
        self.context = context

    @property
    def name(self) -> str:
        return "Workday"

    @staticmethod
    def _matches(
        job,
        request: SearchRequest,
    ) -> bool:
        requested_location = (
            request.location or ""
        ).strip().lower()

        if not requested_location:
            return True

        location = (
            job.location or ""
        ).strip().lower()

        return requested_location in location

    def fetch_jobs(
        self,
        request: SearchRequest,
    ):
        jobs = []
        seen_ids: set[str] = set()

        # Refresh the generated discovery cache when possible.
        # If the public discovery source is unavailable or incomplete,
        # retain the last known-good cache instead of dropping coverage.
        cached_boards = WorkdayDiscovery.load(
            self.DISCOVERY_FILE
        )

        discovered_boards = WorkdayDiscovery(
            timeout=20
        ).discover_live()

        if discovered_boards:
            boards = sorted(
                set(cached_boards)
                | set(discovered_boards)
            )
            WorkdayDiscovery.save(
                boards,
                self.DISCOVERY_FILE,
            )
        else:
            boards = cached_boards

        if not boards:
            return jobs

        for host, tenant, site in boards:
            if (
                request.max_jobs is not None
                and len(jobs) >= request.max_jobs
            ):
                break

            try:
                api = WorkdayAPI(
                    host=host,
                    tenant=tenant,
                    site=site,
                )

                offset = 0
                page_size = 20

                while True:
                    if (
                        request.max_jobs is not None
                        and len(jobs) >= request.max_jobs
                    ):
                        break

                    payload = api.search_jobs(
                        search_text="",
                        offset=offset,
                        limit=page_size,
                    )

                    items = payload.get("jobPostings", [])

                    if not isinstance(items, list):
                        raise WorkdayAPIError(
                            "Workday response contained an invalid "
                            "'jobPostings' collection."
                        )

                    items = [
                        item for item in items
                        if isinstance(item, dict)
                    ]

                    if not items:
                        break

                    for item in items:
                        if (
                            request.max_jobs is not None
                            and len(jobs) >= request.max_jobs
                        ):
                            break

                        external_path = item.get(
                            "externalPath"
                        )

                        if not external_path:
                            continue

                        detail = api.fetch_job_detail(
                            external_path
                        )

                        job = map_job(
                            item,
                            detail,
                            company=tenant,
                            host=host,
                            tenant=tenant,
                            site=site,
                            discovery_keyword=request.keyword,
                        )

                        if not self._matches(
                            job,
                            request,
                        ):
                            continue

                        if job.job_id in seen_ids:
                            continue

                        seen_ids.add(job.job_id)
                        jobs.append(job)

                    if (
                        request.max_jobs is not None
                        and len(jobs) >= request.max_jobs
                    ):
                        break

                    offset += len(items)

                    total = payload.get("total")
                    if isinstance(total, int) and offset >= total:
                        break

                    if len(items) < page_size:
                        break

            except (
                WorkdayAPIError,
                ValueError,
            ):
                continue

        if request.max_jobs is not None:
            return jobs[: request.max_jobs]

        return jobs
