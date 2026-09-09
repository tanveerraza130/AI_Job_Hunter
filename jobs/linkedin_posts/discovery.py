"""
Discovery query helpers for publicly discoverable LinkedIn hiring posts.

This module is intentionally isolated from the existing Job pipeline.

It does not authenticate to LinkedIn, bypass access controls, use proxies,
solve CAPTCHAs, or scrape private/member-only content.
"""

from __future__ import annotations

from dataclasses import dataclass

from jobs.profiles.profile import Profile
from jobs.profiles.search_keywords import build_search_keywords


@dataclass(frozen=True, slots=True)
class LinkedInPostDiscoveryQuery:
    """One search-engine query used to discover public LinkedIn posts."""

    query: str
    profile_id: str
    keyword: str
    location: str


def build_discovery_queries(
    profile: Profile,
    locations: list[str] | None = None,
) -> list[LinkedInPostDiscoveryQuery]:
    """
    Build LinkedIn hiring-post discovery queries from an existing profile.

    The profile remains the source of truth for discovery keywords and
    search exclusions. LinkedIn-specific constraints are added here only.
    """
    effective_locations = locations or profile.locations
    keywords = build_search_keywords(profile)

    queries: list[LinkedInPostDiscoveryQuery] = []
    seen: set[str] = set()

    for location in effective_locations:
        clean_location = location.strip()

        if not clean_location:
            continue

        for keyword in keywords:
            clean_keyword = keyword.strip()

            if not clean_keyword:
                continue

            query = (
                f'site:linkedin.com/posts '
                f'"{clean_keyword}" '
                f'"{clean_location}" '
                f'(hiring OR "we are hiring" OR "we\'re hiring")'
            )

            normalized = query.casefold()

            if normalized in seen:
                continue

            seen.add(normalized)

            queries.append(
                LinkedInPostDiscoveryQuery(
                    query=query,
                    profile_id=profile.profile_id,
                    keyword=clean_keyword,
                    location=clean_location,
                )
            )

    return queries
