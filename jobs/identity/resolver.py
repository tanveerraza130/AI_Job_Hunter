"""
File:
    resolver.py

Version:
    1.0.0

Phase:
    3

Status:
    IMPLEMENTING

Purpose:
    Resolve raw company names into canonical company names.

Responsibilities:
    - Orchestrate normalization and alias resolution
    - Normalize raw company name using Normalizer
    - Resolve aliases using CompanyAliases
    - Return canonical company name

Dependencies:
    - jobs.identity.normalizer: Normalizer
    - jobs.identity.aliases: CompanyAliases

This module does NOT:
    - Use fuzzy matching
    - Use regex
    - Use validation
    - Use logging
    - Use database
    - Use API
    - Use Playwright
    - Use exporter

PEP8:     Yes
SOLID:    Yes (Single Responsibility)
DRY:      Yes
KISS:     Yes
"""

from __future__ import annotations

from jobs.identity.aliases import CompanyAliases
from jobs.identity.normalizer import Normalizer


class CompanyResolver:
    """
    Resolves raw company names to canonical company names.

    Orchestrates normalization followed by alias resolution.

    Methods:
        resolve: Normalize and resolve company name.

    Examples:
        >>> resolver = CompanyResolver()
        >>> resolver.resolve("Google India Pvt Ltd")
        "google"
        >>> resolver.resolve("Alphabet Inc")
        "google"
        >>> resolver.resolve("TCS")
        "tata consultancy services"
    """

    def __init__(self) -> None:
        """
        Initialize CompanyResolver with Normalizer and CompanyAliases.
        """
        self._normalizer: Normalizer = Normalizer()
        self._aliases: CompanyAliases = CompanyAliases()

    def resolve(self, company: str | None) -> str:
        """
        Resolve raw company name to canonical company name.

        Steps:
        1. Normalize company name (lowercase, remove suffixes, etc.)
        2. Resolve aliases to canonical name
        3. Return canonical name

        Args:
            company: Raw company name.

        Returns:
            str: Canonical company name.

        Examples:
            >>> resolver = CompanyResolver()
            >>> resolver.resolve("Google India Pvt Ltd")
            "google"
            >>> resolver.resolve("Alphabet Inc")
            "google"
            >>> resolver.resolve("TCS")
            "tata consultancy services"
            >>> resolver.resolve("Unknown Company Pvt Ltd")
            "unknown company"
        """
        if not company:
            return ""

        # Step 1: Normalize
        normalized: str = self._normalizer.normalize_company(company)

        if not normalized:
            return ""

        # Step 2: Resolve aliases
        canonical: str = self._aliases.resolve(normalized)

        return canonical


# =============================================================================
# END OF FILE
# =============================================================================