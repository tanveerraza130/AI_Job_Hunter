"""
Search keyword builder for AI Job Hunter.

Builds discovery keywords from profile configuration.
"""

from __future__ import annotations

from jobs.profiles.profile import Profile


def build_search_keywords(profile: Profile) -> list[str]:
    """
    Build unique job discovery keywords from profile.search_keywords only.

    Excludes:
    - Values configured in profile.search_exclude.

    Tools and skills must not generate discovery searches.
    """

    seen: set[str] = set()
    result: list[str] = []

    excluded = {
        value.strip().casefold()
        for value in profile.search_exclude
        if value.strip()
    }

    def add_keyword(keyword: str) -> None:
        cleaned = keyword.strip()

        if not cleaned:
            return

        key = cleaned.casefold()

        if key in excluded:
            return

        if key in seen:
            return

        seen.add(key)
        result.append(cleaned)

    for keyword in profile.search_keywords:
        add_keyword(keyword)

    return result
