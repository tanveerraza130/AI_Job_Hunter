"""
Job dataclass.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class Job:
    """
    Normalized job object.

    Attributes:
        job_id: Unique identifier from the portal.
        title: Job title.
        company: Company name.
        location: Job location.
        description: Full job description.
        job_url: URL to the job listing.
        portal: Source portal name (e.g., "naukri").
        posted_date: Date the job was posted.
        salary_min: Minimum salary (annual, in local currency).
        salary_max: Maximum salary (annual, in local currency).
        salary_currency: Currency code (e.g., "₹", "$").
        experience_min: Minimum years of experience required.
        experience_max: Maximum years of experience required.
        employment_type: Employment type (e.g., "FULL_TIME", "CONTRACT").
        skills: List of required skills.
        raw: Raw data from the portal.
        score: Relevance score (0-100) for ranking.
    """
    job_id: str
    title: str
    company: str
    location: str
    description: str
    job_url: str
    portal: str
    discovery_keyword: str = ""
    posted_date: date | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    experience_min: int | None = None
    experience_max: int | None = None
    employment_type: str | None = None
    skills: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)
    score: int = 0


# =============================================================================
# END OF FILE
# =============================================================================