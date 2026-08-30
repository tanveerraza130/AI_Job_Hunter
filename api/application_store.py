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
