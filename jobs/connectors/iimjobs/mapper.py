"""
IIMJobs mapper.

Converts IIMJobs API payloads into the existing normalized Job model.
"""

from __future__ import annotations

import re
from datetime import datetime
from html import unescape
from typing import Any

from jobs.identity.normalizer import Normalizer
from jobs.identity.resolver import CompanyResolver
from jobs.job import Job


def _clean_html(value: Any) -> str:
    """Convert HTML job-description content into plain text."""
    if not value:
        return ""

    text = str(value)

    text = re.sub(
        r"<br\s*/?>",
        "\n",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"</p\s*>",
        "\n",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"<[^>]+>",
        "",
        text,
    )

    text = unescape(text)

    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in text.splitlines()
    ]

    return "\n".join(
        line for line in lines if line
    )


def _parse_created_time(value: Any):
    """Convert IIMJobs epoch milliseconds to a date."""
    if value is None:
        return None

    try:
        timestamp = float(value)

        if timestamp > 10_000_000_000:
            timestamp /= 1000

        return datetime.fromtimestamp(timestamp).date()
    except (TypeError, ValueError, OSError):
        return None


def _extract_locations(item: dict[str, Any]) -> str:
    """Extract and join IIMJobs location names."""
    locations = item.get("locations")

    if not isinstance(locations, list):
        locations = item.get("location")

    if not isinstance(locations, list):
        return ""

    names: list[str] = []

    for location in locations:
        if not isinstance(location, dict):
            continue

        name = location.get("name")

        if name:
            name = str(name).strip()

            if name and name not in names:
                names.append(name)

    return ", ".join(names)


def _extract_tags(item: dict[str, Any]) -> list[str]:
    """Extract IIMJobs tag names."""
    tags = item.get("tags")

    if not isinstance(tags, list):
        return []

    result: list[str] = []

    for tag in tags:
        if not isinstance(tag, dict):
            continue

        name = tag.get("name")

        if name:
            name = str(name).strip()

            if name and name not in result:
                result.append(name)

    return result


def map_job(
    item: dict[str, Any],
    *,
    discovery_keyword: str = "",
) -> Job:
    """Map one IIMJobs job payload to the normalized Job model."""

    normalizer = Normalizer()
    resolver = CompanyResolver()

    job_id = str(
        item.get("id")
        or item.get("refJobId")
        or ""
    ).strip()

    title = str(
        item.get("jobdesignation")
        or item.get("title")
        or ""
    ).strip()

    company_data = item.get("companyData")

    if not isinstance(company_data, dict):
        company_data = {}

    company = str(
        company_data.get("companyName")
        or ""
    ).strip()

    description = _clean_html(
        item.get("introText")
    )

    location = _extract_locations(item)

    tags = _extract_tags(item)

    normalized_company = (
        resolver.resolve(company)
        if company
        else ""
    )

    normalized_location = (
        normalizer.normalize_location(location)
        if location
        else ""
    )

    experience_min = item.get("min")
    experience_max = item.get("max")

    try:
        experience_min = (
            int(experience_min)
            if experience_min is not None
            else None
        )
    except (TypeError, ValueError):
        experience_min = None

    try:
        experience_max = (
            int(experience_max)
            if experience_max is not None
            else None
        )
    except (TypeError, ValueError):
        experience_max = None

    salary_min = item.get("minSal")
    salary_max = item.get("maxSal")

    try:
        salary_min = (
            float(salary_min)
            if salary_min
            else None
        )
    except (TypeError, ValueError):
        salary_min = None

    try:
        salary_max = (
            float(salary_max)
            if salary_max
            else None
        )
    except (TypeError, ValueError):
        salary_max = None

    job_url = str(
        item.get("jobDetailUrl")
        or ""
    ).strip()

    return Job(
        job_id=job_id,
        title=title or "Unknown Position",
        company=(
            normalized_company
            or company
            or "Unknown Company"
        ),
        location=(
            normalized_location
            or location
            or "Unknown Location"
        ),
        description=description,
        job_url=job_url,
        portal="iimjobs",
        discovery_keyword=discovery_keyword,
        posted_date=_parse_created_time(
            item.get("createdTime")
            or item.get("createdTimeMs")
        ),
        salary_min=salary_min,
        salary_max=salary_max,
        salary_currency="INR"
        if salary_min is not None
        or salary_max is not None
        else None,
        experience_min=experience_min,
        experience_max=experience_max,
        employment_type=normalizer.normalize_employment_type(
            ""
        ),
        skills=normalizer.normalize_skills(tags),
        raw=item,
    )


def map_jobs(
    items: list[dict[str, Any]],
    *,
    discovery_keyword: str = "",
) -> list[Job]:
    """Map multiple IIMJobs records."""
    jobs: list[Job] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        job = map_job(
            item,
            discovery_keyword=discovery_keyword,
        )

        if job.job_id:
            jobs.append(job)

    return jobs
