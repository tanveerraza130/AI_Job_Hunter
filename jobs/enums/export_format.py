"""
Export format enums for AI Job Hunter.
"""

from __future__ import annotations

from enum import StrEnum


class ExportFormat(StrEnum):
    """Export format for job data."""

    UNKNOWN = "unknown"
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    DUCKDB = "duckdb"
    PARQUET = "parquet"


# =============================================================================
# END OF FILE
# =============================================================================