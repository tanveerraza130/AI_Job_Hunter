"""
User preferences store — cross-device dashboard filter persistence.

Each user has exactly ONE preferences row (upsert semantics).
Filters are stored as JSON so the shape can evolve without migrations.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb

from api.config import settings

logger = logging.getLogger(__name__)


_db_path = Path(settings.db_path)


def _get_connection() -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(str(_db_path))
    return conn


def _ensure_table() -> None:
    """Create user_preferences table if it doesn't exist."""
    conn = _get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_preferences (
                user_id     VARCHAR PRIMARY KEY,
                filters     JSON NOT NULL,
                updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    finally:
        conn.close()


# Ensure table exists at import time
try:
    _ensure_table()
except Exception as exc:
    logger.warning("Failed to ensure user_preferences table: %s", exc)


def get_preferences(user_id: str) -> dict[str, Any] | None:
    """Return saved filters for user, or None if none saved."""
    if not user_id:
        return None

    conn = _get_connection()
    try:
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

        # DuckDB returns JSON as string; parse to dict
        if isinstance(raw_filters, str):
            filters = json.loads(raw_filters)
        elif isinstance(raw_filters, dict):
            filters = raw_filters
        else:
            filters = json.loads(str(raw_filters))

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

    # Size guard — 50KB max
    serialized = json.dumps(filters)
    if len(serialized) > 50_000:
        raise ValueError("filters payload too large (max 50KB)")

    conn = _get_connection()
    try:
        now = datetime.now(UTC)
        # DuckDB doesn't support ON CONFLICT for all versions; use DELETE + INSERT
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

    conn = _get_connection()
    try:
        conn.execute(
            "DELETE FROM user_preferences WHERE user_id = ?",
            [user_id],
        )
    finally:
        conn.close()
