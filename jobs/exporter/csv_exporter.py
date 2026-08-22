"""
File:
    csv_exporter.py

Version:
    2.0.0

Phase:
    6

Status:
    FROZEN

Purpose:
    Export jobs to CSV format.

Responsibilities:
    - Inherit from BaseExporter
    - Export list[Job] to CSV
    - Create parent directories automatically
    - Write UTF-8 encoded CSV with headers
    - One Job per row

Dependencies:
    - csv: DictWriter
    - dataclasses: fields, asdict
    - pathlib: Path
    - jobs.exporter.base: BaseExporter
    - jobs.job: Job

This module does NOT:
    - Normalize data
    - Validate jobs
    - Deduplicate
    - Log anything
    - Use DuckDB
    - Use Excel
    - Use JSON
    - Use Playwright
    - Use pandas

PEP8:     Yes
SOLID:    Yes (Single Responsibility)
DRY:      Yes
KISS:     Yes
"""

from __future__ import annotations

import csv
from dataclasses import asdict, fields
from pathlib import Path

from jobs.enums import ExportFormat
from jobs.exporter.base import BaseExporter
from jobs.job import Job


class CSVExporter(BaseExporter):
    """
    CSV exporter implementation.

    Exports Job objects to CSV format with headers.

    Methods:
        export: Export jobs to CSV file.
    """

    EXPORT_FORMAT = ExportFormat.CSV

    def export(
        self,
        jobs: list[Job],
        destination: Path,
    ) -> None:
        """
        Export jobs to CSV file.

        Creates parent directories if they don't exist.
        Writes UTF-8 encoded CSV with headers.
        One Job per row.

        Args:
            jobs: List of Job objects to export.
            destination: Path to output CSV file.

        Raises:
            RuntimeError: If export fails.
        """
        try:
            # Get field names from Job dataclass using public API
            fieldnames: list[str] = [field.name for field in fields(Job)]

            # Ensure parent directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)

            # Write CSV with headers
            with destination.open(
                "w",
                newline="",
                encoding="utf-8",
            ) as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()

                # Write rows sequentially to support large exports
                for job in jobs:
                    writer.writerow(asdict(job))

        except (OSError, csv.Error) as e:
            raise RuntimeError(f"Failed to export CSV to {destination}: {e}") from e


# =============================================================================
# END OF FILE
# =============================================================================