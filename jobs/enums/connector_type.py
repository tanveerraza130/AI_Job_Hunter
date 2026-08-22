"""
Connector type enums for AI Job Hunter.
"""

from __future__ import annotations

from enum import StrEnum


class ConnectorType(StrEnum):
    """Type of connector implementation."""

    UNKNOWN = "unknown"
    API = "api"
    PLAYWRIGHT = "playwright"
    BROWSER = "browser"
    MCP = "mcp"
    PROXY = "proxy"
    SCRAPER = "scraper"


# =============================================================================
# END OF FILE
# =============================================================================