"""
File:
    deduplicator.py

Version:
    3.0.0

Phase:
    4

Status:
    FROZEN

Purpose:
    Remove duplicate jobs using deterministic rules.

Responsibilities:
    - Remove duplicate jobs preserving original order
    - Keep first occurrence, discard later duplicates
    - Apply multi-level deduplication rules:
        1. job_url match (normalized)
        2. portal + job_id match (normalized)
        3. canonical_company + title + location match (normalized)

Dependencies:
    - jobs.job: Job
    - jobs.identity.resolver: CompanyResolver

This module does NOT:
    - Use fuzzy matching
    - Use AI
    - Use database
    - Use Playwright
    - Use logging
    - Use regex

PEP8:     Yes
SOLID:    Yes (Single Responsibility)
DRY:      Yes
KISS:     Yes
"""

from __future__ import annotations

from jobs.identity.resolver import CompanyResolver
from jobs.job import Job


class JobDeduplicator:
    """
    Deterministic job deduplicator.

    Removes duplicate jobs from a list while preserving original order.
    Uses three levels of deduplication in priority order.

    Methods:
        deduplicate: Remove duplicate jobs from list.
    """

    def __init__(self) -> None:
        """
        Initialize JobDeduplicator with CompanyResolver.
        """
        self._resolver: CompanyResolver = CompanyResolver()

    def deduplicate(self, jobs: list[Job]) -> list[Job]:
        """
        Remove duplicate jobs preserving original order.

        Deduplication rules (applied in priority order):
            1. job_url exact match (normalized)
            2. portal + job_id match (normalized)
            3. canonical_company + title + location match (normalized)

        When a duplicate is found, the first occurrence is kept.
        Later occurrences are discarded.

        Args:
            jobs: List of Job objects.

        Returns:
            list[Job]: Deduplicated list preserving order.

        Examples:
            >>> deduplicator = JobDeduplicator()
            >>> jobs = [
            ...     Job(job_url="url1", title="SWE", company="Google"),
            ...     Job(job_url="url1", title="SWE", company="Google"),
            ... ]
            >>> len(deduplicator.deduplicate(jobs))
            1
        """
        if not jobs:
            return []

        # Track seen keys for each deduplication level
        seen_urls: set[str] = set()
        seen_portal_job_ids: set[tuple[str, str]] = set()
        seen_composite: set[tuple[str, str, str]] = set()

        deduplicated: list[Job] = []

        for job in jobs:
            # Rule 1: job_url match (normalized)
            job_url: str = (job.job_url or "").strip()
            if job_url:
                if job_url in seen_urls:
                    continue
                seen_urls.add(job_url)

            # Rule 2: portal + job_id match (normalized)
            portal: str = (job.portal or "").strip().lower()
            job_id: str = (job.job_id or "").strip()
            if portal and job_id:
                portal_job_id_key: tuple[str, str] = (portal, job_id)
                if portal_job_id_key in seen_portal_job_ids:
                    continue
                seen_portal_job_ids.add(portal_job_id_key)

            # Rule 3: fallback composite identity.
            #
            # IMPORTANT:
            # Only use the composite fallback when neither a URL
            # nor a portal + job_id identity was available.
            #
            # Otherwise two genuinely different jobs from the same
            # company, with the same title and location, could be
            # incorrectly merged.
            has_strong_identity = bool(
                job_url or (portal and job_id)
            )

            if not has_strong_identity:
                canonical_company: str = (
                    self._resolver.resolve(job.company)
                )
                title: str = (job.title or "").strip().lower()
                location: str = (job.location or "").strip().lower()

                composite_key: tuple[str, str, str] = (
                    canonical_company,
                    title,
                    location,
                )

                if canonical_company or title or location:
                    if composite_key in seen_composite:
                        continue
                    seen_composite.add(composite_key)

            # Not a duplicate, keep this job
            deduplicated.append(job)

        return deduplicated


# =============================================================================
# END OF FILE
# =============================================================================