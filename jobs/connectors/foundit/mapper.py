"""
Foundit -> shared Job mapper.

This module contains only Foundit-specific field normalization.
No CRM/profile/business logic belongs here.
"""

from __future__ import annotations

from datetime import datetime, timezone
from html import unescape
import re
from typing import Any

from jobs.identity.normalizer import Normalizer
from jobs.identity.resolver import CompanyResolver
from jobs.job import Job


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None

    if isinstance(value, (list, tuple)):
        value = ", ".join(
            str(item).strip()
            for item in value
            if str(item).strip()
        )

    text = unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text or None


def _extract_years(value: Any) -> str | None:
    if value is None:
        return None

    if isinstance(value, dict):
        years = value.get("years")

        if years is not None:
            return str(years)

    if isinstance(value, (int, float)):
        return str(value)

    return None


def _parse_experience_values(
    item: dict[str, Any],
) -> tuple[int | None, int | None]:
    minimum = _extract_years(item.get("minimumExperience"))
    maximum = _extract_years(item.get("maximumExperience"))

    def to_int(value: str | None) -> int | None:
        if value is None:
            return None

        match = re.search(r"(\d+)", value)

        if not match:
            return None

        return int(match.group(1))

    minimum_value = to_int(minimum)
    maximum_value = to_int(maximum)

    if minimum_value is None and maximum_value is None:
        experience_text = _clean_text(item.get("exp"))

        if experience_text:
            numbers = re.findall(r"(\d+)", experience_text)

            if numbers:
                minimum_value = int(numbers[0])

            if len(numbers) > 1:
                maximum_value = int(numbers[1])

    return minimum_value, maximum_value


def _parse_salary_values(
    item: dict[str, Any],
) -> tuple[float | None, float | None, str | None]:
    minimum = item.get("minimumSalary") or {}
    maximum = item.get("maximumSalary") or {}

    if not isinstance(minimum, dict):
        minimum = {}

    if not isinstance(maximum, dict):
        maximum = {}

    min_value = minimum.get("absoluteValue")
    max_value = maximum.get("absoluteValue")

    currency = (
        item.get("currencyCode")
        or minimum.get("currency")
        or maximum.get("currency")
        or "INR"
    )

    try:
        min_value = (
            float(min_value)
            if min_value not in (None, "")
            else None
        )
    except (TypeError, ValueError):
        min_value = None

    try:
        max_value = (
            float(max_value)
            if max_value not in (None, "")
            else None
        )
    except (TypeError, ValueError):
        max_value = None

    # Foundit uses 0-0 when salary is undisclosed.
    if min_value == 0 and max_value == 0:
        return None, None, None

    if min_value == 0:
        min_value = None

    if max_value == 0:
        max_value = None

    if min_value is None and max_value is None:
        return None, None, None

    return min_value, max_value, str(currency)


def _format_skills(item: dict[str, Any]) -> list[str]:
    skills = item.get("skills")

    if isinstance(skills, str):
        return [skills] if skills.strip() else []

    if not isinstance(skills, list):
        return []

    values: list[str] = []

    for skill in skills:
        if isinstance(skill, dict):
            # Search payloads may use "value"; detail payloads use "text".
            value = (
                skill.get("text")
                or skill.get("value")
                or skill.get("name")
            )
        else:
            value = skill

        cleaned = _clean_text(value)

        if cleaned:
            values.append(cleaned)

    return values


def _format_posted_date(item: dict[str, Any]) -> datetime | None:
    """
    Foundit's listing payload exposes epoch milliseconds in
    freshness/createdAt.

    Prefer freshness because it represents the job's posting freshness.
    """

    timestamp = item.get("freshness") or item.get("createdAt")

    if timestamp is None:
        return None

    try:
        timestamp = float(timestamp)

        if timestamp > 10_000_000_000:
            timestamp /= 1000

        return datetime.fromtimestamp(
            timestamp,
            tz=timezone.utc,
        )

    except (TypeError, ValueError, OverflowError, OSError):
        return None


def _extract_location(item: dict[str, Any]) -> str | None:
    locations = item.get("locations")

    if isinstance(locations, str):
        return _clean_text(locations)

    if isinstance(locations, dict):
        city = locations.get("city") or locations.get("CITY")
        if city:
            return _clean_text(city)

        state = locations.get("state") or locations.get("STATE")
        if state:
            return _clean_text(state)

        country = locations.get("country") or locations.get("COUNTRY")
        return _clean_text(country)

    if isinstance(locations, list):
        cities: list[str] = []
        states: list[str] = []
        countries: list[str] = []

        for location in locations:
            if not isinstance(location, dict):
                continue

            city = location.get("city") or location.get("CITY")
            state = location.get("state") or location.get("STATE")
            country = location.get("country") or location.get("COUNTRY")

            if city:
                value = _clean_text(city)
                if value and value not in cities:
                    cities.append(value)
            elif state:
                value = _clean_text(state)
                if value and value not in states:
                    states.append(value)
            elif country:
                value = _clean_text(country)
                if value and value not in countries:
                    countries.append(value)

        if cities:
            return ", ".join(cities)

        if states:
            return ", ".join(states)

        if countries:
            return ", ".join(countries)

    return None


def _extract_job_url(item: dict[str, Any]) -> str | None:
    for key in (
        "seoJdUrl",
        "jdUrl",
    ):
        value = _clean_text(item.get(key))

        if value:
            if value.startswith(("http://", "https://")):
                return value

            return f"https://www.foundit.in{value}"

    return None


def _extract_apply_url(item: dict[str, Any]) -> str | None:
    for key in (
        "applyUrl",
        "redirectUrl",
    ):
        value = _clean_text(item.get(key))

        if value and value.startswith(("http://", "https://")):
            return value

    return None


def _extract_description(item: dict[str, Any]) -> str | None:
    for key in (
        "description",
        "jobDescription",
        "jobDescriptionText",
        "jd",
    ):
        value = _clean_text(item.get(key))

        if value:
            return value

    return None


def map_job(
    item: dict[str, Any],
    *,
    description: str | None = None,
    discovery_keyword: str = "",
) -> Job:
    """
    Convert one Foundit listing/detail record into the project's
    canonical jobs.job.Job contract.
    """

    job_id = item.get("jobId") or item.get("id")

    if job_id is None:
        raise ValueError("Foundit job has no job ID")

    job_url = _extract_job_url(item)

    if not job_url:
        raise ValueError(
            f"Foundit job {job_id!r} has no usable job URL"
        )

    normalizer = Normalizer()
    resolver = CompanyResolver()

    raw_company = (
        _clean_text(item.get("companyName"))
        or _clean_text(item.get("recruiterName"))
    )

    company = (
        resolver.resolve(raw_company)
        if raw_company
        else ""
    )

    raw_location = _extract_location(item)

    location = (
        normalizer.normalize_location(raw_location)
        if raw_location
        else ""
    )

    employment_type = (
        _clean_text(item.get("employmentTypes"))
        or _clean_text(item.get("jobTypes"))
    )

    min_salary, max_salary, salary_currency = _parse_salary_values(item)

    min_experience, max_experience = _parse_experience_values(item)

    final_description = (
        _clean_text(description)
        or _extract_description(item)
        or ""
    )

    posted_datetime = _format_posted_date(item)

    return Job(
        job_id=str(job_id),
        title=_clean_text(item.get("title")) or "Unknown Position",
        company=company or raw_company or "Unknown Company",
        location=location or raw_location or "Unknown Location",
        description=final_description,
        job_url=job_url,
        portal="foundit",
        discovery_keyword=discovery_keyword,
        posted_date=posted_datetime.date() if posted_datetime else None,
        salary_min=min_salary,
        salary_max=max_salary,
        salary_currency=salary_currency,
        experience_min=min_experience,
        experience_max=max_experience,
        employment_type=(
            normalizer.normalize_employment_type(employment_type)
            if employment_type
            else ""
        ),
        skills=normalizer.normalize_skills(
            _format_skills(item)
        ),
        raw=item,
    )


def map_jobs(
    items: list[dict[str, Any]],
    *,
    discovery_keyword: str = "",
) -> list[Job]:
    """Map multiple Foundit records into canonical Job objects."""

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

        if job.job_id:
            jobs.append(job)

    return jobs
