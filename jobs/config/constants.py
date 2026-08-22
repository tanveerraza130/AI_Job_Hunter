"""
Central constants for AI Job Hunter.

Single source of truth for application-wide constant values.
"""

from __future__ import annotations

# =============================================================================
# Metadata
# =============================================================================

# Maximum serialized metadata size (10 KB)
MAX_METADATA_SIZE_BYTES: int = 10 * 1024


# =============================================================================
# Time
# =============================================================================

# All timestamps throughout the application are stored in UTC.
UTC_TIMEZONE: str = "UTC"


# =============================================================================
# END OF FILE
# =============================================================================