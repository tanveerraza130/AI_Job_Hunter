"""
Search request builder for AI Job Hunter.

Generates SearchRequest objects from profile keywords.
"""

from __future__ import annotations

from jobs.profiles.profile import Profile
from jobs.profiles.search_keywords import build_search_keywords
from jobs.search import SearchRequest


def build_search_requests(
    profile: Profile,
    location: str,
) -> list[SearchRequest]:
    """
    Build SearchRequest objects from a profile.

    Args:
        profile: Profile object containing search_keywords.
        location: Location to use for all SearchRequests.

    Returns:
        list[SearchRequest]: One SearchRequest per keyword.

    Raises:
        ValueError: If location is empty after stripping.
    """
    cleaned_location = location.strip()

    if not cleaned_location:
        raise ValueError("Location cannot be empty.")

    keywords = build_search_keywords(profile)

    return [
        SearchRequest(
            keyword=keyword,
            location=cleaned_location,
        )
        for keyword in keywords
    ]


# =============================================================================
# END OF FILE
# =============================================================================