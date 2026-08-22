from enum import StrEnum


class SearchStatus(StrEnum):
    """Execution status."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"