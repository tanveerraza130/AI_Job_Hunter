"""
Database utilities for AI Job Hunter.

Provides shared database utilities including schema generation
and CHECK constraint builders.
"""

from __future__ import annotations

from jobs.enums import (
    ConnectorType,
    Destination,
    ExportFormat,
    FinishedReason,
    Portal,
    SearchStatus,
    SearchType,
)


def enum_check_constraint(
    enum_class,
    column_name: str,
) -> str:
    """
    Generate a CHECK constraint SQL string from a Python Enum.

    Args:
        enum_class: The Enum class (e.g., Portal).
        column_name: The column name in the database.

    Returns:
        str: CHECK constraint SQL string.
    """
    values = [f"'{e.value}'" for e in enum_class]
    return f"CHECK ({column_name} IN ({', '.join(values)}))"


def build_search_session_schema() -> str:
    """
    Build the complete search_session table schema SQL.

    Returns:
        str: Complete CREATE TABLE SQL statement.
    """
    portal_check = enum_check_constraint(Portal, "portal")
    connector_check = enum_check_constraint(ConnectorType, "connector_type")
    search_type_check = enum_check_constraint(SearchType, "search_type")
    export_check = enum_check_constraint(ExportFormat, "export_format")
    destination_check = enum_check_constraint(Destination, "destination")
    status_check = enum_check_constraint(SearchStatus, "status")
    finished_reason_check = enum_check_constraint(FinishedReason, "finished_reason")

    return f"""
        CREATE TABLE IF NOT EXISTS search_session (
            execution_id UUID PRIMARY KEY,
            user_id UUID,
            workspace_id UUID,
            saved_search_id UUID,
            portal VARCHAR NOT NULL {portal_check},
            connector_type VARCHAR {connector_check},
            connector_version VARCHAR,
            engine_version VARCHAR,
            ai_pipeline_version VARCHAR,
            search_type VARCHAR {search_type_check},
            keyword VARCHAR NOT NULL,
            location VARCHAR,
            export_format VARCHAR {export_check},
            destination VARCHAR {destination_check},
            status VARCHAR NOT NULL {status_check},
            finished_reason VARCHAR {finished_reason_check},
            created_at TIMESTAMP NOT NULL,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            updated_at TIMESTAMP NOT NULL,
            duration_ms BIGINT,
            jobs_found INTEGER,
            duplicates_removed INTEGER,
            valid_jobs INTEGER,
            invalid_jobs INTEGER,
            exported_jobs INTEGER,
            error_message TEXT,
            metadata JSON,
            archived_at TIMESTAMP
        )
    """


# =============================================================================
# END OF FILE
# =============================================================================