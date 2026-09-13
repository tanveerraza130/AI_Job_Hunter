from __future__ import annotations

from typing import Any

import requests


class WorkdayAPIError(RuntimeError):
    """Raised when the Workday public CXS API cannot be accessed."""


class WorkdayAPI:
    """Client for one public Workday career site."""

    BASE_URL = "https://{host}/wday/cxs/{tenant}/{site}"

    def __init__(
        self,
        host: str,
        tenant: str,
        site: str,
        *,
        session: requests.Session | None = None,
        timeout: int = 20,
    ) -> None:
        self.host = host.strip().rstrip("/")
        self.tenant = tenant.strip()
        self.site = site.strip().strip("/")

        if not self.host:
            raise ValueError("host cannot be empty")
        if not self.tenant:
            raise ValueError("tenant cannot be empty")
        if not self.site:
            raise ValueError("site cannot be empty")

        self.session = session or requests.Session()
        self.timeout = timeout

    @property
    def base_url(self) -> str:
        return self.BASE_URL.format(
            host=self.host,
            tenant=self.tenant,
            site=self.site,
        )

    @property
    def jobs_url(self) -> str:
        return f"{self.base_url}/jobs"

    def search_jobs(
        self,
        *,
        search_text: str = "",
        offset: int = 0,
        limit: int = 20,
        applied_facets: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if limit <= 0:
            raise ValueError("limit must be greater than zero")
        if offset < 0:
            raise ValueError("offset cannot be negative")

        payload = {
            "appliedFacets": applied_facets or {},
            "limit": limit,
            "offset": offset,
            "searchText": search_text,
        }

        try:
            response = self.session.post(
                self.jobs_url,
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise WorkdayAPIError(
                f"Unable to access Workday career site '{self.host}'."
            ) from exc

        if response.status_code != 200:
            raise WorkdayAPIError(
                f"Workday returned HTTP {response.status_code} "
                f"for {self.host}/{self.tenant}/{self.site}."
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise WorkdayAPIError(
                f"Workday returned invalid JSON for "
                f"{self.host}/{self.tenant}/{self.site}."
            ) from exc

        if not isinstance(payload, dict):
            raise WorkdayAPIError(
                "Workday response was not a JSON object."
            )

        return payload

    def fetch_jobs(
        self,
        *,
        search_text: str = "",
        page_size: int = 20,
        max_jobs: int | None = None,
    ) -> list[dict[str, Any]]:
        if page_size <= 0:
            raise ValueError("page_size must be greater than zero")

        if max_jobs is not None and max_jobs <= 0:
            return []

        jobs: list[dict[str, Any]] = []
        offset = 0

        while True:
            remaining = (
                max_jobs - len(jobs)
                if max_jobs is not None
                else page_size
            )
            limit = min(page_size, remaining)

            payload = self.search_jobs(
                search_text=search_text,
                offset=offset,
                limit=limit,
            )

            page = payload.get("jobPostings", [])

            if not isinstance(page, list):
                raise WorkdayAPIError(
                    "Workday response contained an invalid "
                    "'jobPostings' collection."
                )

            page_items = [
                item for item in page
                if isinstance(item, dict)
            ]

            jobs.extend(page_items)

            total = payload.get("total")
            if not isinstance(total, int):
                total = None

            if not page_items:
                break

            if max_jobs is not None and len(jobs) >= max_jobs:
                break

            if total is not None and len(jobs) >= total:
                break

            offset += len(page_items)

            if len(page_items) < limit:
                break

        if max_jobs is not None:
            return jobs[:max_jobs]

        return jobs

    def fetch_job_detail(
        self,
        external_path: str,
    ) -> dict[str, Any]:
        external_path = str(external_path or "").strip()

        if not external_path:
            raise ValueError("external_path cannot be empty")

        if not external_path.startswith("/"):
            external_path = f"/{external_path}"

        url = f"{self.base_url}{external_path}"

        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise WorkdayAPIError(
                f"Unable to fetch Workday job detail "
                f"'{external_path}'."
            ) from exc

        if response.status_code != 200:
            raise WorkdayAPIError(
                f"Workday returned HTTP {response.status_code} "
                f"for job '{external_path}'."
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise WorkdayAPIError(
                f"Workday returned invalid JSON for job "
                f"'{external_path}'."
            ) from exc

        if not isinstance(payload, dict):
            raise WorkdayAPIError(
                "Workday job detail was not a JSON object."
            )

        return payload
