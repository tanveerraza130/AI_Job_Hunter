"""
Standard search result returned by every connector.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from jobs.job import Job


@dataclass(slots=True)
class SearchResult:
    """
    Standard connector result.
    """

    connector: str

    jobs: list[Job] = field(default_factory=list)

    total_results: int = 0

    page: int = 1

    per_page: int = 20

    has_next_page: bool = False

    raw_response: dict | None = None