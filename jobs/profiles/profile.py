"""
Profile data models for AI Job Hunter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class ProfileSkills:
    """
    Skills dictionary for a job profile.

    Attributes:
        required: Skills required for the role.
        desired: Skills preferred but not required.
    """
    required: List[str] = field(default_factory=list)
    desired: List[str] = field(default_factory=list)


@dataclass
class Profile:
    """
    Job profile definition.

    Attributes:
        profile_id: Unique profile identifier.
        profile_name: Unique profile name.
        version: Schema version.
        enabled: Whether the profile is active.
        search_keywords: List of search keywords to use.
        skills: Skills dictionary for AI ranking.
        negative_titles: Titles to filter out.
        negative_keywords: Keywords in title/description to filter out.
        locations: Preferred locations.
        experience_min: Minimum years of experience.
        experience_max: Maximum years of experience.
        salary_min: Minimum salary expectation.
        salary_max: Maximum salary expectation.
        work_modes: Preferred work modes.
        tools: List of tools.
    """
    profile_id: str = ""
    profile_name: str = ""
    version: int = 1
    enabled: bool = True
    search_keywords: List[str] = field(default_factory=list)
    search_exclude: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    negative_titles: List[str] = field(default_factory=list)
    negative_keywords: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    work_modes: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Profile:
        """
        Create a Profile instance from a dictionary.

        Args:
            data: Dictionary containing profile data.

        Returns:
            Profile: The profile instance.
        """
        return cls(
            profile_id=data.get("profile_id", ""),
            profile_name=data.get("profile_name", ""),
            version=data.get("version", 1),
            enabled=data.get("enabled", True),
            search_keywords=data.get("search_keywords", []),
            search_exclude=data.get("search_exclude", []),
            skills=data.get("skills", []),
            negative_titles=data.get("negative_titles", []),
            negative_keywords=data.get("negative_keywords", []),
            locations=data.get("locations", []),
            experience_min=data.get("experience_min"),
            experience_max=data.get("experience_max"),
            salary_min=data.get("salary_min"),
            salary_max=data.get("salary_max"),
            work_modes=data.get("work_modes", []),
            tools=data.get("tools", []),
        )


# =============================================================================
# END OF FILE
# =============================================================================