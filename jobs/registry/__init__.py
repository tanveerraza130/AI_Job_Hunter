"""
Job Registry for AI Job Hunter.

Central authority for job identity, deduplication, and lifecycle tracking.
"""

from __future__ import annotations

from jobs.registry.models import JobStatus, RegistryRecord
from jobs.registry.registry import JobRegistry
from jobs.storage.job_registry_repository import JobRegistryRepository

__all__ = [
    "JobRegistry",
    "JobRegistryRepository",
    "JobStatus",
    "RegistryRecord",
]


# =============================================================================
# END OF FILE
# =============================================================================