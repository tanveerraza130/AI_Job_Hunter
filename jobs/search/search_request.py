"""
Common search request shared by every connector.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(slots=True, frozen=True)
class SearchRequest:
    """
    Immutable search request.

    Every connector receives the same object.
    """

    keyword: str
    location: str | None = None

    page: int = 1
    per_page: int = 20

    experience: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None

    work_mode: str | None = None
    employment_type: str | None = None

    company: str | None = None

    easy_apply_only: bool = False

    posted_within_days: int | None = None

    skills: list[str] = field(default_factory=list)

    # CLI support fields
    page_size: int = 20
    max_jobs: Optional[int] = None