"""
Greenhouse -> normalized Job mapper.
"""

from __future__ import annotations

import re
from datetime import datetime
from html import unescape
from typing import Any

from jobs.job import Job


def _text(value: Any) -> str:
    """Convert a value to clean text."""
    if value is None:
        return ""

    return str(value).strip()


def _clean_html(value: Any) -> str:
    """Convert Greenhouse HTML job content to readable text."""
    text = _text(value)

    if not text:
        return ""

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
        " ",
        text,
    )

    text = unescape(text)

    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in text.splitlines()
    ]

    return "\n".join(
        line
        for line in lines
        if line
    )


def _location(item: dict[str, Any]) -> str:
    """Extract the Greenhouse job location."""
    value = item.get("location")

    if isinstance(value, dict):
        return _text(value.get("name"))

    return _text(value)


def _posted_date(item: dict[str, Any]):
    """Extract the Greenhouse first-published date."""
    value = (
        item.get("first_published")
        or item.get("updated_at")
    )

    text = _text(value)

    if not text:
        return None

    try:
        return datetime.fromisoformat(
            text.replace("Z", "+00:00")
        ).date()
    except ValueError:
        try:
            return datetime.strptime(
                text[:10],
                "%Y-%m-%d",
            ).date()
        except ValueError:
            return None


def _departments(item: dict[str, Any]) -> list[str]:
    """Extract Greenhouse department names."""
    departments = item.get("departments")

    if not isinstance(departments, list):
        return []

    result: list[str] = []

    for department in departments:
        if not isinstance(department, dict):
            continue

        name = _text(department.get("name"))

        if name and name not in result:
            result.append(name)

    return result


def _offices(item: dict[str, Any]) -> list[str]:
    """Extract Greenhouse office names."""
    offices = item.get("offices")

    if not isinstance(offices, list):
        return []

    result: list[str] = []

    for office in offices:
        if not isinstance(office, dict):
            continue

        name = _text(office.get("name"))

        if name and name not in result:
            result.append(name)

    return result


def map_job(
    item: dict[str, Any],
    *,
    discovery_keyword: str = "",
    board_token: str = "",
) -> Job:
    """Map one Greenhouse job payload to the canonical Job model."""

    source_job_id = _text(item.get("id"))

    if not source_job_id:
        raise ValueError(
            "Greenhouse job has no ID"
        )

    board_token = _text(board_token)

    job_id = (
        f"{board_token}:{source_job_id}"
        if board_token
        else source_job_id
    )

    title = _text(item.get("title"))

    company = _text(
        item.get("company_name")
    )

    location = _location(item)

    description = _clean_html(
        item.get("content")
    )

    job_url = _text(
        item.get("absolute_url")
    )

    # Greenhouse department/office metadata is retained in raw.
    # It is not canonical job-skill data.
    skills: list[str] = []

    return Job(
        job_id=job_id,
        title=title or "Unknown Position",
        company=company or "Unknown Company",
        location=location or "Unknown Location",
        description=description,
        job_url=job_url,
        portal="greenhouse",
        discovery_keyword=discovery_keyword,
        posted_date=_posted_date(item),
        skills=skills,
        raw=item,
    )


def map_jobs(
    items: list[dict[str, Any]],
    *,
    discovery_keyword: str = "",
) -> list[Job]:
    """Map Greenhouse jobs to canonical Job objects."""
    jobs: list[Job] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        try:
            job = map_job(
                item,
                discovery_keyword=discovery_keyword,
            )
        except ValueError:
            continue

        jobs.append(job)

    return jobs
