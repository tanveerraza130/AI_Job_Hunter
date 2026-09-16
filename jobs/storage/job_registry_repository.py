"""
Job Registry Repository for AI Job Hunter.

Handles DuckDB operations for the job registry.
No business logic. Only data access.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import duckdb

from jobs.registry.models import (
    JobStatus,
    RegistryRecord,
    VALID_TIMESTAMP_COLUMNS,
)

logger = logging.getLogger(__name__)


class JobRegistryRepository:
    """
    Repository for job registry data.

    Responsibilities:
        - CRUD operations on registry records
        - Query by status, fingerprint, etc.

    No business logic. No state management.
    """

    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        """
        Initialize the repository with a shared DuckDB connection.

        Args:
            connection: Active DuckDB connection.
        """
        self.connection: duckdb.DuckDBPyConnection = connection

    def _serialize_metadata(self, metadata: dict[str, Any] | None) -> str | None:
        """
        Serialize metadata to JSON string.

        Args:
            metadata: Metadata dictionary.

        Returns:
            str or None: JSON string, or None if metadata is None.
        """
        if metadata is None:
            return None
        return json.dumps(metadata, separators=(",", ":"), ensure_ascii=False)

    def _deserialize_metadata(self, metadata_json: str | None) -> dict[str, Any] | None:
        """
        Deserialize metadata from JSON string.

        Args:
            metadata_json: JSON string.

        Returns:
            dict or None: Deserialized metadata, or None if input is None.
        """
        if metadata_json is None:
            return None
        try:
            return json.loads(metadata_json)
        except (TypeError, ValueError):
            return None

    def _json_merge_patch(self, base: str | None, patch: str) -> str:
        """
        Merge two JSON objects using json_merge_patch.

        Args:
            base: Base JSON string (can be None).
            patch: Patch JSON string.

        Returns:
            str: Merged JSON string.
        """
        if base is None:
            base = "{}"

        result = self.connection.execute(
            "SELECT json_merge_patch(?, ?)",
            [base, patch],
        ).fetchone()[0]

        return result

    def get(self, fingerprint: str) -> RegistryRecord | None:
        """
        Get a registry record by fingerprint.

        Args:
            fingerprint: SHA256 fingerprint.

        Returns:
            RegistryRecord or None: The record, or None if not found.
        """
        result = self.connection.execute(
            """
            SELECT fingerprint,
                   portal,
                   portal_job_id,
                   company,
                   title,
                   location,
                   status,
                   first_seen_at,
                   last_seen_at,
                   applied_at,
                   rejected_at,
                   expired_at,
                   metadata
            FROM job_registry
            WHERE fingerprint = ?
            """,
            [fingerprint],
        ).fetchone()

        if not result:
            return None

        return RegistryRecord(
            fingerprint=result[0],
            portal=result[1],
            portal_job_id=result[2] or "",
            company=result[3],
            title=result[4],
            location=result[5] or "",
            status=JobStatus(result[6]),
            first_seen_at=result[7],
            last_seen_at=result[8],
            applied_at=result[9],
            rejected_at=result[10],
            expired_at=result[11],
            metadata=self._deserialize_metadata(result[12]),
        )

    def exists(self, fingerprint: str) -> bool:
        """
        Check if a fingerprint exists in the registry.

        Args:
            fingerprint: SHA256 fingerprint.

        Returns:
            bool: True if it exists.
        """
        result = self.connection.execute(
            "SELECT 1 FROM job_registry WHERE fingerprint = ?",
            [fingerprint],
        ).fetchone()
        return result is not None

    def get_existing_portal_job_ids(
        self,
        portal: str,
        portal_job_ids: Iterable[str],
    ) -> set[str]:
        """
        Return portal job IDs that already exist in the registry.

        Performs one bulk query instead of one query per job.

        Args:
            portal: Source portal.
            portal_job_ids: Portal-provided job IDs to check.

        Returns:
            set[str]: IDs already present in the registry.
        """
        ids = {
            str(job_id).strip()
            for job_id in portal_job_ids
            if job_id is not None and str(job_id).strip()
        }

        if not ids:
            return set()

        placeholders = ", ".join("?" for _ in ids)

        rows = self.connection.execute(
            f"""
            SELECT portal_job_id
            FROM job_registry
            WHERE portal = ?
              AND portal_job_id IN ({placeholders})
            """,
            [portal, *sorted(ids)],
        ).fetchall()

        return {row[0] for row in rows if row[0]}

    def _portal_job_id_exists(self, portal: str, portal_job_id: str) -> bool:
        """
        Check if a portal_job_id already exists for the given portal.

        Args:
            portal: Source portal.
            portal_job_id: Portal's job ID.

        Returns:
            bool: True if it exists.
        """
        if not portal_job_id:
            return False

        result = self.connection.execute(
            """
            SELECT 1 FROM job_registry
            WHERE portal = ? AND portal_job_id = ?
            """,
            [portal, portal_job_id],
        ).fetchone()

        return result is not None

    def insert_or_ignore(
        self,
        fingerprint: str,
        portal: str,
        portal_job_id: str,
        company: str,
        title: str,
        location: str,
        status: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Insert a new registry record, ignoring if it already exists.

        Also enforces uniqueness of portal + portal_job_id when portal_job_id is present.

        Uses RETURNING to reliably determine if insertion succeeded.

        Args:
            fingerprint: SHA256 fingerprint.
            portal: Source portal.
            portal_job_id: Portal's job ID.
            company: Company name.
            title: Job title.
            location: Job location.
            status: Job status.
            metadata: Additional context.

        Returns:
            bool: True if inserted, False if already existed.
        """
        # Check for duplicate portal_job_id within the same portal
        if portal_job_id and self._portal_job_id_exists(portal, portal_job_id):
            logger.debug(
                "portal_job_id '%s' already exists for portal '%s'",
                portal_job_id,
                portal,
            )
            return False

        # Check for duplicate fingerprint
        if self.exists(fingerprint):
            return False

        now = datetime.now(UTC)
        metadata_json = self._serialize_metadata(metadata)

        result = self.connection.execute(
            """
            INSERT INTO job_registry (
                fingerprint,
                portal,
                portal_job_id,
                company,
                title,
                location,
                status,
                first_seen_at,
                last_seen_at,
                metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                fingerprint,
                portal,
                portal_job_id,
                company,
                title,
                location,
                status,
                now,
                now,
                metadata_json,
            ],
        )

        # Check if any row was affected
        return self.exists(fingerprint)

    def update_status(
        self,
        fingerprint: str,
        status: str,
        timestamp_column: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Update the status of a registry record.

        Args:
            fingerprint: SHA256 fingerprint.
            status: New status.
            timestamp_column: Optional timestamp column to update.
            metadata: Optional metadata to merge.

        Raises:
            ValueError: If timestamp_column is not in VALID_TIMESTAMP_COLUMNS.
        """
        if timestamp_column and timestamp_column not in VALID_TIMESTAMP_COLUMNS:
            raise ValueError(
                f"Invalid timestamp column: {timestamp_column}. "
                f"Must be one of: {', '.join(VALID_TIMESTAMP_COLUMNS)}"
            )

        now = datetime.now(UTC)
        metadata_json = self._serialize_metadata(metadata)

        query = """
            UPDATE job_registry
            SET status = ?,
                last_seen_at = ?
        """
        params = [status, now]

        if timestamp_column:
            query += f", {timestamp_column} = ?"
            params.append(now)

        if metadata_json:
            # Get current metadata, then merge using json_merge_patch
            current = self.get(fingerprint)
            current_metadata_json = self._serialize_metadata(current.metadata if current else None)

            if current_metadata_json:
                merged = self._json_merge_patch(current_metadata_json, metadata_json)
            else:
                merged = metadata_json

            query += ", metadata = ?"
            params.append(merged)

        query += " WHERE fingerprint = ?"
        params.append(fingerprint)

        self.connection.execute(query, params)

    def update_last_seen(self, fingerprint: str) -> None:
        """
        Update the last_seen_at timestamp.

        Args:
            fingerprint: SHA256 fingerprint.
        """
        now = datetime.now(UTC)

        self.connection.execute(
            """
            UPDATE job_registry
            SET last_seen_at = ?
            WHERE fingerprint = ?
            """,
            [now, fingerprint],
        )

    def get_by_status(
        self,
        status: JobStatus,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RegistryRecord]:
        """
        Get registry records by status.

        Args:
            status: Job status.
            limit: Max results to return.
            offset: Pagination offset.

        Returns:
            list[RegistryRecord]: List of records.
        """
        results = self.connection.execute(
            """
            SELECT fingerprint,
                   portal,
                   portal_job_id,
                   company,
                   title,
                   location,
                   status,
                   first_seen_at,
                   last_seen_at,
                   applied_at,
                   rejected_at,
                   expired_at,
                   metadata
            FROM job_registry
            WHERE status = ?
            ORDER BY first_seen_at DESC
            LIMIT ?
            OFFSET ?
            """,
            [status.value, limit, offset],
        ).fetchall()

        return [
            RegistryRecord(
                fingerprint=r[0],
                portal=r[1],
                portal_job_id=r[2] or "",
                company=r[3],
                title=r[4],
                location=r[5] or "",
                status=JobStatus(r[6]),
                first_seen_at=r[7],
                last_seen_at=r[8],
                applied_at=r[9],
                rejected_at=r[10],
                expired_at=r[11],
                metadata=self._deserialize_metadata(r[12]),
            )
            for r in results
        ]

    def get_new_jobs(self, limit: int = 100) -> list[RegistryRecord]:
        """
        Get all NEW jobs.

        Useful for AI scoring or notification systems.

        Args:
            limit: Max results to return.

        Returns:
            list[RegistryRecord]: List of new jobs.
        """
        return self.get_by_status(JobStatus.NEW, limit)

    def expire_old_jobs(self, older_than_days: int = 30) -> int:
        """
        Mark jobs as expired if they haven't been seen in X days.

        Args:
            older_than_days: Number of days before expiring.

        Returns:
            int: Number of jobs marked as expired.
        """
        cutoff = datetime.now(UTC) - timedelta(days=older_than_days)
        now = datetime.now(UTC)

        result = self.connection.execute(
            """
            UPDATE job_registry
            SET status = 'EXPIRED',
                expired_at = ?
            WHERE status NOT IN ('APPLIED', 'REJECTED', 'EXPIRED')
            AND last_seen_at < ?
            RETURNING fingerprint
            """,
            [now, cutoff],
        ).fetchall()

        return len(result)

    def get_stats(self) -> dict[str, int]:
        """
        Get statistics about the registry.

        Returns:
            dict: Status counts.
        """
        results = self.connection.execute("""
            SELECT status, COUNT(*) as count
            FROM job_registry
            GROUP BY status
        """).fetchall()

        stats = {}
        for row in results:
            stats[row[0]] = row[1]

        return stats

    def mark_seen_many(self, fingerprints: list[str]) -> None:
        """
        Mark multiple jobs as SEEN in a single bulk operation.

        Updates status to 'SEEN' and updates last_seen_at for all fingerprints.
        Only updates jobs that are currently NEW (protects terminal states).

        Args:
            fingerprints: List of SHA256 fingerprints to mark as SEEN.
        """
        if not fingerprints:
            return

        now = datetime.now(UTC)

        seen_status = JobStatus.SEEN.value
        new_status = JobStatus.NEW.value

        placeholders = ",".join("?" for _ in fingerprints)
        query = f"""
            UPDATE job_registry
            SET status = ?,
                last_seen_at = ?
            WHERE fingerprint IN ({placeholders})
            AND status = ?
        """

        self.connection.execute(query, [seen_status, now] + fingerprints + [new_status])


# =============================================================================
# END OF FILE
# =============================================================================