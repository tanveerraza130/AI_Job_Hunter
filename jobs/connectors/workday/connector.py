from __future__ import annotations

import os
import time
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
        debug_timing = os.getenv(
            "WORKDAY_DEBUG_TIMING",
            "",
        ).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

        debug_started = time.perf_counter()
        debug_search_calls = 0
        debug_search_time = 0.0
        debug_detail_calls = 0
        debug_detail_time = 0.0
        debug_items_seen = 0
        debug_location_matches = 0
        debug_duplicates = 0
        debug_jobs_matched = 0
        debug_errors = 0
        debug_boards = {}

        jobs = []
        seen_ids: set[str] = set()

        # Use the last known-good board cache for normal production runs.
        # Live discovery is intentionally opt-in because it performs multiple
        # Archive CDX requests plus one live validation request per candidate.
        # Set WORKDAY_REFRESH_DISCOVERY=1 when an explicit board refresh is
        # required.
        if self._discovered_boards is None:
            cached_boards = [
                board
                for board in WorkdayDiscovery.load(
                    self.DISCOVERY_FILE
                )
                if (
                    len(board) == 3
                    and board[0].lower().endswith(
                        ".myworkdayjobs.com"
                    )
                    and all(str(part).strip() for part in board)
                )
            ]

            refresh_discovery = os.getenv(
                "WORKDAY_REFRESH_DISCOVERY",
                "",
            ).strip().lower() in {
                "1",
                "true",
                "yes",
                "on",
            }

            if cached_boards and not refresh_discovery:
                boards = sorted(set(cached_boards))
            else:
                discovery = WorkdayDiscovery(timeout=20)

                discovered_boards = discovery.discover()
                candidates = sorted(
                    set(cached_boards)
                    | set(discovered_boards)
                )

                validated_boards = discovery.validate(
                    candidates
                )

                if validated_boards:
                    boards = sorted(set(validated_boards))
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

            board_key = f"{host}|{tenant}|{site}"

            debug_boards[board_key] = {
                "search_calls": 0,
                "search_time": 0.0,
                "items_seen": 0,
                "location_matches": 0,
                "duplicates": 0,
                "detail_calls": 0,
                "detail_time": 0.0,
                "jobs_matched": 0,
                "errors": 0,
            }

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

                applied_facets = None

                if request.location:
                    requested_location = (
                        request.location.strip().lower()
                    )

                    india_locations = {
                        "delhi",
                        "gurugram",
                        "gurgaon",
                        "noida",
                        "bangalore",
                        "bengaluru",
                        "mumbai",
                        "hyderabad",
                        "pune",
                        "kolkata",
                    }

                    if requested_location in india_locations:
                        applied_facets = {
                            "locationCountry": [
                                "c4f78be1a8f14da0ab49ce1162348a5e"
                            ]
                        }

                search_kwargs = {
                    "search_text": request.keyword,
                    "offset": offset,
                    "limit": page_size,
                }

                if applied_facets:
                    search_kwargs["applied_facets"] = (
                        applied_facets
                    )

                search_started = time.perf_counter()
                try:
                    payload = api.search_jobs(
                        **search_kwargs,
                    )
                except WorkdayAPIError:
                    debug_errors += 1
                    debug_boards[board_key]["errors"] += 1
                    raise
                finally:
                    elapsed = time.perf_counter() - search_started
                    debug_search_calls += 1
                    debug_search_time += elapsed
                    debug_boards[board_key]["search_calls"] += 1
                    debug_boards[board_key]["search_time"] += elapsed

                while pages_fetched < max_pages:
                    if (
                        request.max_jobs is not None
                        and len(jobs) >= request.max_jobs
                    ):
                        break

                    if offset > 0:
                        search_kwargs["offset"] = offset
                        search_started = time.perf_counter()
                        try:
                            payload = api.search_jobs(
                                **search_kwargs,
                            )
                        except WorkdayAPIError:
                            debug_errors += 1
                            debug_boards[board_key]["errors"] += 1
                            raise
                        finally:
                            elapsed = time.perf_counter() - search_started
                            debug_search_calls += 1
                            debug_search_time += elapsed
                            debug_boards[board_key]["search_calls"] += 1
                            debug_boards[board_key]["search_time"] += elapsed

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
                        debug_items_seen += 1
                        debug_boards[board_key]["items_seen"] += 1

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
                            debug_duplicates += 1
                            debug_boards[board_key]["duplicates"] += 1
                            continue

                        self._seen_external_paths.add(external_path)

                        search_location = str(
                            item.get("locationsText") or ""
                        ).strip()

                        if request.location and search_location:
                            requested_location = (
                                request.location.strip().lower()
                            )

                            aliases = {
                                "delhi": {
                                    "delhi",
                                    "new delhi",
                                },
                                "gurugram": {
                                    "gurugram",
                                    "gurgaon",
                                },
                                "noida": {"noida"},
                                "bangalore": {
                                    "bangalore",
                                    "bengaluru",
                                },
                                "mumbai": {"mumbai"},
                                "hyderabad": {"hyderabad"},
                                "pune": {"pune"},
                                "kolkata": {
                                    "kolkata",
                                    "calcutta",
                                },
                            }

                            targets = aliases.get(
                                requested_location,
                                {requested_location},
                            )

                            if not any(
                                target in search_location.lower()
                                for target in targets
                            ):
                                continue

                        debug_location_matches += 1
                        debug_boards[board_key]["location_matches"] += 1

                        detail_started = time.perf_counter()
                        try:
                            detail = api.fetch_job_detail(
                                external_path
                            )
                        except WorkdayAPIError:
                            debug_errors += 1
                            debug_boards[board_key]["errors"] += 1
                            raise
                        finally:
                            elapsed = time.perf_counter() - detail_started
                            debug_detail_calls += 1
                            debug_detail_time += elapsed
                            debug_boards[board_key]["detail_calls"] += 1
                            debug_boards[board_key]["detail_time"] += elapsed

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

                        debug_jobs_matched += 1
                        debug_boards[board_key]["jobs_matched"] += 1

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

        if debug_timing:
            debug_wall = time.perf_counter() - debug_started
            debug_unaccounted = (
                debug_wall
                - debug_search_time
                - debug_detail_time
            )

            print(
                "\n========== WORKDAY DEBUG TIMING =========="
            )
            print(f"boards_attempted={len(debug_boards)}")
            print(f"search_calls_total={debug_search_calls}")
            print(f"search_time_total_s={debug_search_time:.3f}")
            print(f"items_seen_total={debug_items_seen}")
            print(
                "location_matches_total="
                f"{debug_location_matches}"
            )
            print(f"duplicates_total={debug_duplicates}")
            print(f"detail_calls_total={debug_detail_calls}")
            print(f"detail_time_total_s={debug_detail_time:.3f}")
            print(f"jobs_matched_total={debug_jobs_matched}")
            print(f"errors_total={debug_errors}")
            print(f"wall_time_s={debug_wall:.3f}")
            print(f"unaccounted_wall_s={debug_unaccounted:.3f}")

            for key, stats in debug_boards.items():
                print(f"BOARD {key}")
                print(f"  {stats}")

            print("========== END WORKDAY DEBUG ==========")

        if request.max_jobs is not None:
            return jobs[: request.max_jobs]

        return jobs
