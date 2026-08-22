"""
Job Registry Models for AI Job Hunter.

Defines the job lifecycle state machine and allowed transitions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class JobStatus(str, Enum):
    """The status of a job in the registry."""

    NEW = "NEW"
    SEEN = "SEEN"
    APPLIED = "APPLIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

    def is_terminal(self) -> bool:
        """Check if this status is terminal (no further transitions)."""
        return self in (JobStatus.REJECTED, JobStatus.EXPIRED)


# Explicit transition map for the state machine
ALLOWED_TRANSITIONS = {
    JobStatus.NEW: {
        JobStatus.SEEN,
        JobStatus.APPLIED,
        JobStatus.REJECTED,
        JobStatus.EXPIRED,
    },
    JobStatus.SEEN: {
        JobStatus.SEEN,
        JobStatus.APPLIED,
        JobStatus.REJECTED,
        JobStatus.EXPIRED,
    },
    JobStatus.APPLIED: {
        JobStatus.APPLIED,  # Only update timestamp
    },
    JobStatus.REJECTED: set(),  # Terminal
    JobStatus.EXPIRED: set(),   # Terminal
}

# Valid timestamp columns for safe SQL updates
VALID_TIMESTAMP_COLUMNS: frozenset[str] = frozenset({
    "applied_at",
    "rejected_at",
    "expired_at",
})


@dataclass
class RegistryRecord:
    """
    A record from the job registry.

    Attributes:
        fingerprint: SHA256 fingerprint.
        portal: Source portal.
        portal_job_id: Portal's job ID.
        company: Company name.
        title: Job title.
        location: Job location.
        status: Job status.
        first_seen_at: First time seen.
        last_seen_at: Last time seen.
        applied_at: Applied timestamp.
        rejected_at: Rejected timestamp.
        expired_at: Expired timestamp.
        metadata: Additional context.
    """
    fingerprint: str
    portal: str
    portal_job_id: str
    company: str
    title: str
    location: str
    status: JobStatus
    first_seen_at: datetime
    last_seen_at: datetime
    applied_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None


# =============================================================================
# END OF FILE
# =============================================================================