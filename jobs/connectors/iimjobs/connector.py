"""
IIMJobs connector.

V2 connector implementation for IIMJobs.
"""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from typing import Any
from uuid import UUID

from jobs.base import BaseConnector
from jobs.enums import ConnectorType, Portal
from jobs.job import Job
from jobs.search import SearchRequest

from .api import IIMJobsAPI
from .mapper import map_job, map_jobs


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Verified IIMJobs public keyword IDs.
#
# Unsupported profile keywords are intentionally skipped rather than sent
# with keywordId=-1, because the public endpoint returns no jobs for -1.
# ---------------------------------------------------------------------------
KEYWORD_IDS: dict[str, int] = {
    "crm": 189,
    "campaign management": 642,
    "automation": 1885,
}


# ---------------------------------------------------------------------------
# Conservative CRM-profile → IIMJobs taxonomy translation.
#
# These are source-local mappings. The CRM profile itself remains unchanged.
# The original profile keyword is preserved as Job.discovery_keyword.
# ---------------------------------------------------------------------------
PROFILE_KEYWORD_ALIASES: dict[str, str] = {
    # CRM taxonomy.
    "crm executive": "crm",
    "crm analyst": "crm",
    "crm analytics manager": "crm",
    "crm specialist": "crm",
    "crm manager": "crm",
    "crm lead": "crm",
    "crm head": "crm",
    "head of crm": "crm",
    "vp crm": "crm",
    "crm & retention head": "crm",
    "crm team lead": "crm",
    "lifecycle marketing": "crm",
    "lifecycle marketing executive": "crm",
    "lifecycle marketing specialist": "crm",
    "lifecycle marketing manager": "crm",
    "lifecycle marketing lead": "crm",
    "customer lifecycle manager": "crm",
    "retention manager": "crm",
    "retention marketing manager": "crm",
    "retention specialist": "crm",
    "customer retention manager": "crm",
    "customer marketing manager": "crm",
    "consumer engagement manager": "crm",
    "crm & loyalty manager": "crm",
    "loyalty marketing manager": "crm",
    "database marketing manager": "crm",
    "customer value management": "crm",
    "cvm": "crm",
    "customer engagement manager": "crm",
    "customer engagement lead": "crm",
    "growth crm manager": "crm",

    # Automation taxonomy.
    "marketing automation manager": "automation",
    "marketing automation specialist": "automation",
    "marketing automation lead": "automation",
    "behavioral marketing": "automation",
    "martech manager": "automation",
    "martech operations manager": "automation",
    "marketing technology manager": "automation",

    # Campaign-management taxonomy.
    "crm campaign manager": "campaign management",
    "campaign manager crm": "campaign management",
    "campaign operations manager": "campaign management",
}


# ---------------------------------------------------------------------------
# Verified IIMJobs public location IDs.
# ---------------------------------------------------------------------------
LOCATION_IDS: dict[str, int] = {
    "delhi ncr": 1,
    "delhi": 36,
    "gurgaon": 37,
    "gurugram": 37,
    "gurgaon/gurugram": 37,
    "noida": 38,
    "greater noida": 39,
    "faridabad": 40,
    "haryana": 16,
    "manesar": 138,
}


DETAIL_WORKERS = 4

DEFAULT_REF_POOLS: dict[int, str] = {
    1: json.dumps(
        {"loc": "Delhi NCR_Delhi"},
        separators=(",", ":"),
    ),
    36: json.dumps(
        {"loc": "Delhi NCR_Delhi"},
        separators=(",", ":"),
    ),
    37: json.dumps(
        {"loc": "Gurgaon/Gurugram"},
        separators=(",", ":"),
    ),
    38: json.dumps(
        {"loc": "Noida"},
        separators=(",", ":"),
    ),
    39: json.dumps(
        {"loc": "Greater Noida"},
        separators=(",", ":"),
    ),
    40: json.dumps(
        {"loc": "Faridabad"},
        separators=(",", ":"),
    ),
    16: json.dumps(
        {"loc": "Haryana"},
        separators=(",", ":"),
    ),
    138: json.dumps(
        {"loc": "Manesar"},
        separators=(",", ":"),
    ),
}


class IIMJobsConnector(BaseConnector):
    """IIMJobs job connector."""

    PORTAL = Portal.IIMJOBS
    CONNECTOR_TYPE = ConnectorType.API
    VERSION = "0.2.0"

    def __init__(
        self,
        context: Any = None,
    ) -> None:
        self.context = context
        self._raw_repo = None
        self._session_id: UUID | None = None
        self._api = IIMJobsAPI()

        # Connector-local cache prevents repeated profile keywords that map
        # to the same IIMJobs taxonomy from issuing identical source calls.
        self._job_cache: dict[
            tuple[int, int, int, int | None],
            list[Job],
        ] = {}

    @property
    def name(self) -> str:
        return "IIMJobs"

    def set_repositories(
        self,
        raw_repo: Any,
        session_id: UUID,
    ) -> None:
        self._raw_repo = raw_repo
        self._session_id = session_id

    @staticmethod
    def _keyword_id(
        keyword: str | None,
    ) -> int | None:
        normalized = (
            (keyword or "")
            .strip()
            .casefold()
        )

        if not normalized:
            return None

        source_keyword = PROFILE_KEYWORD_ALIASES.get(
            normalized,
            normalized,
        )

        return KEYWORD_IDS.get(source_keyword)

    @staticmethod
    def _location_config(
        location: str | None,
    ) -> tuple[int, str] | None:
        normalized = (
            (location or "")
            .strip()
            .casefold()
        )

        location_id = LOCATION_IDS.get(normalized)

        if location_id is None:
            return None

        ref_pool = DEFAULT_REF_POOLS.get(
            location_id,
            json.dumps(
                {"loc": str(location).strip()},
                separators=(",", ":"),
            ),
        )

        return location_id, ref_pool

    @staticmethod
    def _records_from_payload(
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        feed = payload.get("data")

        if isinstance(feed, dict):
            records = (
                feed.get("jobfeed")
                or feed.get("jobs")
                or feed.get("results")
                or []
            )
        elif isinstance(feed, list):
            records = feed
        else:
            records = (
                payload.get("jobfeed")
                or payload.get("jobs")
                or payload.get("results")
                or []
            )

        if not isinstance(records, list):
            return []

        return [
            record
            for record in records
            if isinstance(record, dict)
        ]

    def _fetch_detail(
        self,
        job_id: str,
        discovery_keyword: str,
    ) -> Job | None:
        try:
            payload = self._api.fetch_detail(
                job_code=job_id,
            )

            detail_data = payload.get("data")

            if not isinstance(detail_data, dict):
                logger.warning(
                    "IIMJobs detail %s returned no detail object.",
                    job_id,
                )
                return None

            return map_job(
                detail_data,
                discovery_keyword=discovery_keyword,
            )

        except Exception:
            logger.exception(
                "IIMJobs detail fetch failed for job %s.",
                job_id,
            )
            return None

    def fetch_jobs(
        self,
        request: SearchRequest,
    ) -> list[Job]:
        """
        Fetch IIMJobs listings and normalize them.

        Search discovery is performed through the verified public
        keyword endpoint. Unsupported keywords or locations are skipped
        without making a source request.
        """
        keyword_id = self._keyword_id(
            request.keyword
        )

        if keyword_id is None:
            logger.info(
                "Skipping unsupported IIMJobs keyword=%s.",
                request.keyword,
            )
            return []

        location_config = self._location_config(
            request.location
        )

        if location_config is None:
            logger.info(
                "Skipping unsupported IIMJobs location=%s.",
                request.location,
            )
            return []

        location_id, ref_pool = location_config

        page_size = max(
            int(request.page_size or 20),
            1,
        )

        max_jobs = (
            int(request.max_jobs)
            if request.max_jobs is not None
            else None
        )

        if max_jobs is not None and max_jobs <= 0:
            return []

        cache_key = (
            keyword_id,
            location_id,
            page_size,
            max_jobs,
        )

        cached_jobs = self._job_cache.get(cache_key)

        if cached_jobs is not None:
            logger.info(
                "IIMJobs cache hit for keyword=%s location=%s "
                "(keyword_id=%s, location_id=%s).",
                request.keyword,
                request.location,
                keyword_id,
                location_id,
            )

            return [
                replace(
                    job,
                    discovery_keyword=request.keyword,
                )
                for job in cached_jobs
            ]

        listing_records: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        page = 0

        while True:
            payload = self._api.fetch_keyword(
                page=page,
                keyword_id=keyword_id,
                location_id=location_id,
                ref_pool=ref_pool,
            )

            records = self._records_from_payload(
                payload
            )

            if not records:
                break

            for record in records:
                job_id = str(
                    record.get("id")
                    or record.get("refJobId")
                    or ""
                ).strip()

                if not job_id or job_id in seen_ids:
                    continue

                seen_ids.add(job_id)
                listing_records.append(record)

                if (
                    max_jobs is not None
                    and len(listing_records) >= max_jobs
                ):
                    break

            if (
                max_jobs is not None
                and len(listing_records) >= max_jobs
            ):
                break

            has_more = payload.get("hasMore")

            if has_more is False:
                break

            if has_more is None and len(records) < page_size:
                break

            page += 1

        if not listing_records:
            logger.info(
                "IIMJobs returned no listings for keyword=%s "
                "location=%s.",
                request.keyword,
                request.location,
            )
            return []

        # Map listing data first so the normalized job ID is known before
        # detail requests are scheduled. Only one detail request is issued
        # for each unique source job ID.
        listing_jobs = map_jobs(
            listing_records,
            discovery_keyword=request.keyword,
        )

        jobs_by_id = {
            job.job_id: job
            for job in listing_jobs
            if job.job_id
        }

        if not jobs_by_id:
            return []

        jobs: list[Job] = []

        with ThreadPoolExecutor(
            max_workers=DETAIL_WORKERS,
            thread_name_prefix="iimjobs-detail",
        ) as executor:
            futures = {
                executor.submit(
                    self._fetch_detail,
                    job_id,
                    request.keyword,
                ): job_id
                for job_id in jobs_by_id
            }

            for future in as_completed(futures):
                job_id = futures[future]

                try:
                    job = future.result()
                except Exception:
                    logger.exception(
                        "Unexpected IIMJobs detail worker failure "
                        "for job %s.",
                        job_id,
                    )
                    continue

                if job is not None:
                    jobs.append(job)

        jobs = jobs[:max_jobs] if max_jobs is not None else jobs

        self._job_cache[cache_key] = [
            replace(job)
            for job in jobs
        ]

        logger.info(
            "IIMJobs fetched %s jobs for keyword=%s location=%s "
            "(keyword_id=%s, location_id=%s, listing_ids=%s, "
            "detail_workers=%s).",
            len(jobs),
            request.keyword,
            request.location,
            keyword_id,
            location_id,
            len(jobs_by_id),
            DETAIL_WORKERS,
        )

        return [
            replace(
                job,
                discovery_keyword=request.keyword,
            )
            for job in jobs
        ]
