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
        self._seen_external_paths: set[str] = set()
        self._discovered_boards: list[tuple[str, str, str]] | None = None
        self._board_location_facets: dict[
            tuple[str, str, str],
            list[dict[str, str]],
        ] = {}

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

        aliases = {
            "delhi": {"delhi", "new delhi"},
            "gurugram": {"gurugram", "gurgaon"},
            "noida": {"noida"},
            "bangalore": {"bangalore", "bengaluru"},
            "mumbai": {"mumbai"},
            "hyderabad": {"hyderabad"},
            "pune": {"pune"},
            "kolkata": {"kolkata", "calcutta"},
        }

        targets = aliases.get(
            requested_location,
            {requested_location},
        )

        return any(
            target in location
            for target in targets
        )

    @staticmethod
    def _location_facet_ids(
        facets,
        requested_location: str,
    ) -> list[str]:
        requested = requested_location.strip().lower()

        if not requested:
            return []

        aliases = {
            "delhi": {"delhi", "new delhi"},
            "gurugram": {"gurugram", "gurgaon"},
            "noida": {"noida"},
            "bangalore": {"bangalore", "bengaluru"},
            "mumbai": {"mumbai"},
            "hyderabad": {"hyderabad"},
            "pune": {"pune"},
            "kolkata": {"kolkata", "calcutta"},
        }

        targets = aliases.get(
            requested,
            {requested},
        )

        ids: list[str] = []

        def collect(values) -> None:
            if not isinstance(values, list):
                return

            for value in values:
                if not isinstance(value, dict):
                    continue

                descriptor = str(
                    value.get("descriptor") or ""
                ).strip().lower()

                facet_id = str(
                    value.get("id") or ""
                ).strip()

                if facet_id and any(
                    target in descriptor
                    for target in targets
                ):
                    ids.append(facet_id)

                collect(value.get("values"))

        collect(facets)

        return list(dict.fromkeys(ids))

    def fetch_jobs(
        self,
        request: SearchRequest,
    ):
        jobs = []
        seen_ids: set[str] = set()

        # Discover and validate Workday boards once per connector run.
        # If the public discovery source is unavailable or incomplete,
        # retain the last known-good cache instead of dropping coverage.
        if self._discovered_boards is None:
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

            self._discovered_boards = boards

        boards = self._discovered_boards

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
                max_pages = 2
                pages_fetched = 0

                if request.location:
                    board_key = (host, tenant, site)

                    if board_key not in self._board_location_facets:
                        facet_payload = api.search_jobs(
                            search_text="",
                            offset=0,
                            limit=page_size,
                        )

                        location_values = []

                        def find_location_facet(values) -> None:
                            if not isinstance(values, list):
                                return

                            for value in values:
                                if not isinstance(value, dict):
                                    continue

                                if (
                                    value.get("facetParameter")
                                    == "locations"
                                ):
                                    collect_location_values(
                                        value.get("values")
                                    )
                                    return

                                find_location_facet(
                                    value.get("values")
                                )

                        def collect_location_values(values) -> None:
                            if not isinstance(values, list):
                                return

                            for value in values:
                                if not isinstance(value, dict):
                                    continue

                                descriptor = str(
                                    value.get("descriptor") or ""
                                ).strip()

                                facet_id = str(
                                    value.get("id") or ""
                                ).strip()

                                if facet_id and descriptor:
                                    location_values.append(
                                        {
                                            "descriptor": descriptor,
                                            "id": facet_id,
                                        }
                                    )

                                collect_location_values(
                                    value.get("values")
                                )

                        find_location_facet(
                            facet_payload.get("facets", [])
                        )

                        self._board_location_facets[board_key] = (
                            location_values
                        )

                    location_facet_ids = self._location_facet_ids(
                        self._board_location_facets[board_key],
                        request.location,
                    )

                    if not location_facet_ids:
                        continue

                    payload = api.search_jobs(
                        search_text=request.keyword,
                        offset=0,
                        limit=page_size,
                        applied_facets={
                            "locations": location_facet_ids,
                        },
                    )
                else:
                    payload = api.search_jobs(
                        search_text=request.keyword,
                        offset=offset,
                        limit=page_size,
                    )

                while pages_fetched < max_pages:
                    if (
                        request.max_jobs is not None
                        and len(jobs) >= request.max_jobs
                    ):
                        break

                    if offset > 0:
                        payload = api.search_jobs(
                            search_text=request.keyword,
                            offset=offset,
                            limit=page_size,
                            applied_facets=(
                                {
                                    "locations": location_facet_ids,
                                }
                                if request.location
                                else None
                            ),
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

                        if external_path in self._seen_external_paths:
                            continue

                        self._seen_external_paths.add(external_path)

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
                    pages_fetched += 1

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
