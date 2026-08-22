"""
Taxonomy validator.

Provides both the compiled-taxonomy validator and the legacy
dictionary-based validation helpers used by the test suite.
"""

from __future__ import annotations

from typing import Dict, List, Set

from taxonomy.models import CompiledCategory, TaxonomyBuildError
from taxonomy.normalizer import Normalizer


class Validator:
    """Validate taxonomy data and compiled taxonomy output."""

    def __init__(self) -> None:
        self.normalizer = Normalizer()

    # ------------------------------------------------------------------
    # Legacy dictionary API
    # ------------------------------------------------------------------

    def validate_schema(self, categories: Dict) -> bool:
        """Validate simple category dictionaries."""
        if not isinstance(categories, dict):
            return False

        for category_items in categories.values():
            if not isinstance(category_items, list):
                return False

            for item in category_items:
                if not isinstance(item, dict):
                    return False

                name = item.get("name")
                aliases = item.get("aliases")

                if not isinstance(name, str) or not name.strip():
                    return False

                if not isinstance(aliases, list) or not aliases:
                    return False

                if not all(
                    isinstance(alias, str) and alias.strip()
                    for alias in aliases
                ):
                    return False

        return True

    def check_duplicates(self, items: List[Dict]) -> Dict:
        """Check duplicate canonical names and aliases."""
        canonical_seen: Dict[str, Dict] = {}
        alias_seen: Dict[str, Dict] = {}

        canonical_duplicates = []
        alias_duplicates = []

        for item in items:
            name = str(item.get("name", "")).strip()
            normalized_name = self.normalizer.normalize(name)

            if normalized_name:
                if normalized_name in canonical_seen:
                    canonical_duplicates.append(name)
                else:
                    canonical_seen[normalized_name] = item

            for alias in item.get("aliases", []) or []:
                alias_text = str(alias).strip()
                normalized_alias = self.normalizer.normalize(alias_text)

                if not normalized_alias:
                    continue

                if normalized_alias in alias_seen:
                    alias_duplicates.append(alias_text)
                else:
                    alias_seen[normalized_alias] = item

        return {
            "has_duplicates": bool(
                canonical_duplicates or alias_duplicates
            ),
            "canonicals": canonical_duplicates,
            "aliases": alias_duplicates,
        }

    def check_alias_quality(self, items: List[Dict]) -> Dict:
        """Check aliases for low-quality values."""
        low_quality = []

        for item in items:
            name = str(item.get("name", "")).strip()
            normalized_name = self.normalizer.normalize(name)

            for alias in item.get("aliases", []) or []:
                alias_text = str(alias).strip()
                normalized_alias = self.normalizer.normalize(alias_text)

                if not normalized_alias:
                    low_quality.append(alias_text)
                    continue

                if normalized_alias == normalized_name:
                    low_quality.append(alias_text)
                    continue

                # Very short or overly generic aliases are low quality.
                if len(normalized_alias) <= 3:
                    low_quality.append(alias_text)

        return {
            "has_low_quality": bool(low_quality),
            "items": low_quality,
        }

    # ------------------------------------------------------------------
    # Compiled taxonomy validation
    # ------------------------------------------------------------------

    def validate(
        self,
        categories: Dict[str, CompiledCategory],
    ) -> None:
        """Validate compiled taxonomy output."""
        errors: List[str] = []

        all_canonicals: Set[str] = set()
        canonical_source: Dict[str, str] = {}

        for category_name, category in categories.items():
            for item in category.items:
                normalized_name = self.normalizer.normalize(item.name)

                if normalized_name in all_canonicals:
                    errors.append(
                        f"{category_name}: Duplicate canonical "
                        f"'{item.name}' "
                        f"(already in "
                        f"'{canonical_source[normalized_name]}')"
                    )

                all_canonicals.add(normalized_name)
                canonical_source[normalized_name] = category_name

        all_aliases: Set[str] = set()
        alias_source: Dict[str, Dict] = {}

        for category_name, category in categories.items():
            for item in category.items:
                name = item.name
                aliases = item.aliases
                normalized_name = self.normalizer.normalize(name)

                child_canonicals: Set[str] = set()

                for child_alias in item.child_map:
                    child_canonicals.add(
                        self.normalizer.normalize(child_alias)
                    )

                for alias in aliases:
                    normalized_alias = self.normalizer.normalize(alias)

                    if normalized_alias == normalized_name:
                        continue

                    if normalized_alias in all_aliases:
                        previous = alias_source[
                            normalized_alias
                        ]

                        errors.append(
                            f"{category_name}: Duplicate alias "
                            f"'{alias}' "
                            f"(already used by "
                            f"'{previous['canonical']}' "
                            f"in '{previous['category']}')"
                        )
                    else:
                        alias_source[normalized_alias] = {
                            "canonical": name,
                            "category": category_name,
                        }
                        all_aliases.add(normalized_alias)

                    if normalized_alias in all_canonicals:
                        if normalized_alias not in child_canonicals:
                            source_category = canonical_source[
                                normalized_alias
                            ]

                            errors.append(
                                f"{category_name}: Alias '{alias}' "
                                f"conflicts with canonical "
                                f"'{normalized_alias}' in "
                                f"'{source_category}'."
                            )

                if not aliases:
                    errors.append(
                        f"{category_name}: '{name}' has no aliases"
                    )

                for child_alias, parent in item.child_map.items():
                    if parent != name:
                        errors.append(
                            f"{category_name}: Child alias "
                            f"'{child_alias}' maps to "
                            f"'{parent}' not '{name}'"
                        )

        if errors:
            raise TaxonomyBuildError(
                "validator",
                "\n".join(errors),
            )
