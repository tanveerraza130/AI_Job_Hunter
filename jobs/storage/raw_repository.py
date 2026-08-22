"""
Raw data repository for portal API responses.

Stores complete raw request/response data from job portals
for audit, debugging, and re-processing purposes.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

import duckdb

logger = logging.getLogger(__name__)


class RawRepository:
    """
    Repository for storing raw portal API responses.

    This repository stores complete request and response data
    from job portals for audit, debugging, and re-processing.

    All timestamps are stored in UTC using native timestamp types.

    Attributes:
        connection: DuckDB connection (shared across repositories).
    """

    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        """
        Initialize the repository with a shared DuckDB connection.

        Args:
            connection: Active DuckDB connection.
        """
        self.connection: duckdb.DuckDBPyConnection = connection

    def _filter_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """
        Filter sensitive headers before storage.

        Removes headers that contain authentication tokens, session IDs,
        or other sensitive information.

        Args:
            headers: Raw request headers.

        Returns:
            dict[str, str]: Filtered headers safe for storage.
        """
        if not headers:
            return {}

        sensitive_keys = {
            "cookie",
            "cookies",
            "authorization",
            "x-csrf-token",
            "csrf-token",
            "x-api-key",
            "api-key",
            "apikey",
            "session",
            "session-id",
            "x-session-id",
            "token",
            "access-token",
            "refresh-token",
            "x-auth-token",
            "auth-token",
        }

        safe_headers = {}

        for key, value in headers.items():
            key_lower = key.lower()
            if key_lower in sensitive_keys:
                continue

            safe_headers[key] = value

        return safe_headers

    def _to_json(self, data: Any) -> str:
        """
        Convert data to compact JSON string.

        Args:
            data: Data to serialize.

        Returns:
            str: Compact JSON string.
        """
        if data is None:
            return "null"
        return json.dumps(data, separators=(",", ":"), ensure_ascii=False)

    def _now_utc(self) -> datetime:
        """
        Get current UTC timestamp.

        Returns:
            datetime: UTC datetime object.
        """
        return datetime.now(UTC)

    def save(
        self,
        search_id: str,
        portal: str,
        keyword: str,
        location: str,
        page_no: int,
        request_url: str,
        request_method: str,
        request_headers: dict[str, str],
        request_query: dict[str, Any],
        response_json: dict[str, Any],
        response_status: int | None = None,
        jobs_count: int | None = None,
    ) -> None:
        """
        Save a raw API request/response to the database.

        Args:
            search_id: Unique ID for this search session (UUID string).
            portal: Source portal name (lowercase, e.g., "naukri", "linkedin").
            keyword: User search keyword.
            location: User search location.
            page_no: API page number.
            request_url: Full API request URL.
            request_method: HTTP method.
            request_headers: Raw request headers (filtered internally).
            request_query: Query parameters.
            response_json: Complete API response.
            response_status: HTTP status code (optional).
            jobs_count: Number of jobs in this page (optional).

        Raises:
            RuntimeError: If save fails.
        """
        try:
            # Filter sensitive headers
            safe_headers = self._filter_headers(request_headers)

            # Serialize JSON to compact strings
            request_headers_json = self._to_json(safe_headers)
            request_query_json = self._to_json(request_query)
            response_json_json = self._to_json(response_json)

            # Calculate response size in bytes
            response_size_bytes = len(response_json_json.encode("utf-8"))

            # Generate UTC timestamp
            captured_at = self._now_utc()

            conn = self.connection

            conn.execute(
                """
                INSERT INTO portal_raw_data (
                    search_id,
                    portal,
                    keyword,
                    location,
                    page_no,
                    captured_at,
                    request_url,
                    request_method,
                    response_status,
                    request_headers,
                    request_query,
                    response_json,
                    jobs_count,
                    response_size_bytes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    search_id,
                    portal.lower(),
                    keyword,
                    location,
                    page_no,
                    captured_at,
                    request_url,
                    request_method,
                    response_status,
                    request_headers_json,
                    request_query_json,
                    response_json_json,
                    jobs_count,
                    response_size_bytes,
                ],
            )

            logger.debug("Saved raw data for %s page %s", portal, page_no)

        except duckdb.ConstraintException:
            logger.warning(
                "Duplicate raw data for %s page %s (search_id=%s) - skipping",
                portal,
                page_no,
                search_id,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to save raw data: {e}") from e


# =============================================================================
# END OF FILE
# =============================================================================