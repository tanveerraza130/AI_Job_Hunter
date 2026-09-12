"""
Instahyre -> normalized Job mapper.
"""

from __future__ import annotations

from typing import Any

from jobs.job import Job


def _clean(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _locations(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(
            _clean(item)
            for item in value
            if _clean(item)
        )

    return _clean(value)


def _skills(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    result: list[str] = []

    for item in value:
        skill = _clean(item)

        if skill and skill not in result:
            result.append(skill)

    return result


def map_job(
    item: dict[str, Any],
    discovery_keyword: str = "",
    detail: dict[str, Any] | None = None,
) -> Job:
    """
    Map an Instahyre listing into the normalized Job model.

    `detail` is optional structured data extracted from the
    public job page. When available, its full JobPosting
    description takes precedence over the listing metadata.
    """

    job_id = _clean(
        item.get("id")
        or item.get("job_id")
    )

    if not job_id:
        resource_uri = _clean(
            item.get("resource_uri")
            or item.get("resourceUri")
        )

        if resource_uri:
            job_id = resource_uri.rstrip("/").split("/")[-1]

    if not job_id:
        raise ValueError("Instahyre job has no ID")

    employer = item.get("employer")

    if not isinstance(employer, dict):
        employer = {}

    company = _clean(
        item.get("company_name")
        or item.get("companyName")
        or employer.get("company_name")
        or employer.get("companyName")
    )

    title = _clean(
        item.get("title")
        or item.get("candidate_title")
        or item.get("candidateTitle")
    )

    location = _locations(
        item.get("locations")
        or item.get("locationsRaw")
    )

    job_url = _clean(
        item.get("public_url")
        or item.get("publicUrl")
        or item.get("url")
    )

    skills = _skills(
        item.get("keywords")
        or item.get("skills")
    )

    employer_note = _clean(
        employer.get("instahyre_note")
        or employer.get("company_about")
        or employer.get("companyAbout")
    )

    description = ""

    if isinstance(detail, dict):
        description = _clean(
            detail.get("description")
        )

    # Listing-level fallback when public-page enrichment
    # is unavailable.
    if not description:
        description_parts: list[str] = []

        if employer_note:
            description_parts.append(
                employer_note
            )

        if skills:
            description_parts.append(
                "Skills: " + ", ".join(skills)
            )

        description = "\n\n".join(
            description_parts
        )

    raw = dict(item)

    if detail:
        raw["_instahyre_detail"] = detail

    return Job(
        job_id=job_id,
        title=title,
        company=company or "Unknown",
        location=location,
        description=description,
        job_url=job_url,
        portal="instahyre",
        discovery_keyword=discovery_keyword,
        skills=skills,
        raw=raw,
    )
