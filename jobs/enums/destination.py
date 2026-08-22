from enum import StrEnum


class Destination(StrEnum):
    """Execution destination."""

    LOCAL = "local"
    WEB = "web"
    API = "api"