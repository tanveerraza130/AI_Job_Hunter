"""
Persistent application tracking store.

Job data remains in the read-only job_hunter.duckdb.
Application state is intentionally stored separately.
"""

from pathlib import Path
from datetime import datetime

import duckdb


DB_PATH = Path("data/application.duckdb")


def _connect() -> duckdb.DuckDBPyConnection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(DB_PATH))

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            job_id VARCHAR PRIMARY KEY,
            profile_id VARCHAR NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'saved',
            applied_at TIMESTAMP,
            notes VARCHAR NOT NULL DEFAULT '',
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    return connection


def get_application(job_id: str, profile_id: str) -> dict | None:
    connection = _connect()

    try:
        row = connection.execute(
            """
            SELECT
                job_id,
                profile_id,
                status,
                applied_at,
                notes,
                updated_at,
                created_at
            FROM applications
            WHERE job_id = ?
              AND profile_id = ?
            """,
            [job_id, profile_id],
        ).fetchone()

        if row is None:
            return None

        columns = [
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


def upsert_application(
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
                job_id,
                profile_id,
                status,
                applied_at,
                notes,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (job_id)
            DO UPDATE SET
                profile_id = excluded.profile_id,
                status = excluded.status,
                applied_at = excluded.applied_at,
                notes = excluded.notes,
                updated_at = excluded.updated_at
            """,
            [
                job_id,
                profile_id,
                status,
                applied_at,
                notes,
                now,
            ],
        )

        return get_application(
            job_id,
            profile_id,
        )

    finally:
        connection.close()

def delete_application(
    job_id: str,
    profile_id: str,
) -> None:
    connection = _connect()

    try:
        connection.execute(
            """
            DELETE FROM applications
            WHERE job_id = ?
              AND profile_id = ?
            """,
            [job_id, profile_id],
        )
    finally:
        connection.close()


def get_application_summary(
    profile_id: str,
) -> dict:
    connection = _connect()

    try:
        rows = connection.execute(
            """
            SELECT
                status,
                COUNT(*) AS count
            FROM applications
            WHERE profile_id = ?
            GROUP BY status
            """,
            [profile_id],
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
