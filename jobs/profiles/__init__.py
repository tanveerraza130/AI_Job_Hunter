"""
Job profile definitions for AI Job Hunter.

Profiles define search configurations for specific job roles.
"""

from __future__ import annotations

from jobs.profiles.profile import Profile
from jobs.profiles.loader import load_profile
from jobs.profiles.search_keywords import build_search_keywords
from jobs.profiles.request_builder import build_search_requests
from jobs.profiles.search_plan import build_search_plan

__all__ = [
    "Profile",
    "load_profile",
    "build_search_keywords",
    "build_search_requests",
    "build_search_plan",
]


# =============================================================================
# END OF FILE
# =============================================================================