"""
Base exporter interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from jobs.enums import ExportFormat
from jobs.job import Job


class BaseExporter(ABC):
    """
    Abstract base class for all exporters.

    Attributes:
        EXPORT_FORMAT: The format this exporter produces.
    """

    EXPORT_FORMAT: ExportFormat = ExportFormat.UNKNOWN

    @abstractmethod
    def export(
        self,
        jobs: list[Job],
        destination: Path,
    ) -> None:
        """
        Export jobs to the specified destination.

        Args:
            jobs: List of Job objects to export.
            destination: Destination path (file or directory).

        Raises:
            RuntimeError: If export fails.
        """
        ...


# =============================================================================
# END OF FILE
# =============================================================================