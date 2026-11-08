"""Canonical job ID construction shared across the pipeline."""

from __future__ import annotations


def canonical_job_id(portal: str, job_id: str) -> str:
    """Return a portal-prefixed job ID without altering source ID segments."""
    portal_value = str(portal).strip()
    source_id = str(job_id).strip()

    if not portal_value or not source_id:
        raise ValueError("portal and job_id are required")

    prefix = f"{portal_value}:"

    if source_id.startswith(prefix):
        return source_id

    return f"{prefix}{source_id}"
