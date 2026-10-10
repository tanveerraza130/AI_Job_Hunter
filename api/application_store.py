"""
Persistent per-user application/job-status tracking.

Job data remains in the read-only job_hunter.duckdb.
Application state is stored separately in data/application.duckdb.

Ownership is enforced by (user_id, job_id).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import duckdb


DB_PATH = Path("data/application.duckdb")


def _connect() -> duckdb.DuckDBPyConnection:
    """
    Open the application database.

    IMPORTANT:
    No schema-changing DDL is performed here.
    The database schema is initialized/migrated separately.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DB_PATH))


def get_application(
    user_id: str,
    job_id: str,
) -> dict | None:
    connection = _connect()

    try:
        row = connection.execute(
            """
            SELECT
                user_id,
                job_id,
                profile_id,
                status,
                applied_at,
                notes,
                updated_at,
                created_at
            FROM applications
            WHERE user_id = ?
              AND job_id = ?
            """,
            [user_id, job_id],
        ).fetchone()

        if row is None:
            return None

        columns = [
            "user_id",
            "job_id",
            "profile_id",
            "status",
            "applied_at",
            "notes",
            "updated_at",
            "created_at",
        ]

        return dict(zip(columns, row))

    finally:
        connection.close()


def get_applications(
    user_id: str,
    job_ids: list[str],
) -> dict[str, dict]:
    """
    Return application records for one authenticated user.

    Only requested job IDs are returned.
    Missing jobs are intentionally omitted.
    """
    if not job_ids:
        return {}

    unique_job_ids = list(dict.fromkeys(job_ids))

    connection = _connect()

    try:
        placeholders = ", ".join(
            "?" for _ in unique_job_ids
        )

        rows = connection.execute(
            f"""
            SELECT
                user_id,
                job_id,
                profile_id,
                status,
                applied_at,
                notes,
                updated_at,
                created_at
            FROM applications
            WHERE user_id = ?
              AND job_id IN ({placeholders})
            """,
            [user_id, *unique_job_ids],
        ).fetchall()

        columns = [
            "user_id",
            "job_id",
            "profile_id",
            "status",
            "applied_at",
            "notes",
            "updated_at",
            "created_at",
        ]

        return {
            row[1]: dict(zip(columns, row))
            for row in rows
        }

    finally:
        connection.close()


def upsert_application(
    user_id: str,
    job_id: str,
    profile_id: str,
    status: str,
    applied_at: str | None,
    notes: str,
) -> dict:
    connection = _connect()

    try:
        now = datetime.now()

        connection.execute(
            """
            INSERT INTO applications (
                user_id,
                job_id,
                profile_id,
                status,
                applied_at,
                notes,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (user_id, job_id)
            DO UPDATE SET
                profile_id = excluded.profile_id,
                status = excluded.status,
                applied_at = excluded.applied_at,
                notes = excluded.notes,
                updated_at = excluded.updated_at
            """,
            [
                user_id,
                job_id,
                profile_id,
                status,
                applied_at,
                notes,
                now,
            ],
        )

        application = get_application(
            user_id,
            job_id,
        )

        if application is None:
            raise RuntimeError(
                "Application was saved but could not be reloaded."
            )

        return application

    finally:
        connection.close()


def delete_application(
    user_id: str,
    job_id: str,
) -> None:
    connection = _connect()

    try:
        connection.execute(
            """
            DELETE FROM applications
            WHERE user_id = ?
              AND job_id = ?
            """,
            [user_id, job_id],
        )

    finally:
        connection.close()


def get_application_summary(
    user_id: str,
) -> dict:
    connection = _connect()

    try:
        rows = connection.execute(
            """
            SELECT
                status,
                COUNT(*) AS count
            FROM applications
            WHERE user_id = ?
            GROUP BY status
            """,
            [user_id],
        ).fetchall()

        summary = {
            "saved": 0,
            "pending": 0,
            "applied": 0,
            "interview": 0,
            "rejected": 0,
            "offer": 0,
            "not_relevant": 0,
        }

        for status, count in rows:
            if status in summary:
                summary[status] = int(count)

        summary["total"] = sum(summary.values())

        return summary

    finally:
        connection.close()


def report_job_dead(
    user_id: str,
    job_id: str,
) -> dict:
    """
    Record that the given user reported this job as dead.

    Idempotent — re-reporting the same job by the same user
    updates the timestamp but does not double-count.
    Returns the current distinct-user report count.
    """
    if not user_id:
        raise ValueError("user_id is required")
    if not job_id:
        raise ValueError("job_id is required")

    connection = _connect()

    try:
        # Upsert a minimal application row (status stays 'saved' if new).
        # We use ON CONFLICT so we don't clobber any existing status.
        connection.execute(
            """
            INSERT INTO applications (
                user_id,
                job_id,
                profile_id,
                status,
                notes,
                reported_dead_at,
                updated_at,
                created_at
            )
            VALUES (?, ?, '', 'saved', '', NOW(), NOW(), NOW())
            ON CONFLICT (user_id, job_id) DO UPDATE SET
                reported_dead_at = NOW(),
                updated_at = NOW()
            """,
            [user_id, job_id],
        )

        count_row = connection.execute(
            """
            SELECT COUNT(DISTINCT user_id)
            FROM applications
            WHERE job_id = ?
              AND reported_dead_at IS NOT NULL
            """,
            [job_id],
        ).fetchone()

        count = int(count_row[0]) if count_row else 0

        connection.commit() if hasattr(connection, "commit") else None
        return {"job_id": job_id, "dead_report_count": count}

    finally:
        connection.close()


def count_dead_reports(
    job_id: str,
) -> int:
    """Return the number of distinct users who reported this job as dead."""
    if not job_id:
        return 0

    connection = _connect()

    try:
        row = connection.execute(
            """
            SELECT COUNT(DISTINCT user_id)
            FROM applications
            WHERE job_id = ?
              AND reported_dead_at IS NOT NULL
            """,
            [job_id],
        ).fetchone()

        return int(row[0]) if row else 0

    finally:
        connection.close()
