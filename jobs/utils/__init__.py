"""
Utility functions for AI Job Hunter.

Provides shared utilities for database operations, JSON handling,
and other common tasks.
"""

from __future__ import annotations

from jobs.utils.db_utils import build_search_session_schema
from jobs.utils.json_utils import safe_deserialize_metadata, validate_and_serialize_metadata

__all__ = [
    "build_search_session_schema",
    "safe_deserialize_metadata",
    "validate_and_serialize_metadata",
]


# =============================================================================
# END OF FILE
# =============================================================================