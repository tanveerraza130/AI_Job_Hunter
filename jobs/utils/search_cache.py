"""
Search cache — skip keyword+city pairs recently fetched.

Prevents duplicate portal searches within a configurable window.
Cache is stored in the master DB (search_cache table).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import duckdb

logger = logging.getLogger(__name__)


CACHE_SCHEMA = """
CREATE TABLE IF NOT EXISTS search_cache (
    portal        VARCHAR NOT NULL,
    keyword       VARCHAR NOT NULL,
    location      VARCHAR NOT NULL,
    last_run_at   TIMESTAMP NOT NULL,
    jobs_found    INTEGER DEFAULT 0,
    jobs_exported INTEGER DEFAULT 0,
    PRIMARY KEY (portal, keyword, location)
);
"""


class SearchCache:
    """Simple search-result cache with a time-to-live."""

    def __init__(self, connection: duckdb.DuckDBPyConnection, ttl_days: int = 3) -> None:
        self.connection = connection
        self.ttl_days = ttl_days
        self.connection.execute(CACHE_SCHEMA)

    def should_skip(self, portal: str, keyword: str, location: str | None) -> bool:
        """Return True if this search ran within TTL."""
        loc = location or ""
        cutoff = datetime.now(UTC) - timedelta(days=self.ttl_days)
        row = self.connection.execute(
            """
            SELECT 1 FROM search_cache
            WHERE portal = ?
              AND keyword = ?
              AND location = ?
              AND last_run_at >= ?
            LIMIT 1
            """,
            [portal, keyword, loc, cutoff],
        ).fetchone()
        return row is not None

    def record(
        self,
        portal: str,
        keyword: str,
        location: str | None,
        jobs_found: int = 0,
        jobs_exported: int = 0,
    ) -> None:
        """Record or update a completed search."""
        loc = location or ""
        now = datetime.now(UTC)
        self.connection.execute(
            """
            INSERT INTO search_cache
                (portal, keyword, location, last_run_at, jobs_found, jobs_exported)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (portal, keyword, location) DO UPDATE SET
                last_run_at = EXCLUDED.last_run_at,
                jobs_found = EXCLUDED.jobs_found,
                jobs_exported = EXCLUDED.jobs_exported
            """,
            [portal, keyword, loc, now, jobs_found, jobs_exported],
        )

    def clear_stale(self) -> int:
        """Delete cache entries older than TTL."""
        cutoff = datetime.now(UTC) - timedelta(days=self.ttl_days)
        result = self.connection.execute(
            "DELETE FROM search_cache WHERE last_run_at < ?",
            [cutoff],
        )
        return result.rowcount if hasattr(result, "rowcount") else 0

    def stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        total = self.connection.execute(
            "SELECT COUNT(*) FROM search_cache"
        ).fetchone()[0]
        cutoff = datetime.now(UTC) - timedelta(days=self.ttl_days)
        fresh = self.connection.execute(
            "SELECT COUNT(*) FROM search_cache WHERE last_run_at >= ?",
            [cutoff],
        ).fetchone()[0]
        return {"total": total, "fresh": fresh, "stale": total - fresh, "ttl_days": self.ttl_days}
