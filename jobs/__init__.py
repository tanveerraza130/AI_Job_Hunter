"""
AI Job Hunter - Main Package.

A production-ready job hunting platform with AI capabilities.
"""

from __future__ import annotations

from jobs.registry import JobRegistry, JobStatus, RegistryRecord
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