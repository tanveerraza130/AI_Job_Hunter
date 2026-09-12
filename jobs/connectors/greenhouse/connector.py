"""
Greenhouse Jobs connector.

Flow:

SearchRequest
    ↓
Configured public Greenhouse boards
    ↓
Board-wide published jobs
    ↓
Source-local keyword/location candidate filtering
    ↓
Mapper
    ↓
Canonical Job objects

This connector does not perform profile filtering, scoring,
intelligence, persistence, or application logic.
"""

from __future__ import annotations

import os
from typing import Any

from jobs.base import BaseConnector
from jobs.enums import ConnectorType, Portal
from jobs.job import Job
from jobs.search import SearchRequest

from .api import GreenhouseAPI
from .mapper import map_job


class GreenhouseConnector(BaseConnector):
    """Fetch published jobs from configured Greenhouse boards."""

    PORTAL = Portal.GREENHOUSE
    CONNECTOR_TYPE = ConnectorType.API
    VERSION = "0.1.0"

    def __init__(
        self,
        context: Any = None,
        *,
        board_tokens: list[str] | None = None,
    ) -> None:
        self.context = context

        if board_tokens is None:
            configured = os.getenv(
                "GREENHOUSE_BOARD_TOKENS",
                "",
            )

            board_tokens = [
                token.strip()
                for token in configured.split(",")
                if token.strip()
            ]

        self.board_tokens = list(
            dict.fromkeys(board_tokens or [])
        )

        self._apis = {
            token: GreenhouseAPI(token)
            for token in self.board_tokens
        }

    @property
    def name(self) -> str:
        return "Greenhouse"

    @staticmethod
    def _matches(
        item: dict[str, Any],
        request: SearchRequest,
    ) -> bool:
        """
        Apply source-local keyword/location candidate matching.

        Keyword is checked against title and full public JD.
        Location is checked against the Greenhouse location field.

        Empty criteria do not exclude a job.
        """
        title = str(
            item.get("title") or ""
        )

        content = str(
            item.get("content") or ""
        )

        keyword = (
            request.keyword or ""
        ).strip().lower()

        location_data = item.get("location")

        if isinstance(location_data, dict):
            location = str(
                location_data.get("name") or ""
            )
        else:
            location = str(
                location_data or ""
            )

        location = location.lower()

        keyword_match = (
            not keyword
            or keyword in (
                title + "\n" + content
            ).lower()
        )

        requested_location = (
            request.location or ""
        ).strip().lower()

        location_match = (
            not requested_location
            or requested_location in location
        )

        return keyword_match and location_match

    @staticmethod
    def _safe_max_jobs(
        request: SearchRequest,
    ) -> int | None:
        if request.max_jobs is None:
            return None

        try:
            value = int(request.max_jobs)
        except (TypeError, ValueError):
            return 0

        return max(value, 0)

    def fetch_jobs(
        self,
        request: SearchRequest,
    ) -> list[Job]:
        """
        Fetch and normalize relevant jobs from configured boards.
        """
        max_jobs = self._safe_max_jobs(request)

        if max_jobs == 0:
            return []

        if not self.board_tokens:
            return []

        jobs: list[Job] = []
        seen_ids: set[str] = set()

        for board_token in self.board_tokens:
            api = self._apis[board_token]

            items = api.fetch_jobs(
                content=True,
            )

            for item in items:
                if not self._matches(
                    item,
                    request,
                ):
                    continue

                job_id = str(
                    item.get("id") or ""
                ).strip()

                if not job_id:
                    continue

                canonical_key = (
                    f"{board_token}:{job_id}"
                )

                if canonical_key in seen_ids:
                    continue

                seen_ids.add(canonical_key)

                try:
                    job = map_job(
                        item,
                        discovery_keyword=request.keyword,
                        board_token=board_token,
                    )
                except ValueError:
                    continue

                jobs.append(job)

                if (
                    max_jobs is not None
                    and len(jobs) >= max_jobs
                ):
                    return jobs

        return jobs
