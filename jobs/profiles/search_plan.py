"""
Search plan builder for AI Job Hunter.

Generates a list of SearchRequest objects for multiple locations.
"""

from __future__ import annotations

from jobs.profiles.profile import Profile
from jobs.profiles.request_builder import build_search_requests
from jobs.search import SearchRequest


def build_search_plan(
    profile: Profile,
    locations: list[str],
) -> list[SearchRequest]:
    """
    Build a search plan from a profile and multiple locations.

    Args:
        profile: Profile object containing search_keywords.
        locations: List of locations to search.

    Returns:
        list[SearchRequest]: One SearchRequest per keyword per location.

    Raises:
        ValueError: If no valid locations remain after stripping.
    """
    valid_locations: list[str] = []

    for location in locations:
        cleaned = location.strip()
        if cleaned:
            valid_locations.append(cleaned)

    if not valid_locations:
        raise ValueError("At least one location is required.")

    all_requests: list[SearchRequest] = []

    for location in valid_locations:
        all_requests.extend(
            build_search_requests(profile, location)
        )

    return all_requests


# =============================================================================
# END OF FILE
# =============================================================================