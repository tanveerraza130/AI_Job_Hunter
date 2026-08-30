"""
AI Job Hunter account storage.

User/account data is intentionally stored separately from
the read-only job database.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import duckdb


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "account.duckdb"


def _connect() -> duckdb.DuckDBPyConnection:
    """
    Open the account database without performing schema DDL.

    IMPORTANT:
    Schema creation must not happen here. This function is called by
    normal read/write requests, often concurrently. Running CREATE TABLE
    IF NOT EXISTS on every connection can cause DuckDB catalog
    write-write conflicts during simultaneous requests.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DB_PATH))


def _initialize_schema() -> None:
    """
    Initialize the account database schema once during application startup.

    This function is intentionally separate from _connect() so ordinary
    API requests never perform catalog-changing DDL.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(DB_PATH))

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR PRIMARY KEY,
                email VARCHAR NOT NULL UNIQUE,
                password_hash VARCHAR,
                auth_provider VARCHAR NOT NULL DEFAULT 'email',
                google_subject VARCHAR UNIQUE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                token_id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL,
                token_hash VARCHAR NOT NULL UNIQUE,
                expires_at TIMESTAMP NOT NULL,
                used_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id VARCHAR PRIMARY KEY,
                full_name VARCHAR NOT NULL,
                phone VARCHAR,
                profile_id VARCHAR NOT NULL,
                preferred_location VARCHAR NOT NULL,
                role_level VARCHAR NOT NULL,
                experience_years VARCHAR NOT NULL,
                current_ctc_lpa DOUBLE NOT NULL,
                expected_ctc_lpa DOUBLE NOT NULL,
                resume_path VARCHAR,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(user_id)
            )
            """
        )
    finally:
        connection.close()


_initialize_schema()


def create_user(
    email: str,
    password_hash: str | None = None,
    auth_provider: str = "email",
    google_subject: str | None = None,
) -> dict:
    connection = _connect()

    try:
        user_id = str(uuid4())
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        connection.execute(
            """
            INSERT INTO users (
                user_id,
                email,
                password_hash,
                auth_provider,
                google_subject,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                user_id,
                email.strip().lower(),
                password_hash,
                auth_provider,
                google_subject,
                now,
                now,
            ],
        )

        return {
            "user_id": user_id,
            "email": email.strip().lower(),
            "auth_provider": auth_provider,
            "google_subject": google_subject,
        }

    finally:
        connection.close()


def get_user_by_email(email: str) -> dict | None:
    connection = _connect()

    try:
        row = connection.execute(
            """
            SELECT
                user_id,
                email,
                password_hash,
                auth_provider,
                google_subject,
                created_at,
                updated_at
            FROM users
            WHERE LOWER(email) = LOWER(?)
            """,
            [email.strip()],
        ).fetchone()

        if row is None:
            return None

        columns = [
            "user_id",
            "email",
            "password_hash",
            "auth_provider",
            "google_subject",
            "created_at",
            "updated_at",
        ]

        return dict(zip(columns, row))

    finally:
        connection.close()


def get_user_by_id(user_id: str) -> dict | None:
    connection = _connect()

    try:
        row = connection.execute(
            """
            SELECT
                user_id,
                email,
                password_hash,
                auth_provider,
                google_subject,
                created_at,
                updated_at
            FROM users
            WHERE user_id = ?
            """,
            [user_id],
        ).fetchone()

        if row is None:
            return None

        columns = [
            "user_id",
            "email",
            "password_hash",
            "auth_provider",
            "google_subject",
            "created_at",
            "updated_at",
        ]

        return dict(zip(columns, row))

    finally:
        connection.close()


def create_or_replace_profile(
    user_id: str,
    full_name: str,
    phone: str | None,
    profile_id: str,
    preferred_location: str,
    role_level: str,
    experience_years: str,
    current_ctc_lpa: float,
    expected_ctc_lpa: float,
    resume_path: str | None = None,
) -> dict:
    connection = _connect()

    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        connection.execute(
            """
            INSERT INTO user_profiles (
                user_id,
                full_name,
                phone,
                profile_id,
                preferred_location,
                role_level,
                experience_years,
                current_ctc_lpa,
                expected_ctc_lpa,
                resume_path,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (user_id)
            DO UPDATE SET
                full_name = excluded.full_name,
                phone = excluded.phone,
                profile_id = excluded.profile_id,
                preferred_location = excluded.preferred_location,
                role_level = excluded.role_level,
                experience_years = excluded.experience_years,
                current_ctc_lpa = excluded.current_ctc_lpa,
                expected_ctc_lpa = excluded.expected_ctc_lpa,
                resume_path = excluded.resume_path,
                updated_at = excluded.updated_at
            """,
            [
                user_id,
                full_name.strip(),
                phone.strip() if phone else None,
                profile_id,
                preferred_location,
                role_level,
                experience_years,
                float(current_ctc_lpa),
                float(expected_ctc_lpa),
                resume_path,
                now,
                now,
            ],
        )

        return get_profile(user_id)

    finally:
        connection.close()


def get_profile(user_id: str) -> dict | None:
    connection = _connect()

    try:
        row = connection.execute(
            """
            SELECT
                user_id,
                full_name,
                phone,
                profile_id,
                preferred_location,
                role_level,
                experience_years,
                current_ctc_lpa,
                expected_ctc_lpa,
                resume_path,
                created_at,
                updated_at
            FROM user_profiles
            WHERE user_id = ?
            """,
            [user_id],
        ).fetchone()

        if row is None:
            return None

        columns = [
            "user_id",
            "full_name",
            "phone",
            "profile_id",
            "preferred_location",
            "role_level",
            "experience_years",
            "current_ctc_lpa",
            "expected_ctc_lpa",
            "resume_path",
            "created_at",
            "updated_at",
        ]

        return dict(zip(columns, row))

    finally:
        connection.close()


def create_password_reset_token(
    user_id: str,
    token_hash: str,
    expires_at: datetime,
) -> dict:
    connection = _connect()

    try:
        token_id = str(uuid4())

        connection.execute(
            """
            UPDATE password_reset_tokens
            SET used_at = ?
            WHERE user_id = ?
              AND used_at IS NULL
            """,
            [datetime.now(timezone.utc).replace(tzinfo=None), user_id],
        )

        connection.execute(
            """
            INSERT INTO password_reset_tokens (
                token_id,
                user_id,
                token_hash,
                expires_at
            )
            VALUES (?, ?, ?, ?)
            """,
            [
                token_id,
                user_id,
                token_hash,
                expires_at,
            ],
        )

        return {
            "token_id": token_id,
            "user_id": user_id,
            "expires_at": expires_at,
        }

    finally:
        connection.close()


def get_password_reset_token(
    token_hash: str,
) -> dict | None:
    connection = _connect()

    try:
        row = connection.execute(
            """
            SELECT
                token_id,
                user_id,
                token_hash,
                expires_at,
                used_at,
                created_at
            FROM password_reset_tokens
            WHERE token_hash = ?
            """,
            [token_hash],
        ).fetchone()

        if row is None:
            return None

        columns = [
            "token_id",
            "user_id",
            "token_hash",
            "expires_at",
            "used_at",
            "created_at",
        ]

        return dict(zip(columns, row))

    finally:
        connection.close()


def mark_password_reset_token_used(
    token_id: str,
) -> None:
    connection = _connect()

    try:
        connection.execute(
            """
            UPDATE password_reset_tokens
            SET used_at = ?
            WHERE token_id = ?
            """,
            [
                datetime.now(timezone.utc).replace(tzinfo=None),
                token_id,
            ],
        )

    finally:
        connection.close()


def update_user_password(
    user_id: str,
    password_hash: str,
) -> None:
    connection = _connect()

    try:
        connection.execute(
            """
            UPDATE users
            SET
                password_hash = ?,
                auth_provider = 'email',
                updated_at = ?
            WHERE user_id = ?
            """,
            [
                password_hash,
                datetime.now(timezone.utc).replace(tzinfo=None),
                user_id,
            ],
        )

    finally:
        connection.close()
