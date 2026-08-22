"""
File:
    validators.py

Version:
    2.0.0

Phase:
    5

Status:
    IMPLEMENTING

Purpose:
    Validate Job objects.

Responsibilities:
    - Validate individual Job objects
    - Validate lists of Job objects
    - Return valid and invalid jobs separately
    - Validate required fields (title, company, job_url, portal)
    - Validate URL format (http:// or https://)

Dependencies:
    - jobs.job: Job

This module does NOT:
    - Modify data
    - Normalize data
    - Export data
    - Use regex
    - Use logging
    - Use Playwright
    - Use AI
    - Use database
    - Use exporter

PEP8:     Yes
SOLID:    Yes (Single Responsibility)
DRY:      Yes
KISS:     Yes
"""

from __future__ import annotations

from jobs.job import Job


class JobValidator:
    """
    Deterministic job validator.

    Validates Job objects against required field rules.
    Does NOT modify or normalize data.

    Methods:
        validate: Validate a single Job object.
        validate_many: Validate multiple Job objects.
    """

    # ------------------------------------------------------------------
    # Constants
    # ------------------------------------------------------------------

    URL_PREFIXES: tuple[str, ...] = (
        "http://",
        "https://",
    )

    # ------------------------------------------------------------------
    # Private Validation Methods
    # ------------------------------------------------------------------

    def _validate_title(self, job: Job) -> bool:
        """
        Validate title field.

        Args:
            job: Job object.

        Returns:
            bool: True if valid, False otherwise.
        """
        title: str = (job.title or "").strip()
        return bool(title)

    def _validate_company(self, job: Job) -> bool:
        """
        Validate company field.

        Args:
            job: Job object.

        Returns:
            bool: True if valid, False otherwise.
        """
        company: str = (job.company or "").strip()
        return bool(company)

    def _validate_job_url(self, job: Job) -> bool:
        """
        Validate job_url field.

        Args:
            job: Job object.

        Returns:
            bool: True if valid, False otherwise.
        """
        job_url: str = (job.job_url or "").strip()

        if not job_url:
            return False

        return job_url.startswith(self.URL_PREFIXES)

    def _validate_portal(self, job: Job) -> bool:
        """
        Validate portal field.

        Args:
            job: Job object.

        Returns:
            bool: True if valid, False otherwise.
        """
        portal: str = (job.portal or "").strip()
        return bool(portal)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(self, job: Job) -> bool:
        """
        Validate a single Job object.

        Checks:
            - title: non-empty
            - company: non-empty
            - job_url: non-empty and starts with http:// or https://
            - portal: non-empty

        Args:
            job: Job object to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        if not job:
            return False

        if not self._validate_title(job):
            return False

        if not self._validate_company(job):
            return False

        if not self._validate_job_url(job):
            return False

        if not self._validate_portal(job):
            return False

        return True

    def validate_many(self, jobs: list[Job]) -> tuple[list[Job], list[Job]]:
        """
        Validate multiple Job objects.

        Args:
            jobs: List of Job objects to validate.

        Returns:
            tuple[list[Job], list[Job]]: (valid_jobs, invalid_jobs)
        """
        valid_jobs: list[Job] = []
        invalid_jobs: list[Job] = []

        for job in jobs:
            if self.validate(job):
                valid_jobs.append(job)
            else:
                invalid_jobs.append(job)

        return valid_jobs, invalid_jobs


# =============================================================================
# END OF FILE
# =============================================================================