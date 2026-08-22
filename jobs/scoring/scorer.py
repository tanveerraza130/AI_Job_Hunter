"""
File:
    search.py

Version:
    2.1.0

Phase:
    8

Status:
    FROZEN

Purpose:
    Define search request data structure.

Responsibilities:
    - Store search keyword and location
    - Store optional filter fields (experience, salary, remote, employment_type)
    - Provide a simple dataclass for search configuration

Dependencies:
    - dataclasses: dataclass

This module does NOT:
    - Perform any filtering logic
    - Validate search parameters
    - Handle enums
    - Interact with connectors

PEP8:     Yes
SOLID:    Yes (Single Responsibility)
DRY:      Yes
KISS:     Yes
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SearchRequest:
    """
    Search request for job listings.

    Attributes:
        keyword: Primary search keyword (e.g., "python developer").
        location: Location filter (e.g., "bangalore", "remote").
        experience_min: Minimum years of experience (optional).
        experience_max: Maximum years of experience (optional).
        salary_min: Minimum annual salary in local currency (optional).
        salary_max: Maximum annual salary in local currency (optional).
        remote: Filter for remote jobs (optional, True = remote only).
        employment_type: Employment type (e.g., "FULL_TIME", "CONTRACT") (optional).
    """
    keyword: str
    location: str
    experience_min: int | None = None
    experience_max: int | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    remote: bool | None = None
    employment_type: str | None = None


# =============================================================================
# END OF FILE
# =============================================================================