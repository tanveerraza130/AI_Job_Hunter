"""
File:
    normalizer.py

Version:
    3.0.0

Phase:
    3

Status:
    FROZEN

Purpose:
    Deterministic normalization of raw values from job portals.

Responsibilities:
    - Normalize company names (lowercase, remove legal suffixes, collapse spaces)
    - Normalize locations (deterministic mapping)
    - Normalize work modes (REMOTE, HYBRID, ONSITE)
    - Normalize employment types (FULL_TIME, CONTRACT, etc.)
    - Normalize skills (lowercase, deduplicate, sort)
    - Normalize salary formatting

Dependencies:
    - jobs.identity.constants: COMPANY_SUFFIXES, LOCATION_MAP, WORK_MODE_MAP, EMPLOYMENT_TYPE_MAP
    - re: Compiled regex patterns

This module does NOT:
    - Use fuzzy matching
    - Use AI
    - Use alias resolution
    - Validate
    - Deduplicate
    - Use database
    - Use exporter
    - Use logging
    - Use Playwright

PEP8:     Yes
SOLID:    Yes (Single Responsibility)
DRY:      Yes
KISS:     Yes
"""

from __future__ import annotations

import re

from jobs.identity.constants import (
    COMPANY_SUFFIXES,
    EMPLOYMENT_TYPE_MAP,
    LOCATION_MAP,
    WORK_MODE_MAP,
)

# ------------------------------------------------------------------
# Compiled Regex Patterns
# ------------------------------------------------------------------

SPACE_REGEX = re.compile(r"\s+")
PUNCTUATION_REGEX = re.compile(r"[^\w\s]")
HYPHEN_REGEX = re.compile(r"(\d)-(\d)")
CURRENCY_SPACE_REGEX = re.compile(r"([₹$€£])\s+(\d)")


class Normalizer:
    """
    Deterministic normalizer for job data.

    Methods:
        normalize_company: Normalize company name
        normalize_location: Normalize location
        normalize_work_mode: Normalize work mode
        normalize_employment_type: Normalize employment type
        normalize_skills: Normalize skills (str | list[str] | None)
        normalize_salary: Normalize salary text
    """

    def _clean_text(self, text: str) -> str:
        """
        Clean text: lowercase, strip, collapse spaces.

        Args:
            text: Input text.

        Returns:
            str: Cleaned text.
        """
        if not text:
            return ""

        cleaned: str = text.lower().strip()
        cleaned = SPACE_REGEX.sub(" ", cleaned)
        return cleaned

    def _remove_suffixes(self, text: str, suffixes: list[str]) -> str:
        """
        Remove common suffixes from text.

        Args:
            text: Input text.
            suffixes: List of suffixes to remove.

        Returns:
            str: Text with suffixes removed.
        """
        if not text:
            return ""

        words: list[str] = text.split()

        # Remove suffix words from the end
        while words and words[-1] in suffixes:
            words.pop()

        return " ".join(words)

    def normalize_company(self, company: str | None) -> str:
        """
        Normalize company name.

        Steps:
        1. Clean text (lowercase, trim, collapse spaces)
        2. Remove punctuation
        3. Collapse spaces
        4. Remove legal suffixes only (Pvt, Ltd, Inc, etc.)
        5. Final strip

        Args:
            company: Raw company name.

        Returns:
            str: Normalized company name.

        Examples:
            >>> normalizer = Normalizer()
            >>> normalizer.normalize_company("Google India Pvt Ltd")
            "google"
            >>> normalizer.normalize_company("Microsoft Corporation")
            "microsoft"
            >>> normalizer.normalize_company("Tech Mahindra")
            "tech mahindra"
        """
        if not company:
            return ""

        # Clean text
        cleaned: str = self._clean_text(company)

        # Remove punctuation
        cleaned = PUNCTUATION_REGEX.sub(" ", cleaned)

        # Collapse spaces
        cleaned = SPACE_REGEX.sub(" ", cleaned).strip()

        # Remove legal suffixes only
        cleaned = self._remove_suffixes(cleaned, COMPANY_SUFFIXES)

        # Final strip
        cleaned = cleaned.strip()

        return cleaned

    def normalize_location(self, location: str | None) -> str:
        """
        Normalize location using deterministic mapping.

        Steps:
        1. Lowercase
        2. Trim spaces
        3. Lookup in location map
        4. Return canonical name

        Args:
            location: Raw location name.

        Returns:
            str: Normalized location.

        Examples:
            >>> normalizer = Normalizer()
            >>> normalizer.normalize_location("Bangalore")
            "BENGALURU"
            >>> normalizer.normalize_location("Bombay")
            "MUMBAI"
        """
        if not location:
            return ""

        cleaned: str = self._clean_text(location)

        # Lookup in location map
        normalized: str = LOCATION_MAP.get(cleaned, cleaned)

        return normalized.upper()

    def normalize_work_mode(self, work_mode: str | None) -> str:
        """
        Normalize work mode.

        Steps:
        1. Lowercase
        2. Trim spaces
        3. Lookup in work mode map
        4. Return canonical value

        Args:
            work_mode: Raw work mode.

        Returns:
            str: Normalized work mode (REMOTE, HYBRID, ONSITE).

        Examples:
            >>> normalizer = Normalizer()
            >>> normalizer.normalize_work_mode("WFH")
            "REMOTE"
            >>> normalizer.normalize_work_mode("Hybrid")
            "HYBRID"
        """
        if not work_mode:
            return ""

        cleaned: str = self._clean_text(work_mode)

        # Lookup in work mode map
        normalized: str = WORK_MODE_MAP.get(cleaned, cleaned)

        return normalized.upper()

    def normalize_employment_type(self, employment_type: str | None) -> str:
        """
        Normalize employment type.

        Steps:
        1. Lowercase
        2. Trim spaces
        3. Lookup in employment type map
        4. Return canonical value

        Args:
            employment_type: Raw employment type.

        Returns:
            str: Normalized employment type.

        Examples:
            >>> normalizer = Normalizer()
            >>> normalizer.normalize_employment_type("Permanent")
            "FULL_TIME"
            >>> normalizer.normalize_employment_type("Contract")
            "CONTRACT"
        """
        if not employment_type:
            return ""

        cleaned: str = self._clean_text(employment_type)

        # Lookup in employment type map
        normalized: str = EMPLOYMENT_TYPE_MAP.get(cleaned, cleaned)

        return normalized.upper()

    def normalize_skills(self, skills: str | list[str] | None) -> list[str]:
        """
        Normalize skills.

        Supports both string (comma-separated) and list input.

        Steps:
        1. Parse input (str or list)
        2. Lowercase each skill
        3. Trim spaces
        4. Remove duplicates using set
        5. Sort alphabetically

        Args:
            skills: Raw skills (comma-separated string, list, or None).

        Returns:
            list[str]: Normalized, deduplicated, sorted skills.

        Examples:
            >>> normalizer = Normalizer()
            >>> normalizer.normalize_skills(["Python", "SQL ", "AWS", "Python"])
            ["aws", "python", "sql"]
            >>> normalizer.normalize_skills("Python, SQL, AWS")
            ["aws", "python", "sql"]
        """
        if not skills:
            return []

        # Parse input
        raw_skills: list[str] = []

        if isinstance(skills, str):
            # Split by comma, handle empty
            raw_skills = [s.strip() for s in skills.split(",") if s.strip()]
        elif isinstance(skills, list):
            raw_skills = [s.strip() for s in skills if s and s.strip()]
        else:
            return []

        if not raw_skills:
            return []

        # Normalize: lowercase, deduplicate using set, sort
        skill_set: set[str] = set()

        for skill in raw_skills:
            cleaned: str = skill.lower().strip()
            if cleaned:
                skill_set.add(cleaned)

        return sorted(skill_set)

    def normalize_salary(self, salary_text: str | None) -> str:
        """
        Normalize salary text formatting only.

        Does NOT parse ranges or convert currency.

        Steps:
        1. Strip spaces
        2. Collapse multiple spaces
        3. Remove extra spaces around symbols

        Args:
            salary_text: Raw salary text.

        Returns:
            str: Normalized salary text.

        Examples:
            >>> normalizer = Normalizer()
            >>> normalizer.normalize_salary("₹ 20 LPA")
            "₹20 LPA"
            >>> normalizer.normalize_salary("20-25 LPA")
            "20 - 25 LPA"
        """
        if not salary_text:
            return ""

        # Clean text: strip and collapse spaces
        cleaned: str = SPACE_REGEX.sub(" ", salary_text.strip())

        # Add space around hyphen for ranges
        cleaned = HYPHEN_REGEX.sub(r"\1 - \2", cleaned)

        # Remove space between currency symbol and number
        cleaned = CURRENCY_SPACE_REGEX.sub(r"\1\2", cleaned)

        return cleaned


# =============================================================================
# END OF FILE
# =============================================================================