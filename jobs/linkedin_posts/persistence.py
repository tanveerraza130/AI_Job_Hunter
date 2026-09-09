"""
Persistence bootstrap for LinkedIn member hiring posts.

This module is intentionally isolated from the existing Job storage
and Engine repository initialization.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from jobs.linkedin_posts.repository import LinkedInHiringPostRepository


_SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def initialize_linkedin_hiring_posts(
    connection: duckdb.DuckDBPyConnection,
) -> LinkedInHiringPostRepository:
    """
    Apply the LinkedIn Hiring Posts schema and return its repository.

    The caller owns the DuckDB connection. This function never creates,
    replaces, or closes a database connection.
    """
    schema_sql = _SCHEMA_PATH.read_text(encoding="utf-8")
    connection.execute(schema_sql)

    return LinkedInHiringPostRepository(connection)
