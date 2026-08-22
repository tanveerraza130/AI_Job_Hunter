"""
Profile configuration loader for AI Job Hunter.

Generic loader for all profile-related YAML files.

Architecture:
    Profile
        ↓
    Profile-owned YAML configuration
        ↓
    Generic application components

No profile-specific business rules or scoring defaults are defined here.
Missing required configuration is returned as an empty mapping so the
consumer can raise a precise, profile-specific validation error.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

import yaml

from jobs.profiles.profile import Profile
from jobs.version import AI_PIPELINE_VERSION

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Generic configuration loader for profile-related YAML files.

    All profile-specific configuration must live inside:

        jobs/profiles/{profile_type}/

    Core application code must not contain profile-specific defaults.
    """

    PROFILES_PATH = Path(__file__).parent
    VERSION = AI_PIPELINE_VERSION

    @classmethod
    def load(
        cls,
        profile_type: str,
        section: Optional[str] = None,
        file: Optional[str] = None,
        default: Any = None,
    ) -> dict[str, Any]:
        """
        Load a YAML configuration file.

        Args:
            profile_type: Profile identifier.
            section: Optional profile section directory.
            file: Optional YAML filename.
            default: Value returned when the file does not exist.

        Returns:
            Loaded YAML mapping, or default when the file is absent.

        Raises:
            ValueError: If YAML cannot be parsed or does not contain a mapping.
        """
        if not profile_type or not profile_type.strip():
            raise ValueError("profile_type is required.")

        if file is None:
            file = f"{profile_type}.yaml"

        path = cls.PROFILES_PATH / profile_type

        if section:
            path = path / section

        path = path / file

        if not path.exists():
            if default is not None:
                return default
            return {}

        try:
            with path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle)

        except yaml.YAMLError as exc:
            raise ValueError(
                f"Invalid YAML configuration: {path}"
            ) from exc

        except OSError as exc:
            raise ValueError(
                f"Unable to read configuration: {path}"
            ) from exc

        if data is None:
            return {}

        if not isinstance(data, dict):
            raise ValueError(
                f"Configuration must be a YAML mapping: {path}"
            )

        return data

    @classmethod
    def load_profile(cls, profile_type: str) -> Profile:
        """Load the profile YAML and return a Profile instance."""
        data = cls.load(
            profile_type,
            file=f"{profile_type}.yaml",
        )

        if not data:
            raise ValueError(
                f"Profile '{profile_type}' configuration was not found or is empty."
            )

        return Profile.from_dict(data)

    @classmethod
    def load_categories(cls, profile_type: str) -> dict[str, Any]:
        """
        Load profile-owned intelligence category mappings.

        Required file:

            jobs/profiles/{profile_type}/intelligence/categories.yaml
        """
        data = cls.load(
            profile_type,
            section="intelligence",
            file="categories.yaml",
        )

        categories = data.get("categories")

        if not isinstance(categories, dict) or not categories:
            raise ValueError(
                f"Profile '{profile_type}' must define intelligence "
                f"category mappings in "
                f"{cls.PROFILES_PATH / profile_type / 'intelligence' / 'categories.yaml'}"
            )

        return categories

    @classmethod
    def load_scoring_weights(
        cls,
        profile_type: str,
    ) -> dict[str, Any]:
        """
        Load profile-owned scoring configuration.

        There are intentionally NO scoring defaults here.
        """
        data = cls.load(
            profile_type,
            section="scoring",
            file="weights.yaml",
        )

        if not data:
            raise ValueError(
                f"Profile '{profile_type}' is missing scoring/weights.yaml."
            )

        return data

    @classmethod
    def load_matching_rules(
        cls,
        profile_type: str,
    ) -> dict[str, Any]:
        """
        Load optional profile-owned matching rules.

        Missing matching.yaml means no additional matching rules.
        """
        return cls.load(
            profile_type,
            section="scoring",
            file="matching.yaml",
            default={},
        )

    @classmethod
    def load_bonus_rules(
        cls,
        profile_type: str,
    ) -> dict[str, Any]:
        """
        Load optional profile-owned bonus rules.

        Missing bonus.yaml means no bonus rules.
        """
        return cls.load(
            profile_type,
            section="scoring",
            file="bonus.yaml",
            default={},
        )

    @classmethod
    def load_llm_config(
        cls,
        profile_type: str,
    ) -> dict[str, Any]:
        """
        Load optional profile-owned LLM configuration.

        No provider, model, or behavior is hard-coded here.
        """
        return cls.load(
            profile_type,
            section="scoring",
            file="llm.yaml",
            default={},
        )


# Backward-compatible alias.
ProfileLoader = ConfigLoader


def load_profile(profile_type: str) -> Profile:
    """Load a profile."""
    return ConfigLoader.load_profile(profile_type)


def load_categories(profile_type: str) -> dict[str, Any]:
    """Load profile intelligence categories."""
    return ConfigLoader.load_categories(profile_type)


def load_scoring_weights(profile_type: str) -> dict[str, Any]:
    """Load profile scoring configuration."""
    return ConfigLoader.load_scoring_weights(profile_type)


def load_matching_rules(profile_type: str) -> dict[str, Any]:
    """Load profile matching rules."""
    return ConfigLoader.load_matching_rules(profile_type)


def load_bonus_rules(profile_type: str) -> dict[str, Any]:
    """Load profile bonus rules."""
    return ConfigLoader.load_bonus_rules(profile_type)


def load_llm_config(profile_type: str) -> dict[str, Any]:
    """Load profile LLM configuration."""
    return ConfigLoader.load_llm_config(profile_type)


# =============================================================================
# END OF FILE
# =============================================================================