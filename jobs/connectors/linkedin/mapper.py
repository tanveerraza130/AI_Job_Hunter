"""
LinkedIn JobPosting → canonical jobs.job.Job mapper.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any
from urllib.parse import urlparse

from jobs.job import Job


def _text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _company_name(value: Any) -> str:
    if isinstance(value, dict):
        return _text(value.get("name"))

    return _text(value)


def _location(value: Any) -> str:
    if isinstance(value, list):
        values = [_location(item) for item in value]
        return ", ".join(v for v in values if v)

    if not isinstance(value, dict):
        return _text(value)

    address = value.get("address")

    if isinstance(address, dict):
        parts = [
            address.get("addressLocality"),
            address.get("addressRegion"),
            address.get("addressCountry"),
        ]

        return ", ".join(
            str(part).strip()
            for part in parts
            if part
        )

    return _text(address)


def _posted_date(value: Any) -> date | None:
    value = _text(value)

    if not value:
        return None

    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _experience_years(value: Any) -> int | None:
    if value is None:
        return None

    try:
        months = int(value)
    except (TypeError, ValueError):
        return None

    if months < 0:
        return None

    return months // 12


def _job_id(url: str) -> str:
    path = urlparse(url).path

    match = re.search(r"-([0-9]{6,})/?$", path)

    if match:
        return match.group(1)

    match = re.search(r"/jobs/view/[^/]*-([0-9]{6,})", path)

    if match:
        return match.group(1)

    return path.rstrip("/").split("/")[-1]


def _description_text(value: Any) -> str:
    text = _text(value)

    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def _skills(payload: dict[str, Any]) -> list[str]:
    value = payload.get("skills")

    if isinstance(value, list):
        return [
            _text(item)
            for item in value
            if _text(item)
        ]

    if isinstance(value, str) and value.strip():
        return [value.strip()]

    return []


def map_job(
    payload: dict[str, Any],
    *,
    job_url: str,
    discovery_keyword: str = "",
) -> Job:
    title = _text(payload.get("title"))
    company = _company_name(
        payload.get("hiringOrganization")
    )
    location = _location(
        payload.get("jobLocation")
    )
    description = _description_text(
        payload.get("description")
    )

    employment_type = _text(
        payload.get("employmentType")
    ) or None

    experience = _experience_years(
        (
            payload.get("experienceRequirements") or {}
        ).get("monthsOfExperience")
        if isinstance(
            payload.get("experienceRequirements"),
            dict,
        )
        else None
    )

    return Job(
        job_id=_job_id(job_url),
        title=title,
        company=company,
        location=location,
        description=description,
        job_url=job_url,
        portal="linkedin",
        discovery_keyword=discovery_keyword,
        posted_date=_posted_date(
            payload.get("datePosted")
        ),
        experience_min=experience,
        employment_type=employment_type,
        skills=_skills(payload),
        raw=payload,
    )
