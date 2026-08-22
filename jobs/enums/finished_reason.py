from enum import StrEnum


class FinishedReason(StrEnum):
    """Execution completion reason."""

    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    LIMIT_REACHED = "limit_reached"