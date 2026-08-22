from enum import StrEnum


class SearchType(StrEnum):
    """Search trigger."""

    MANUAL = "manual"
    SCHEDULED = "scheduled"
    AGENT = "agent"
    API = "api"