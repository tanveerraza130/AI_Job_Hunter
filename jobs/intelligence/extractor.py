"""
Rule-based intelligence extractor for AI Job Hunter.

Extracts structured intelligence from job descriptions using profile-owned
YAML dictionaries.

Architecture:

    profile_type
        ↓
    jobs/profiles/{profile_type}/
        ├── intelligence/categories.yaml
        └── dictionaries/*.yaml
        ↓
    JobIntelligence

No profile-specific taxonomy, category names, or scoring rules are defined
inside this module.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

import yaml

from jobs.intelligence.models import JobIntelligence, WeightedItem

logger = logging.getLogger(__name__)


class IntelligenceExtractor:
    """
    Profile-driven rule-based intelligence extractor.

    Every profile owns its own:
        - category mappings
        - dictionaries
        - aliases
        - taxonomy

    The extractor itself contains no CRM-specific knowledge.
    """

    def __init__(self, profile_type: str) -> None:
        """
        Initialize the extractor for a required profile.

        Args:
            profile_type: Profile identifier.

        Raises:
            ValueError: If profile_type is missing or required configuration
                        is unavailable.
        """
        if not profile_type or not profile_type.strip():
            raise ValueError(
                "profile_type is required for IntelligenceExtractor."
            )

        self.profile_type = profile_type.strip()

        self.profile_path = (
            Path(__file__).parent.parent
            / "profiles"
            / self.profile_type
        )

        self.dictionaries_path = self.profile_path / "dictionaries"

        if not self.profile_path.exists():
            raise ValueError(
                f"Profile directory does not exist: {self.profile_path}"
            )

        if not self.dictionaries_path.exists():
            raise ValueError(
                f"Profile dictionary directory does not exist: "
                f"{self.dictionaries_path}"
            )

        self.category_mappings = self._load_categories()

        self._category_alias_maps: dict[str, dict[str, str]] = {}
        self._canonical_items: dict[
            str,
            list[tuple[str, list[str]]],
        ] = {}

        self._load_dictionaries()

        if not self._canonical_items:
            raise ValueError(
                f"Profile '{self.profile_type}' has no taxonomy dictionaries "
                f"in {self.dictionaries_path}"
            )

    def _load_categories(self) -> dict[str, str]:
        """
        Load category mappings exclusively from the active profile.

        Required file:

            profiles/{profile}/intelligence/categories.yaml
        """
        categories_path = (
            self.profile_path
            / "intelligence"
            / "categories.yaml"
        )

        if not categories_path.exists():
            raise ValueError(
                f"Profile '{self.profile_type}' is missing required "
                f"categories configuration: {categories_path}"
            )

        try:
            with categories_path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}

        except yaml.YAMLError as exc:
            raise ValueError(
                f"Invalid categories YAML: {categories_path}"
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                f"Categories configuration must be a mapping: "
                f"{categories_path}"
            )

        categories = data.get("categories")

        if not isinstance(categories, dict) or not categories:
            raise ValueError(
                f"Profile '{self.profile_type}' must define a non-empty "
                f"'categories' mapping in {categories_path}"
            )

        normalized: dict[str, str] = {}

        for key, value in categories.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError(
                    f"Invalid category mapping in {categories_path}: "
                    f"{key!r}: {value!r}"
                )

            normalized[key.strip()] = value.strip()

        return normalized

    def _load_dictionaries(self) -> None:
        """
        Load every YAML dictionary owned by the active profile.

        The YAML category name is authoritative.
        """
        dictionary_files = sorted(
            self.dictionaries_path.glob("*.yaml")
        )

        if not dictionary_files:
            raise ValueError(
                f"No YAML dictionaries found in {self.dictionaries_path}"
            )

        for filepath in dictionary_files:
            try:
                with filepath.open(
                    "r",
                    encoding="utf-8",
                ) as handle:
                    data = yaml.safe_load(handle) or {}

            except yaml.YAMLError as exc:
                raise ValueError(
                    f"Invalid dictionary YAML: {filepath}"
                ) from exc

            if not isinstance(data, dict):
                raise ValueError(
                    f"Dictionary must contain a mapping: {filepath}"
                )

            category = data.get("category", {})
            category_name = (
                category.get("name")
                if isinstance(category, dict)
                else None
            )

            if not category_name:
                category_name = filepath.stem

            items = data.get("items", [])

            if not isinstance(items, list):
                raise ValueError(
                    f"'items' must be a list in dictionary: {filepath}"
                )

            parsed_items: list[tuple[str, list[str]]] = []
            alias_map: dict[str, str] = {}

            for item in items:
                if not isinstance(item, dict):
                    continue

                name = str(item.get("name", "")).strip()

                if not name:
                    continue

                aliases = item.get("aliases", [])

                if aliases is None:
                    aliases = []

                if not isinstance(aliases, list):
                    raise ValueError(
                        f"Aliases must be a list for '{name}' "
                        f"in {filepath}"
                    )

                cleaned_aliases = [
                    str(alias).strip()
                    for alias in aliases
                    if str(alias).strip()
                ]

                parsed_items.append(
                    (name, cleaned_aliases)
                )

                alias_map[name.lower()] = name

                for alias in cleaned_aliases:
                    alias_map[alias.lower()] = name

            self._canonical_items[category_name] = parsed_items
            self._category_alias_maps[category_name] = alias_map

            logger.debug(
                "Loaded profile dictionary: profile=%s file=%s "
                "category=%s items=%d",
                self.profile_type,
                filepath.name,
                category_name,
                len(parsed_items),
            )

    def _get_alias_map(
        self,
        category_name: str,
    ) -> dict[str, str]:
        """Return aliases for a profile-owned category."""
        return self._category_alias_maps.get(category_name, {})

    def _normalize_text(self, text: str) -> str:
        """Normalize text for deterministic matching."""
        if not text:
            return ""

        normalized = text.lower()
        normalized = re.sub(
            r"[^\w\s'-]",
            " ",
            normalized,
        )
        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        )

        return normalized.strip()

    def _extract_weighted_keywords_with_aliases(
        self,
        text: str,
        alias_map: dict[str, str],
    ) -> list[WeightedItem]:
        """
        Extract profile taxonomy terms and aliases from normalized text.
        """
        if not text or not alias_map:
            return []

        found: dict[str, int] = {}

        for term, canonical_name in alias_map.items():
            if not term:
                continue

            pattern = re.compile(
                r"\b" + re.escape(term) + r"\b"
            )

            matches = pattern.findall(text)

            if matches:
                found[canonical_name] = (
                    found.get(canonical_name, 0)
                    + len(matches)
                )

        return sorted(
            [
                WeightedItem(
                    name=name,
                    count=count,
                )
                for name, count in found.items()
            ],
            key=lambda item: (
                -item.count,
                item.name,
            ),
        )

    def _extract_experience(
        self,
        text: str,
    ) -> tuple[Optional[int], Optional[int]]:
        """Extract experience metadata."""
        if not text:
            return None, None

        text_lower = text.lower()

        if re.search(
            r"\b(fresher|entry level|0 years|0-1 years)\b",
            text_lower,
        ):
            return 0, 1

        range_match = re.search(
            r"(\d+)\s*(?:-|to)\s*(\d+)\s*(?:years?|yrs?)",
            text_lower,
        )

        if range_match:
            return (
                int(range_match.group(1)),
                int(range_match.group(2)),
            )

        plus_match = re.search(
            r"(\d+)\+\s*(?:years?|yrs?)",
            text_lower,
        )

        if plus_match:
            return int(plus_match.group(1)), None

        min_match = re.search(
            r"(?:minimum|min)\s*(\d+)\s*(?:years?|yrs?)",
            text_lower,
        )

        if min_match:
            return int(min_match.group(1)), None

        single_match = re.search(
            r"(\d+)\s*(?:years?|yrs?)",
            text_lower,
        )

        if single_match:
            value = int(single_match.group(1))
            return value, value

        return None, None

    def _extract_salary(
        self,
        text: str,
    ) -> tuple[
        Optional[float],
        Optional[float],
        Optional[str],
    ]:
        """Extract salary metadata."""
        if not text:
            return None, None, None

        currency_map = {
            "₹": "INR",
            "$": "USD",
            "€": "EUR",
            "£": "GBP",
        }

        currency = next(
            (
                code
                for symbol, code in currency_map.items()
                if symbol in text
            ),
            None,
        )

        cleaned = re.sub(
            r"[₹$€£]",
            "",
            text,
        ).strip()

        numbers = re.findall(
            r"(\d+\.?\d*)",
            cleaned,
        )

        if not numbers:
            return None, None, currency

        values = [float(number) for number in numbers]

        multiplier = (
            100000
            if (
                "lpa" in cleaned.lower()
                or "lakh" in cleaned.lower()
            )
            else 1
        )

        if len(values) == 1:
            return (
                values[0] * multiplier,
                None,
                currency,
            )

        return (
            values[0] * multiplier,
            values[1] * multiplier,
            currency,
        )

    def extract(
        self,
        title: str,
        description: str,
        salary_min: Optional[float] = None,
        salary_max: Optional[float] = None,
        salary_currency: Optional[str] = None,
        experience_min: Optional[int] = None,
        experience_max: Optional[int] = None,
    ) -> JobIntelligence:
        """
        Extract intelligence from a job.

        Salary and experience are extracted as metadata only.
        They are not scoring components.
        """
        raw_text = (
            f"{title or ''} "
            f"{description or ''}"
        )

        normalized_text = self._normalize_text(raw_text)

        categories: dict[str, list[WeightedItem]] = {}

        for category_name, alias_map in (
            self._category_alias_maps.items()
        ):
            weighted = (
                self._extract_weighted_keywords_with_aliases(
                    normalized_text,
                    alias_map,
                )
            )

            if weighted:
                categories[category_name] = weighted

        if (
            salary_min is not None
            or salary_max is not None
        ):
            final_salary_min = salary_min
            final_salary_max = salary_max
            final_salary_currency = salary_currency
        else:
            (
                final_salary_min,
                final_salary_max,
                final_salary_currency,
            ) = self._extract_salary(raw_text)

        if (
            experience_min is not None
            or experience_max is not None
        ):
            final_experience_min = experience_min
            final_experience_max = experience_max
        else:
            (
                final_experience_min,
                final_experience_max,
            ) = self._extract_experience(raw_text)

        return JobIntelligence(
            categories=categories,
            experience_min=final_experience_min,
            experience_max=final_experience_max,
            salary_min=final_salary_min,
            salary_max=final_salary_max,
            salary_currency=final_salary_currency,
        )

    def extract_from_job(self, job) -> JobIntelligence:
        """Extract intelligence from a Job object."""
        return self.extract(
            title=job.title or "",
            description=job.description or "",
            salary_min=getattr(
                job,
                "salary_min",
                None,
            ),
            salary_max=getattr(
                job,
                "salary_max",
                None,
            ),
            salary_currency=getattr(
                job,
                "salary_currency",
                None,
            ),
            experience_min=getattr(
                job,
                "experience_min",
                None,
            ),
            experience_max=getattr(
                job,
                "experience_max",
                None,
            ),
        )

    def extract_many(
        self,
        jobs: list,
    ) -> list[JobIntelligence]:
        """Extract intelligence from multiple jobs."""
        return [
            self.extract_from_job(job)
            for job in jobs
        ]


# =============================================================================
# END OF FILE
# =============================================================================