"""
Persistent per-user dashboard filter preferences (cross-device sync).

Stored in a SEPARATE DuckDB file (data/preferences.duckdb) to avoid
conflicts with the API's read-only job database.

Ownership is enforced by user_id.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb

logger = logging.getLogger(__name__)


DB_PATH = Path("data/preferences.duckdb")


def _connect() -> duckdb.DuckDBPyConnection:
    """
    Open the preferences database.

    Schema-changing DDL is performed separately in _ensure_table().
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DB_PATH))


def _ensure_table() -> None:
    """Create user_preferences table if it doesn't exist."""
    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id     VARCHAR PRIMARY KEY,
                filters     VARCHAR NOT NULL,
                updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    finally:
        conn.close()


# Ensure table exists at import time
try:
    _ensure_table()
    logger.info("preferences_store ready at %s", DB_PATH)
except Exception as exc:
    logger.warning("Failed to ensure preferences table: %s", exc)


def get_preferences(user_id: str) -> dict[str, Any] | None:
    """Return saved filters for user, or None if none saved."""
    if not user_id:
        return None

    conn = _connect()
    try:
        _ensure_table()  # Safety net

        row = conn.execute(
            """
            SELECT filters, updated_at
            FROM user_preferences
            WHERE user_id = ?
            """,
            [user_id],
        ).fetchone()

        if not row:
            return None

        raw_filters = row[0]
        updated_at = row[1]

        # Parse JSON string
        if isinstance(raw_filters, str):
            filters = json.loads(raw_filters)
        else:
            filters = raw_filters

        return {
            "filters": filters,
            "updated_at": updated_at.isoformat() if updated_at else None,
        }
    finally:
        conn.close()


def save_preferences(user_id: str, filters: dict[str, Any]) -> None:
    """Upsert user's preferences."""
    if not user_id:
        raise ValueError("user_id is required")

    if not isinstance(filters, dict):
        raise ValueError("filters must be a dict")

    serialized = json.dumps(filters)
    if len(serialized) > 50_000:
        raise ValueError("filters payload too large (max 50KB)")

    conn = _connect()
    try:
        _ensure_table()  # Safety net

        now = datetime.now(UTC)

        # DuckDB doesn't guarantee ON CONFLICT on all versions → delete + insert
        conn.execute(
            "DELETE FROM user_preferences WHERE user_id = ?",
            [user_id],
        )
        conn.execute(
            """
            INSERT INTO user_preferences (user_id, filters, updated_at)
            VALUES (?, ?, ?)
            """,
            [user_id, serialized, now],
        )
    finally:
        conn.close()


def clear_preferences(user_id: str) -> None:
    """Delete user's preferences."""
    if not user_id:
        return

    conn = _connect()
    try:
        _ensure_table()  # Safety net

        conn.execute(
            "DELETE FROM user_preferences WHERE user_id = ?",
            [user_id],
        )
    finally:
        conn.close()
