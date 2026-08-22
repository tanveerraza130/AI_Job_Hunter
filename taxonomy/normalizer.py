"""
Shared text normalization pipeline.
"""

from __future__ import annotations

import re


class Normalizer:
    """Shared normalization pipeline for all text."""

    @staticmethod
    def normalize(text: str) -> str:
        """Normalize text for deterministic taxonomy matching."""
        if not text:
            return ""

        text = str(text).lower()

        # Normalize common semantic punctuation.
        text = text.replace("&", " and ")

        # Normalize separators.
        text = re.sub(r"[-_]", " ", text)

        # Remove punctuation/special characters while preserving
        # alphanumeric characters and whitespace.
        text = re.sub(r"[^\w\s]", " ", text)

        # Collapse whitespace.
        text = re.sub(r"\s+", " ", text)

        return text.strip()
