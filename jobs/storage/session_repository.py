"""
Search session repository for AI Job Hunter.

Tracks individual search executions. Each search_session represents
one complete search run from start to finish.

Phase 1: Single connector per session.

Phase 2 Design Note:
    When multi-connector support is added, the relationship will be:
        search_session (execution container)
            │
            ├── session_connector (per-connector details)
            │       │
            │       └── fact_jobs
            │
            ├── portal_raw_data (execution-level)
            │
            └── execution_events (observability)

Soft Delete: Sessions are archived (never hard-deleted).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import duckdb

from jobs.enums import (
    ConnectorType,
    Destination,
    ExportFormat,
    FinishedReason,
    Portal,
    SearchStatus,
    SearchType,
)
from jobs.utils.json_utils import safe_deserialize_metadata, validate_and_serialize_metadata
from jobs.version import AI_PIPELINE_VERSION, ENGINE_VERSION

logger = logging.getLogger(__name__)


class SessionRepository:
    """
    Repository for managing search sessions.

    Each session represents one complete search execution
    with its parameters and results summary.

    Phase 1: Single connector per session.

    Soft Delete: Sessions are archived (never hard-deleted).

    Attributes:
        connection: Shared DuckDB connection.
    """

    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        """
        Initialize the repository with a shared DuckDB connection.

        Args:
            connection: Active DuckDB connection.
        """
        self.connection: duckdb.DuckDBPyConnection = connection

    def start_session(
        self,
        portal: Portal,
        keyword: str,
        connector_version: str,
        location: str | None = None,
        user_id: UUID | None = None,
        workspace_id: UUID | None = None,
        saved_search_id: UUID | None = None,
        connector_type: ConnectorType | None = None,
        search_type: SearchType = SearchType.MANUAL,
        export_format: ExportFormat | None = None,
        destination: Destination | None = None,
        ai_pipeline_version: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> UUID:
        """
        Start a new search session.

        Args:
            portal: Source portal name.
            keyword: Search keyword.
            connector_version: Version of the connector (from connector instance).
            location: Search location (optional).
            user_id: Owner of this search session.
            workspace_id: Workspace/team context.
            saved_search_id: Reference to saved search (optional).
            connector_type: Type of connector used.
            search_type: How the search was initiated.
            export_format: Format of exported data.
            destination: Where data was exported.
            ai_pipeline_version: Version of the AI pipeline.
            metadata: Additional context (max 10KB).

        Returns:
            UUID: The execution ID.

        Raises:
            ValueError: If metadata cannot be serialized or exceeds size limit.
        """
        # Validate and serialize metadata
        metadata_json = validate_and_serialize_metadata(metadata)

        execution_id = uuid4()
        now = datetime.now(UTC)

        # Use defaults if not provided
        if ai_pipeline_version is None:
            ai_pipeline_version = AI_PIPELINE_VERSION

        conn = self.connection
        conn.execute(
            """
            INSERT INTO search_session (
                execution_id,
                user_id,
                workspace_id,
                saved_search_id,
                portal,
                connector_type,
                connector_version,
                engine_version,
                ai_pipeline_version,
                search_type,
                keyword,
                location,
                export_format,
                destination,
                status,
                created_at,
                started_at,
                updated_at,
                metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                execution_id,
                user_id,
                workspace_id,
                saved_search_id,
                portal.value,
                connector_type.value if connector_type else None,
                connector_version,
                ENGINE_VERSION,
                ai_pipeline_version,
                search_type.value,
                keyword,
                location,
                export_format.value if export_format else None,
                destination.value if destination else None,
                SearchStatus.RUNNING.value,
                now,  # created_at
                now,  # started_at
                now,  # updated_at
                metadata_json,
            ],
        )

        logger.info(
            "Started search session %s: portal=%s connector=%s status=%s",
            execution_id,
            portal.value,
            connector_type.value if connector_type else "unknown",
            SearchStatus.RUNNING.value,
        )
        return execution_id

    def _merge_metadata(
        self,
        existing_metadata: dict[str, Any],
        new_metadata: dict[str, Any] | None,
    ) -> tuple[dict[str, Any], bool]:
        """
        Merge new metadata into existing metadata.

        TODO Phase 2: Replace with atomic JSON update for concurrency safety.

        Args:
            existing_metadata: Existing metadata dictionary.
            new_metadata: New metadata to merge.

        Returns:
            tuple[dict[str, Any], bool]: (merged_metadata, has_changes)
        """
        if not new_metadata:
            return existing_metadata, False

        merged = existing_metadata.copy()
        changed = False

        for key, value in new_metadata.items():
            if key not in merged or merged[key] != value:
                merged[key] = value
                changed = True

        return merged, changed

    def complete_session(
        self,
        execution_id: UUID,
        status: SearchStatus = SearchStatus.COMPLETED,
        finished_reason: FinishedReason | None = None,
        jobs_found: int | None = None,
        duplicates_removed: int | None = None,
        valid_jobs: int | None = None,
        invalid_jobs: int | None = None,
        exported_jobs: int | None = None,
        duration_ms: int | None = None,
        error_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Complete a search session.

        NOTE: This method uses read-modify-write for metadata. In Phase 2,
        when concurrent workers exist, consider using atomic updates or
        a separate metadata table.

        Args:
            execution_id: The session to complete.
            status: Session status.
            finished_reason: Why the session ended.
            jobs_found: Total jobs collected.
            duplicates_removed: Duplicates removed.
            valid_jobs: Jobs that passed validation.
            invalid_jobs: Jobs that failed validation.
            exported_jobs: Jobs successfully exported.
            duration_ms: Total execution time in milliseconds.
            error_message: Error details if failed.
            metadata: Additional context to merge with existing.

        Raises:
            ValueError: If metadata cannot be serialized or exceeds size limit.
        """
        now = datetime.now(UTC)

        conn = self.connection

        # Get existing metadata if any
        existing = conn.execute(
            "SELECT metadata FROM search_session WHERE execution_id = ? AND archived_at IS NULL",
            [execution_id],
        ).fetchone()

        existing_metadata = {}
        if existing and existing[0]:
            existing_metadata = safe_deserialize_metadata(existing[0])

        # Merge metadata
        merged_metadata, metadata_changed = self._merge_metadata(existing_metadata, metadata)

        # Validate and serialize merged metadata
        metadata_json = validate_and_serialize_metadata(merged_metadata)

        # Update the session
        conn.execute(
            """
            UPDATE search_session
            SET status = ?,
                finished_reason = ?,
                completed_at = ?,
                updated_at = ?,
                duration_ms = ?,
                jobs_found = ?,
                duplicates_removed = ?,
                valid_jobs = ?,
                invalid_jobs = ?,
                exported_jobs = ?,
                error_message = ?,
                metadata = ?
            WHERE execution_id = ?
            AND archived_at IS NULL
            """,
            [
                status.value,
                finished_reason.value if finished_reason else None,
                now,
                now,
                duration_ms,
                jobs_found,
                duplicates_removed,
                valid_jobs,
                invalid_jobs,
                exported_jobs,
                error_message,
                metadata_json,
                execution_id,
            ],
        )

        logger.info(
            "Completed session %s: status=%s portal=%s jobs=%s",
            execution_id,
            status.value,
            conn.execute(
                "SELECT portal FROM search_session WHERE execution_id = ?",
                [execution_id],
            ).fetchone()[0],
            jobs_found,
        )

    def archive_session(self, execution_id: UUID) -> tuple[bool, str]:
        """
        Archive a search session (soft delete).

        Args:
            execution_id: The session to archive.

        Returns:
            tuple[bool, str]: (success, message)
                - True, "Archived" if session was archived
                - False, "Session not found" if session doesn't exist
                - False, "Session already archived" if already archived
        """
        # First, check if session exists and get its current state
        result = self.connection.execute(
            """
            SELECT execution_id, archived_at, portal
            FROM search_session
            WHERE execution_id = ?
            """,
            [execution_id],
        ).fetchone()

        if result is None:
            return False, "Session not found"

        if result[1] is not None:
            return False, "Session already archived"

        now = datetime.now(UTC)

        conn = self.connection
        conn.execute(
            """
            UPDATE search_session
            SET archived_at = ?,
                updated_at = ?
            WHERE execution_id = ?
            AND archived_at IS NULL
            """,
            [now, now, execution_id],
        )

        logger.info("Archived session %s: portal=%s", execution_id, result[2])
        return True, "Archived"

    def restore_session(self, execution_id: UUID) -> tuple[bool, str]:
        """
        Restore an archived search session.

        Args:
            execution_id: The session to restore.

        Returns:
            tuple[bool, str]: (success, message)
                - True, "Restored" if session was restored
                - False, "Session not found" if session doesn't exist
                - False, "Session not archived" if session is active
        """
        # First, check if session exists and get its current state
        result = self.connection.execute(
            """
            SELECT execution_id, archived_at, portal
            FROM search_session
            WHERE execution_id = ?
            """,
            [execution_id],
        ).fetchone()

        if result is None:
            return False, "Session not found"

        if result[1] is None:
            return False, "Session not archived"

        now = datetime.now(UTC)

        conn = self.connection
        conn.execute(
            """
            UPDATE search_session
            SET archived_at = NULL,
                updated_at = ?
            WHERE execution_id = ?
            AND archived_at IS NOT NULL
            """,
            [now, execution_id],
        )

        logger.info("Restored session %s: portal=%s", execution_id, result[2])
        return True, "Restored"

    def get_session_details(self, execution_id: UUID) -> dict[str, Any] | None:
        """
        Get full session details including metadata.

        Args:
            execution_id: The session to retrieve.

        Returns:
            dict or None: The session record.
        """
        result = self.connection.execute(
            """
            SELECT execution_id,
                   user_id,
                   workspace_id,
                   saved_search_id,
                   portal,
                   connector_type,
                   connector_version,
                   engine_version,
                   ai_pipeline_version,
                   search_type,
                   keyword,
                   location,
                   export_format,
                   destination,
                   status,
                   finished_reason,
                   created_at,
                   started_at,
                   completed_at,
                   updated_at,
                   duration_ms,
                   jobs_found,
                   duplicates_removed,
                   valid_jobs,
                   invalid_jobs,
                   exported_jobs,
                   error_message,
                   metadata,
                   archived_at
            FROM search_session
            WHERE execution_id = ?
            AND archived_at IS NULL
            """,
            [execution_id],
        ).fetchone()

        if not result:
            return None

        return {
            "execution_id": result[0],
            "user_id": result[1],
            "workspace_id": result[2],
            "saved_search_id": result[3],
            "portal": result[4],
            "connector_type": result[5],
            "connector_version": result[6],
            "engine_version": result[7],
            "ai_pipeline_version": result[8],
            "search_type": result[9],
            "keyword": result[10],
            "location": result[11],
            "export_format": result[12],
            "destination": result[13],
            "status": result[14],
            "finished_reason": result[15],
            "created_at": result[16],
            "started_at": result[17],
            "completed_at": result[18],
            "updated_at": result[19],
            "duration_ms": result[20],
            "jobs_found": result[21],
            "duplicates_removed": result[22],
            "valid_jobs": result[23],
            "invalid_jobs": result[24],
            "exported_jobs": result[25],
            "error_message": result[26],
            "metadata": safe_deserialize_metadata(result[27]),
            "archived_at": result[28],
        }

    def list_session_summaries(
        self,
        user_id: UUID | None = None,
        workspace_id: UUID | None = None,
        portal: Portal | None = None,
        status: SearchStatus | None = None,
        search_type: SearchType | None = None,
        include_archived: bool = False,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        List session summaries (without metadata).

        Args:
            user_id: Filter by user.
            workspace_id: Filter by workspace.
            portal: Filter by portal.
            status: Filter by status.
            search_type: Filter by search type.
            include_archived: Whether to include archived sessions.
            limit: Max results to return.
            offset: Pagination offset.

        Returns:
            list[dict]: List of session summaries.
        """
        query = """
            SELECT execution_id,
                   user_id,
                   workspace_id,
                   saved_search_id,
                   portal,
                   connector_type,
                   connector_version,
                   engine_version,
                   ai_pipeline_version,
                   search_type,
                   keyword,
                   location,
                   export_format,
                   destination,
                   status,
                   finished_reason,
                   created_at,
                   started_at,
                   completed_at,
                   updated_at,
                   duration_ms,
                   jobs_found,
                   duplicates_removed,
                   valid_jobs,
                   invalid_jobs,
                   exported_jobs,
                   error_message,
                   archived_at
            FROM search_session
            WHERE 1=1
        """
        params = []

        if not include_archived:
            query += " AND archived_at IS NULL"

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if workspace_id:
            query += " AND workspace_id = ?"
            params.append(workspace_id)

        if portal:
            query += " AND portal = ?"
            params.append(portal.value)

        if status:
            query += " AND status = ?"
            params.append(status.value)

        if search_type:
            query += " AND search_type = ?"
            params.append(search_type.value)

        query += " ORDER BY started_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        results = self.connection.execute(query, params).fetchall()

        return [
            {
                "execution_id": r[0],
                "user_id": r[1],
                "workspace_id": r[2],
                "saved_search_id": r[3],
                "portal": r[4],
                "connector_type": r[5],
                "connector_version": r[6],
                "engine_version": r[7],
                "ai_pipeline_version": r[8],
                "search_type": r[9],
                "keyword": r[10],
                "location": r[11],
                "export_format": r[12],
                "destination": r[13],
                "status": r[14],
                "finished_reason": r[15],
                "created_at": r[16],
                "started_at": r[17],
                "completed_at": r[18],
                "updated_at": r[19],
                "duration_ms": r[20],
                "jobs_found": r[21],
                "duplicates_removed": r[22],
                "valid_jobs": r[23],
                "invalid_jobs": r[24],
                "exported_jobs": r[25],
                "error_message": r[26],
                "archived_at": r[27],
            }
            for r in results
        ]


# =============================================================================
# END OF FILE
# =============================================================================