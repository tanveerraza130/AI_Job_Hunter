"""
Job Registry for AI Job Hunter.

Central authority for job identity, deduplication, and lifecycle tracking.

Responsibilities:
    - Generate deterministic fingerprints for jobs
    - Check if a job already exists in the system
    - Save new jobs
    - Track job status (NEW, SEEN, APPLIED, REJECTED, EXPIRED)
    - Enforce state machine transitions

All persistence is delegated to JobRegistryRepository.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Iterable

from jobs.job import Job
from jobs.registry.models import ALLOWED_TRANSITIONS, JobStatus, RegistryRecord
from jobs.storage.job_registry_repository import JobRegistryRepository

logger = logging.getLogger(__name__)

# Fields used for fallback fingerprint when no external_id is available
_FALLBACK_FIELDS: tuple[str, ...] = (
    "portal",
    "company",
    "title",
    "location",
    "experience",
    "employment_type",
)


def _normalize_fields(fields: dict[str, str]) -> str:
    """
    Normalize fields for fingerprint generation.

    Args:
        fields: Dictionary of field names to values.

    Returns:
        str: Normalized, concatenated string for hashing.
    """
    normalized = []

    for key in _FALLBACK_FIELDS:
        value = fields.get(key, "")
        normalized.append(value.lower().strip())

    return "|".join(normalized)


def _get_experience_string(job: Job) -> str:
    """
    Get experience string from a Job object.

    Args:
        job: Job object.

    Returns:
        str: Experience string (e.g., "3-5").
    """
    if job.experience_min is not None or job.experience_max is not None:
        min_exp = job.experience_min or 0
        max_exp = job.experience_max or 0
        return f"{min_exp}-{max_exp}"
    return ""


def _generate_fingerprint(job: Job) -> str:
    """
    Generate a deterministic SHA256 fingerprint for a job.

    Priority:
        1. If portal and job_id exist: uses portal + job_id
        2. Otherwise, if job_url exists: uses normalized job_url
        3. Otherwise: uses fallback fields

    Args:
        job: Job object.

    Returns:
        str: SHA256 fingerprint (64 hex characters).

    This is an internal function. The Registry uses it for deduplication.
    No other module should call this directly.
    """
    # Priority 1: Portal + Job ID (stable portal-provided ID)
    if job.portal and job.job_id:
        key = f"{job.portal}|{job.job_id}"
        return hashlib.sha256(
            key.lower().encode("utf-8")
        ).hexdigest()

    # Priority 2: Job URL (stable external identity when available)
    if job.job_url:
        normalized_url = job.job_url.strip()
        return hashlib.sha256(
            normalized_url.encode("utf-8")
        ).hexdigest()

    # Priority 3: Fallback to core fields
    fields = {
        "portal": job.portal or "unknown",
        "company": job.company or "unknown",
        "title": job.title or "unknown",
        "location": job.location or "unknown",
        "experience": _get_experience_string(job),
        "employment_type": job.employment_type or "",
    }

    key = _normalize_fields(fields)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


class JobRegistry:
    """
    Central authority for job identity and lifecycle.

    All job-related identity checks go through this Registry.

    Attributes:
        repo: JobRegistryRepository instance.
    """

    def __init__(self, repo: JobRegistryRepository) -> None:
        """
        Initialize the Registry with a repository.

        Args:
            repo: JobRegistryRepository instance.
        """
        self.repo = repo

    def _get_fingerprint(self, job: Job) -> str:
        """Generate fingerprint for a job."""
        return _generate_fingerprint(job)

    def exists(self, job: Job) -> bool:
        """
        Check if a job already exists in the registry.

        Args:
            job: Job object to check.

        Returns:
            bool: True if the job exists, False otherwise.
        """
        fingerprint = self._get_fingerprint(job)
        return self.repo.exists(fingerprint)

    def save(self, job: Job) -> None:
        """
        Save a new job to the registry.

        If the job already exists, it is ignored (race condition safe).

        Args:
            job: Job object to save.
        """
        fingerprint = self._get_fingerprint(job)

        inserted = self.repo.insert_or_ignore(
            fingerprint=fingerprint,
            portal=job.portal or "unknown",
            portal_job_id=job.job_id or "",
            company=job.company or "",
            title=job.title or "",
            location=job.location or "",
            status=JobStatus.NEW.value,
            metadata={
            "discovery_keyword": job.discovery_keyword,
        },
        )

        if inserted:
            logger.info("Saved new job: %s at %s", job.title, job.company)
        else:
            logger.debug("Job already exists: %s at %s", job.title, job.company)

    def get_existing_portal_job_ids(
        self,
        portal: str,
        portal_job_ids: Iterable[str],
    ) -> set[str]:
        """
        Return portal job IDs already present in the registry.

        Args:
            portal: Source portal.
            portal_job_ids: Portal-provided job IDs to check.

        Returns:
            set[str]: IDs already present in the registry.
        """
        return self.repo.get_existing_portal_job_ids(
            portal=portal,
            portal_job_ids=portal_job_ids,
        )

    def _transition_to(
        self,
        job: Job,
        target_status: JobStatus,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Internal method to transition a job to a new status.

        This method enforces the state machine transitions.

        Args:
            job: Job object to update.
            target_status: The target status.
            metadata: Optional metadata to merge.

        Raises:
            RuntimeError: If the job doesn't exist or transition is invalid.
        """
        fingerprint = self._get_fingerprint(job)
        current = self.repo.get(fingerprint)

        if not current:
            raise RuntimeError(f"Job not found: {job.title} at {job.company}")

        current_status = current.status

        # Check if transition is allowed
        if target_status not in ALLOWED_TRANSITIONS.get(current_status, set()):
            raise RuntimeError(
                f"Invalid transition: {current_status.value} → {target_status.value} "
                f"for {job.title} at {job.company}"
            )

        # Map status to timestamp column
        timestamp_map = {
            JobStatus.APPLIED: "applied_at",
            JobStatus.REJECTED: "rejected_at",
            JobStatus.EXPIRED: "expired_at",
        }

        timestamp_column = timestamp_map.get(target_status)

        self.repo.update_status(
            fingerprint,
            target_status.value,
            timestamp_column=timestamp_column,
            metadata=metadata,
        )

        logger.info(
            "Job transitioned: %s → %s for %s at %s",
            current_status.value,
            target_status.value,
            job.title,
            job.company,
        )

    def mark_applied(self, job: Job, metadata: dict[str, Any] | None = None) -> None:
        """
        Mark a job as applied.

        Args:
            job: Job object to update.
            metadata: Additional context.
        """
        self._transition_to(job, JobStatus.APPLIED, metadata)

    def mark_rejected(
        self,
        job: Job,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Mark a job as rejected.

        Args:
            job: Job object to update.
            reason: Optional rejection reason.
            metadata: Additional context.
        """
        merged_metadata = metadata or {}
        if reason:
            merged_metadata["rejection_reason"] = reason

        self._transition_to(job, JobStatus.REJECTED, merged_metadata)

    def mark_expired(self, job: Job, metadata: dict[str, Any] | None = None) -> None:
        """
        Mark a job as expired.

        Args:
            job: Job object to update.
            metadata: Additional context.
        """
        self._transition_to(job, JobStatus.EXPIRED, metadata)

    def mark_seen(self, job: Job) -> None:
        """
        Mark a job as seen (update last_seen_at).

        This is used during cron runs to update the timestamp without
        creating a new record.

        Args:
            job: Job object to update.

        Raises:
            RuntimeError: If the job doesn't exist.
        """
        fingerprint = self._get_fingerprint(job)
        current = self.repo.get(fingerprint)

        if not current:
            raise RuntimeError(f"Job not found: {job.title} at {job.company}")

        # If status is NEW, transition to SEEN
        if current.status == JobStatus.NEW:
            self._transition_to(job, JobStatus.SEEN)
        else:
            # Just update last_seen_at
            self.repo.update_last_seen(fingerprint)

        logger.debug("Marked job as seen: %s at %s", job.title, job.company)

    def mark_seen_many(self, jobs: Iterable[Job]) -> None:
        """
        Mark multiple jobs as SEEN in a single bulk operation.

        Only transitions NEW jobs to SEEN. Protects terminal states
        (APPLIED, REJECTED, EXPIRED) from being overwritten.

        Args:
            jobs: Iterable of Job objects to mark as SEEN.
        """
        fingerprints = [
            self._get_fingerprint(job)
            for job in jobs
            if job is not None
        ]

        if fingerprints:
            self.repo.mark_seen_many(fingerprints)

    def get_status(self, job: Job) -> JobStatus | None:
        """
        Get the status of a job.

        Args:
            job: Job object to check.

        Returns:
            JobStatus: The job status, or None if not found.
        """
        fingerprint = self._get_fingerprint(job)
        result = self.repo.get(fingerprint)

        if not result:
            return None

        return result.status

    def get_new_jobs(self, limit: int = 100) -> list[RegistryRecord]:
        """
        Get all NEW jobs.

        Useful for AI scoring or notification systems.

        Args:
            limit: Max results to return.

        Returns:
            list[RegistryRecord]: List of new jobs.
        """
        return self.repo.get_new_jobs(limit)

    def expire_old_jobs(self, older_than_days: int = 30) -> int:
        """
        Mark jobs as expired if they haven't been seen in X days.

        Args:
            older_than_days: Number of days before expiring.

        Returns:
            int: Number of jobs marked as expired.
        """
        return self.repo.expire_old_jobs(older_than_days)


# =============================================================================
# END OF FILE
# =============================================================================