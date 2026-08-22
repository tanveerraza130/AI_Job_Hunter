"""
Database connection for API.

Uses the single canonical AI Job Hunter DuckDB configured
through api.config.settings.db_path.
"""

import duckdb

from api.config import settings


def _resolve_db_path():
    """
    Resolve the canonical master DuckDB from application settings.
    """
    db_path = settings.db_path.resolve()

    if not db_path.exists():
        raise FileNotFoundError(
            f"Master database not found: {db_path}"
        )

    return db_path


def get_db() -> duckdb.DuckDBPyConnection:
    """
    Open a fresh read-only connection for every request.
    """
    db_path = _resolve_db_path()

    return duckdb.connect(
        str(db_path),
        read_only=True,
    )


def close_db() -> None:
    """
    Kept for compatibility.

    Connections are request-scoped.
    """
    return None
