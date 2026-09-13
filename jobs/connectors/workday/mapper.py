from __future__ import annotations

import re
from datetime import datetime
from html import unescape
from typing import Any

from jobs.job import Job


def _text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _clean_html(value: Any) -> str:
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
        r"</li\s*>",
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
        line for line in lines if line
    )


def _posted_date(info: dict[str, Any]):
    """
    Parse an actual ISO posting date when Workday provides one.

    Workday's human-readable `postedOn` value such as
    'Posted 30+ Days Ago' is intentionally not parsed as a date.
    """
    for key in ("posted", "postedDate", "postingDate"):
        value = info.get(key)

        if not isinstance(value, str):
            continue

        value = value.strip()

        if not value:
            continue

        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            ).date()
        except ValueError:
            try:
                return datetime.strptime(
                    value[:10],
                    "%Y-%m-%d",
                ).date()
            except ValueError:
                continue

    return None


def map_job(
    search_item: dict[str, Any],
    detail_payload: dict[str, Any],
    *,
    company: str,
    host: str,
    tenant: str,
    site: str,
    discovery_keyword: str = "",
) -> Job:
    """
    Map one Workday search/detail pair to the canonical Job model.
    """
    info = detail_payload.get("jobPostingInfo", {})

    if not isinstance(info, dict):
        raise ValueError(
            "Workday job detail has no valid jobPostingInfo"
        )

    requisition_id = _text(
        info.get("jobReqId")
        or search_item.get("bulletFields", [""])[0]
        if isinstance(search_item.get("bulletFields"), list)
        else info.get("jobReqId")
    )

    internal_id = _text(
        info.get("id")
    )

    source_id = requisition_id or internal_id

    if not source_id:
        raise ValueError(
            "Workday job has no requisition or internal ID"
        )

    job_id = f"{tenant}:{source_id}"

    title = _text(
        info.get("title")
        or search_item.get("title")
    )

    location = _text(
        info.get("location")
        or search_item.get("locationsText")
    )

    description = _clean_html(
        info.get("jobDescription")
    )

    external_url = _text(
        info.get("externalUrl")
    )

    if not external_url:
        external_path = _text(
            search_item.get("externalPath")
        )

        if external_path:
            external_url = (
                f"https://{host}"
                f"/{site.strip('/')}"
                f"{external_path}"
            )

    raw = {
        "search": search_item,
        "detail": detail_payload,
        "workday": {
            "host": host,
            "tenant": tenant,
            "site": site,
            "time_type": info.get("timeType"),
            "remote_type": info.get("remoteType"),
            "start_date": info.get("startDate"),
            "job_req_id": info.get("jobReqId"),
            "job_posting_id": info.get("jobPostingId"),
        },
    }

    return Job(
        job_id=job_id,
        title=title or "Unknown Position",
        company=company or "Unknown Company",
        location=location or "Unknown Location",
        description=description,
        job_url=external_url,
        portal="workday",
        discovery_keyword=discovery_keyword,
        posted_date=_posted_date(info),
        employment_type=_text(
            info.get("timeType")
        ) or None,
        skills=[],
        raw=raw,
    )


def map_jobs(
    items: list[tuple[dict[str, Any], dict[str, Any]]],
    *,
    company: str,
    host: str,
    tenant: str,
    site: str,
    discovery_keyword: str = "",
) -> list[Job]:
    jobs: list[Job] = []

    for search_item, detail_payload in items:
        try:
            job = map_job(
                search_item,
                detail_payload,
                company=company,
                host=host,
                tenant=tenant,
                site=site,
                discovery_keyword=discovery_keyword,
            )
        except ValueError:
            continue

        jobs.append(job)

    return jobs
