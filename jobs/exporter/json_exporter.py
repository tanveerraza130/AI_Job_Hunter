"""
File:
    json_exporter.py

Version:
    1.0.0

Phase:
    6

Status:
    FROZEN

Purpose:
    Export jobs to JSON format.

Responsibilities:
    - Inherit from BaseExporter
    - Export list[Job] to JSON
    - Create parent directories automatically
    - Write UTF-8 encoded JSON
    - One Job object per JSON object
    - Preserve dataclass field names

Dependencies:
    - json
    - pathlib: Path
    - jobs.exporter.base: BaseExporter
    - jobs.job: Job

This module does NOT:
    - Normalize data
    - Validate jobs
    - Deduplicate
    - Log anything
    - Use DuckDB
    - Use CSV
    - Use Excel
    - Use Playwright
    - Use pandas

PEP8:     Yes
SOLID:    Yes (Single Responsibility)
DRY:      Yes
KISS:     Yes
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from jobs.enums import ExportFormat
from jobs.exporter.base import BaseExporter
from jobs.job import Job


class JSONExporter(BaseExporter):
    """
    JSON exporter implementation.

    Exports Job objects to JSON format as an array.

    Methods:
        export: Export jobs to JSON file.
    """

    EXPORT_FORMAT = ExportFormat.JSON

    def _job_to_dict(self, job: Job) -> dict:
        """
        Convert a Job object to a dictionary.

        Uses explicit attribute mapping to avoid accidental inclusion
        of internal or dynamic attributes.

        Args:
            job: Job object.

        Returns:
            dict: Dictionary representation of the job.
        """
        return {
            "job_id": job.job_id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "salary_currency": job.salary_currency,
            "description": job.description,
            "job_url": job.job_url,
            "portal": job.portal,
            "posted_date": job.posted_date,
            "experience_min": job.experience_min,
            "experience_max": job.experience_max,
            "employment_type": job.employment_type,
            "skills": job.skills,
        }

    def export(
        self,
        jobs: list[Job],
        destination: Path,
    ) -> None:
        """
        Export jobs to JSON file.

        Creates parent directories if they don't exist.
        Writes UTF-8 encoded JSON as an array.
        One Job object per array element.

        Args:
            jobs: List of Job objects to export.
            destination: Path to output JSON file.

        Raises:
            RuntimeError: If export fails.
        """
        try:
            # Ensure parent directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)

            # Convert jobs to list of dictionaries using explicit mapping
            data = [self._job_to_dict(job) for job in jobs]

            # Write JSON array
            with destination.open("w", encoding="utf-8") as file:
                json.dump(
                    data,
                    file,
                    indent=2,
                    ensure_ascii=False,
                )

        except (OSError, TypeError, ValueError) as e:
            raise RuntimeError(f"Failed to export JSON to {destination}: {e}") from e


# =============================================================================
# END OF FILE
# =============================================================================