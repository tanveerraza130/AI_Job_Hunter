
"""
Rule-based intelligence extractor for job descriptions.

Extracts structured data from job descriptions using keyword matching.
No AI/LLM dependency. Configurable via YAML dictionaries with aliases.

Profile-driven: uses the profile type from the loaded profile configuration.
Category mappings are loaded from intelligence/categories.yaml.

Phase 4.1: Extraction only. All scoring weights belong in Phase 4.2.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from jobs.intelligence.models import JobIntelligence, WeightedItem

logger = logging.getLogger(__name__)


class IntelligenceExtractor:
    """
    Rule-based extractor for job intelligence.

    The extractor is located inside:

        jobs/profiles/{profile}/intelligence/extractor.py

    Therefore:

        Path(__file__).parent.parent

    points directly to:

        jobs/profiles/{profile}
    """

    def __init__(
        self,
        profile_type: str = "crm_manager",
    ) -> None:
        """
        Initialize the extractor.

        Args:
            profile_type:
                Profile name, e.g. "crm_manager".
        """
        self.profile_type = profile_type

        # IMPORTANT:
        # extractor.py is already inside:
        #
        # jobs/profiles/{profile}/intelligence/
        #
        # Therefore parent.parent = profile directory.
        self.profile_path = (
            Path(__file__).parent.parent
        )

        self.dictionaries_path = (
            self.profile_path
            / "dictionaries"
        )

        self.category_mappings = (
            self._load_categories()
        )

        self._canonical_items: Dict[
            str,
            List[Tuple[str, List[str]]],
        ] = {}

        self._category_alias_maps: Dict[
            str,
            Dict[str, str],
        ] = {}

        self._load_dictionaries()

    # ------------------------------------------------------------------
    # CATEGORY LOADING
    # ------------------------------------------------------------------

    def _load_categories(self) -> Dict[str, str]:
        """
        Load category mappings from categories.yaml.
        """
        categories_path = (
            self.profile_path
            / "intelligence"
            / "categories.yaml"
        )

        default_mappings = {
            "skills": "crm_skills",
            "tools": "crm_platforms",
            "concepts": "crm_concepts",
            "channels": "communication_channels",
            "analytics": "analytics_tools",
            "bsps": "cpaas_providers",
        }

        if not categories_path.exists():
            logger.warning(
                "Categories file not found: %s",
                categories_path,
            )
            return default_mappings

        try:
            with categories_path.open(
                "r",
                encoding="utf-8",
            ) as handle:
                data = yaml.safe_load(handle) or {}

        except (
            OSError,
            yaml.YAMLError,
        ) as exc:
            logger.warning(
                "Failed to load categories %s: %s",
                categories_path,
                exc,
            )
            return default_mappings

        if not isinstance(data, dict):
            return default_mappings

        categories = data.get(
            "categories",
            default_mappings,
        )

        if not isinstance(categories, dict):
            return default_mappings

        normalized: Dict[str, str] = {}

        for key, value in categories.items():

            if not isinstance(key, str):
                continue

            if not isinstance(value, str):
                continue

            normalized[
                key.strip()
            ] = value.strip()

        return normalized or default_mappings

    # ------------------------------------------------------------------
    # DICTIONARY LOADING
    # ------------------------------------------------------------------

    def _load_dictionaries(self) -> None:
        """
        Load all profile-owned YAML dictionaries.

        Dictionary files are loaded from:

            jobs/profiles/{profile}/dictionaries/

        Duplicate aliases are handled deterministically.

        Longer phrases are preferred during extraction.
        """
        if not self.dictionaries_path.exists():
            raise ValueError(
                "Dictionary directory does not exist: "
                f"{self.dictionaries_path}"
            )

        dictionary_files = sorted(
            self.dictionaries_path.glob("*.yaml")
        )

        if not dictionary_files:
            raise ValueError(
                "No YAML dictionaries found in: "
                f"{self.dictionaries_path}"
            )

        for filepath in dictionary_files:

            try:
                with filepath.open(
                    "r",
                    encoding="utf-8",
                ) as handle:
                    data = yaml.safe_load(
                        handle
                    ) or {}

            except (
                OSError,
                yaml.YAMLError,
            ) as exc:
                raise ValueError(
                    f"Failed to load dictionary: {filepath}"
                ) from exc

            if not isinstance(data, dict):
                raise ValueError(
                    f"Dictionary must contain a mapping: "
                    f"{filepath}"
                )

            category = data.get(
                "category",
                {},
            )

            if isinstance(category, dict):
                category_name = category.get(
                    "name"
                )
            else:
                category_name = None

            if not category_name:
                category_name = filepath.stem

            category_name = str(
                category_name
            ).strip()

            items = data.get(
                "items",
                [],
            )

            if not isinstance(items, list):
                raise ValueError(
                    f"'items' must be a list in: "
                    f"{filepath}"
                )

            parsed_items: List[
                Tuple[str, List[str]]
            ] = []

            alias_map: Dict[str, str] = {}

            for item in items:

                if not isinstance(item, dict):
                    continue

                name = str(
                    item.get(
                        "name",
                        "",
                    )
                ).strip()

                if not name:
                    continue

                aliases = item.get(
                    "aliases",
                    [],
                )

                if aliases is None:
                    aliases = []

                if not isinstance(
                    aliases,
                    list,
                ):
                    raise ValueError(
                        f"Aliases must be a list for "
                        f"'{name}' in {filepath}"
                    )

                cleaned_aliases: List[str] = []

                for alias in aliases:

                    alias_text = str(
                        alias
                    ).strip()

                    if alias_text:
                        cleaned_aliases.append(
                            alias_text
                        )

                parsed_items.append(
                    (
                        name,
                        cleaned_aliases,
                    )
                )

                # Canonical name.
                canonical_key = (
                    name.lower()
                )

                if canonical_key not in alias_map:
                    alias_map[
                        canonical_key
                    ] = name

                # Aliases.
                #
                # First definition wins.
                for alias in cleaned_aliases:

                    alias_key = (
                        alias.lower()
                    )

                    if alias_key not in alias_map:
                        alias_map[
                            alias_key
                        ] = name

                    elif (
                        alias_map[alias_key]
                        != name
                    ):
                        logger.debug(
                            "Duplicate alias ignored: "
                            "category=%s alias=%r "
                            "existing=%r new=%r",
                            category_name,
                            alias_key,
                            alias_map[
                                alias_key
                            ],
                            name,
                        )

            self._canonical_items[
                category_name
            ] = parsed_items

            self._category_alias_maps[
                category_name
            ] = alias_map

            logger.info(
                "Loaded dictionary: "
                "category=%s items=%d aliases=%d",
                category_name,
                len(parsed_items),
                len(alias_map),
            )

    # ------------------------------------------------------------------
    # ACCESSORS
    # ------------------------------------------------------------------

    def _get_alias_map(
        self,
        category_name: str,
    ) -> Dict[str, str]:
        """
        Return aliases for a category.
        """
        return self._category_alias_maps.get(
            category_name,
            {},
        )

    # ------------------------------------------------------------------
    # TEXT NORMALIZATION
    # ------------------------------------------------------------------

    def _normalize_text(
        self,
        text: str,
    ) -> str:
        """
        Normalize text for deterministic matching.
        """
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

    # ------------------------------------------------------------------
    # TAXONOMY MATCHING
    # ------------------------------------------------------------------

    def _extract_weighted_keywords_with_aliases(
        self,
        text: str,
        alias_map: Dict[str, str],
    ) -> List[WeightedItem]:
        """
        Extract taxonomy terms using longest-match-first.

        Example:

            marketing automation

        is preferred over:

            automation

        when both are present in the taxonomy.
        """
        if not text or not alias_map:
            return []

        found: Dict[str, int] = {}

        # Longer phrases first.
        sorted_terms = sorted(
            alias_map.items(),
            key=lambda item: (
                -len(item[0].split()),
                -len(item[0]),
                item[0],
            ),
        )

        occupied_ranges: List[
            Tuple[int, int]
        ] = []

        def overlaps(
            start: int,
            end: int,
        ) -> bool:
            """
            Check whether a candidate match overlaps
            an already accepted match.
            """
            for (
                existing_start,
                existing_end,
            ) in occupied_ranges:

                if (
                    start < existing_end
                    and end > existing_start
                ):
                    return True

            return False

        for term, canonical_name in sorted_terms:

            if not term:
                continue

            pattern = re.compile(
                r"\b"
                + re.escape(term)
                + r"\b"
            )

            for match in pattern.finditer(
                text
            ):

                start = match.start()
                end = match.end()

                if overlaps(
                    start,
                    end,
                ):
                    continue

                occupied_ranges.append(
                    (
                        start,
                        end,
                    )
                )

                found[
                    canonical_name
                ] = (
                    found.get(
                        canonical_name,
                        0,
                    )
                    + 1
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

    # ------------------------------------------------------------------
    # EXPERIENCE
    # ------------------------------------------------------------------

    def _extract_experience(
        self,
        text: str,
    ) -> Tuple[
        Optional[int],
        Optional[int],
    ]:
        """
        Extract minimum and maximum experience.
        """
        if not text:
            return None, None

        text_lower = text.lower()

        if re.search(
            r"\b("
            r"fresher"
            r"|entry level"
            r"|0 years"
            r"|0-1 years"
            r")\b",
            text_lower,
        ):
            return 0, 1

        range_match = re.search(
            r"(\d+)"
            r"\s*(?:-|to)\s*"
            r"(\d+)"
            r"\s*(?:years?|yrs?)",
            text_lower,
        )

        if range_match:
            return (
                int(range_match.group(1)),
                int(range_match.group(2)),
            )

        plus_match = re.search(
            r"(\d+)\+\s*"
            r"(?:years?|yrs?)",
            text_lower,
        )

        if plus_match:
            return (
                int(plus_match.group(1)),
                None,
            )

        min_match = re.search(
            r"(?:minimum|min)\s*"
            r"(\d+)\s*"
            r"(?:years?|yrs?)",
            text_lower,
        )

        if min_match:
            return (
                int(min_match.group(1)),
                None,
            )

        single_match = re.search(
            r"(\d+)\s*"
            r"(?:years?|yrs?)",
            text_lower,
        )

        if single_match:
            value = int(
                single_match.group(1)
            )

            return value, value

        return None, None

    # ------------------------------------------------------------------
    # SALARY
    # ------------------------------------------------------------------

    def _extract_salary(
        self,
        text: str,
    ) -> Tuple[
        Optional[float],
        Optional[float],
        Optional[str],
    ]:
        """
        Extract salary information.
        """
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
                for symbol, code
                in currency_map.items()
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
            return (
                None,
                None,
                currency,
            )

        values = [
            float(number)
            for number in numbers
        ]

        cleaned_lower = (
            cleaned.lower()
        )

        multiplier = (
            100000
            if (
                "lpa" in cleaned_lower
                or "lakh" in cleaned_lower
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

    # ------------------------------------------------------------------
    # MAIN EXTRACTION
    # ------------------------------------------------------------------

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
        Extract structured intelligence from a job.
        """
        raw_text = (
            f"{title or ''} "
            f"{description or ''}"
        )

        normalized_text = (
            self._normalize_text(
                raw_text
            )
        )

        categories: Dict[
            str,
            List[WeightedItem],
        ] = {}

        for (
            category_name,
            _canonical_items,
        ) in self._canonical_items.items():

            alias_map = (
                self._get_alias_map(
                    category_name
                )
            )

            # Canonical taxonomy names must always be searchable,
            # even when they have no explicit alias entry.
            #
            # This prevents valid canonical skills such as
            # "Loyalty" and "Statistical Analysis" from being
            # silently missed by alias-only extraction.
            for canonical_item in _canonical_items:
                canonical_name = None

                if isinstance(canonical_item, str):
                    canonical_name = canonical_item

                elif isinstance(canonical_item, dict):
                    canonical_name = canonical_item.get(
                        "name"
                    )

                elif hasattr(canonical_item, "name"):
                    canonical_name = canonical_item.name

                if (
                    canonical_name
                    and str(canonical_name).strip()
                ):
                    canonical_name = str(
                        canonical_name
                    ).strip()

                    alias_map.setdefault(
                        canonical_name.lower(),
                        canonical_name,
                    )

            weighted = (
                self._extract_weighted_keywords_with_aliases(
                    normalized_text,
                    alias_map,
                )
            )

            if weighted:
                categories[
                    category_name
                ] = weighted

        # ------------------------------------------------------------
        # Derived CRM evidence: Multi Channel
        #
        # "multi-channel" / "multi channel" is a capability signal,
        # not a single communication channel. Normalize it into the
        # CRM concepts category so the profile's job_skill_mapping
        # remains the single source of truth for scoring.
        # ------------------------------------------------------------
        multi_channel_count = (
            normalized_text.count("multi-channel")
            + normalized_text.count("multi channel")
            + normalized_text.count("multichannel")
        )

        if multi_channel_count:
            concept_items = categories.setdefault(
                "crm_concepts",
                [],
            )

            existing = next(
                (
                    item
                    for item in concept_items
                    if item.name.strip().lower()
                    == "multi channel"
                ),
                None,
            )

            if existing is None:
                concept_items.append(
                    WeightedItem(
                        name="Multi Channel",
                        count=multi_channel_count,
                    )
                )
            else:
                existing.count += len(
                    multi_channel_count
                )

            concept_items.sort(
                key=lambda item: (
                    -item.count,
                    item.name,
                )
            )

        # Salary.
        if (
            salary_min is not None
            or salary_max is not None
        ):
            final_salary_min = salary_min
            final_salary_max = salary_max
            final_salary_currency = (
                salary_currency
            )
        else:
            (
                final_salary_min,
                final_salary_max,
                final_salary_currency,
            ) = self._extract_salary(
                raw_text
            )

        # Experience.
        if (
            experience_min is not None
            or experience_max is not None
        ):
            final_experience_min = (
                experience_min
            )
            final_experience_max = (
                experience_max
            )
        else:
            (
                final_experience_min,
                final_experience_max,
            ) = self._extract_experience(
                raw_text
            )

        return JobIntelligence(
            categories=categories,
            experience_min=(
                final_experience_min
            ),
            experience_max=(
                final_experience_max
            ),
            salary_min=(
                final_salary_min
            ),
            salary_max=(
                final_salary_max
            ),
            salary_currency=(
                final_salary_currency
            ),
        )

    # ------------------------------------------------------------------
    # JOB HELPERS
    # ------------------------------------------------------------------

    def extract_from_job(
        self,
        job,
    ) -> JobIntelligence:
        """
        Extract intelligence from a Job object.
        """
        return self.extract(
            title=getattr(
                job,
                "title",
                "",
            )
            or "",
            description=getattr(
                job,
                "description",
                "",
            )
            or "",
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
        """
        Extract intelligence from multiple jobs.
        """
        return [
            self.extract_from_job(job)
            for job in jobs
        ]
