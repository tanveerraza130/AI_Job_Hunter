"""
JSON utilities for AI Job Hunter.

Provides reusable functions for JSON serialization and validation.
"""

from __future__ import annotations

import json
from typing import Any

from jobs.config.constants import MAX_METADATA_SIZE_BYTES


def validate_and_serialize_metadata(
    metadata: dict[str, Any] | None,
) -> str | None:
    """
    Validate and serialize metadata to JSON.

    Checks:
        1. Metadata is serializable to JSON
        2. Metadata size does not exceed MAX_METADATA_SIZE_BYTES

    Args:
        metadata: Metadata dictionary to validate and serialize.

    Returns:
        str | None: Serialized JSON string, or None if metadata is None.

    Raises:
        ValueError: If metadata cannot be serialized or exceeds size limit.
    """
    if metadata is None:
        return None

    try:
        metadata_json = json.dumps(metadata, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as e:
        raise ValueError(
            f"Metadata cannot be serialized to JSON: {e}"
        ) from e

    if len(metadata_json.encode("utf-8")) > MAX_METADATA_SIZE_BYTES:
        raise ValueError(
            f"Metadata exceeds maximum size of {MAX_METADATA_SIZE_BYTES} bytes. "
            f"Current size: {len(metadata_json.encode('utf-8'))} bytes"
        )

    return metadata_json


def safe_deserialize_metadata(metadata_json: str | None) -> dict[str, Any]:
    """
    Safely deserialize metadata from JSON.

    Args:
        metadata_json: JSON string to deserialize.

    Returns:
        dict[str, Any]: Deserialized metadata, or empty dict if None.
    """
    if metadata_json is None:
        return {}

    try:
        return json.loads(metadata_json)
    except (TypeError, ValueError):
        return {}


# =============================================================================
# END OF FILE
# =============================================================================