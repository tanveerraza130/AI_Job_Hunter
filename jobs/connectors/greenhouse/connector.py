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
from pathlib import Path
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

            catalog_path = os.getenv(
                "GREENHOUSE_BOARD_CATALOG",
                "config/greenhouse_boards.txt",
            )

            catalog = Path(catalog_path)

            if catalog.exists():
                catalog_tokens = [
                    line.strip()
                    for line in catalog.read_text().splitlines()
                    if line.strip()
                    and not line.lstrip().startswith("#")
                ]

                board_tokens.extend(catalog_tokens)

        self.board_tokens = list(
            dict.fromkeys(board_tokens or [])
        )

        self._apis = {
            token: GreenhouseAPI(token)
            for token in self.board_tokens
        }

        # Cache each public board inventory once per connector run.
        # Multiple profiles/search requests can reuse the same board data.
        self._job_cache: dict[str, list[dict[str, Any]]] = {}

    @property
    def name(self) -> str:
        return "Greenhouse"

    @staticmethod
    def _matches(
        item: dict[str, Any],
        request: SearchRequest,
    ) -> bool:
        """
        Apply only safe source-level candidate constraints.

        Greenhouse does not perform profile/keyword relevance
        matching. Search keywords belong to the shared profile
        filtering layer so that semantically relevant jobs whose
        titles differ from the literal search keyword are not lost.

        Location may still be used as a source-level constraint
        because it is an explicit SearchRequest boundary.
        """
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

        requested_location = (
            request.location or ""
        ).strip().lower()

        return (
            not requested_location
            or requested_location in location
        )

    def fetch_jobs(
        self,
        request: SearchRequest,
    ) -> list[Job]:
        """
        Fetch and normalize relevant jobs from configured boards.
        """
        if not self.board_tokens:
            return []

        jobs: list[Job] = []
        seen_ids: set[str] = set()

        for board_token in self.board_tokens:
            api = self._apis[board_token]

            if board_token not in self._job_cache:
                self._job_cache[board_token] = api.fetch_jobs(
                    content=True,
                )

            items = self._job_cache[board_token]

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

        return jobs
