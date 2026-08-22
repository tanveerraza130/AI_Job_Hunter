"""
File:
    excel_exporter.py

Version:
    3.0.0

Phase:
    6

Status:
    FROZEN

Purpose:
    Export jobs to Excel (.xlsx) format.

Responsibilities:
    - Inherit from BaseExporter
    - Export list[Job] to Excel
    - Create parent directories automatically
    - Write .xlsx file with headers
    - One Job per row
    - Convert complex types (list, dict, set) to strings before writing

Dependencies:
    - openpyxl: Workbook
    - dataclasses: asdict, fields
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
    - Use JSON
    - Use pandas
    - Use Playwright

PEP8:     Yes
SOLID:    Yes (Single Responsibility)
DRY:      Yes
KISS:     Yes
"""

from __future__ import annotations

import json
from dataclasses import asdict, fields
from pathlib import Path
from typing import Any

from openpyxl import Workbook

from jobs.enums import ExportFormat
from jobs.exporter.base import BaseExporter
from jobs.job import Job


class ExcelExporter(BaseExporter):
    """
    Excel exporter implementation.

    Exports Job objects to Excel (.xlsx) format with headers.

    Methods:
        export: Export jobs to Excel file.
    """

    EXPORT_FORMAT = ExportFormat.EXCEL

    def _convert_value(self, value: Any) -> Any:
        """
        Convert complex values to Excel-compatible types.

        Args:
            value: Value to convert.

        Returns:
            Any: Excel-compatible value.
        """
        if value is None:
            return ""

        if isinstance(value, list):
            return ", ".join(str(v) for v in value)

        if isinstance(value, dict):
            return json.dumps(value, separators=(",", ":"), ensure_ascii=False)

        if isinstance(value, set):
            return ", ".join(sorted(str(v) for v in value))

        return value

    def _row_to_excel_compatible(self, row: dict[str, Any]) -> list[Any]:
        """
        Convert a dataclass row dictionary to Excel-compatible values.

        Args:
            row: Dictionary from dataclass.asdict().

        Returns:
            list[Any]: List of Excel-compatible values.
        """
        return [self._convert_value(v) for v in row.values()]

    def export(
        self,
        jobs: list[Job],
        destination: Path,
    ) -> None:
        """
        Export jobs to Excel file.

        Creates parent directories if they don't exist.
        Writes .xlsx file with headers.
        One Job per row.

        Args:
            jobs: List of Job objects to export.
            destination: Path to output Excel file.

        Raises:
            RuntimeError: If export fails.
        """
        try:
            # Ensure parent directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)

            # Get field names from Job dataclass using public API
            fieldnames: list[str] = [field.name for field in fields(Job)]

            # Create workbook
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Jobs"

            # Write header row
            sheet.append(fieldnames)

            # Write data rows sequentially with value conversion
            for job in jobs:
                row_dict = asdict(job)
                excel_row = self._row_to_excel_compatible(row_dict)
                sheet.append(excel_row)

            # Save workbook
            workbook.save(destination)

        except (OSError, PermissionError) as e:
            raise RuntimeError(f"Failed to export Excel to {destination}: {e}") from e


# =============================================================================
# END OF FILE
# =============================================================================