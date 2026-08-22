"""
LookupBuilder: Builds lookup table from CompiledCategory.
"""

from __future__ import annotations

from typing import Dict, List

from taxonomy.models import CompiledCategory, TaxonomyBuildError
from taxonomy.normalizer import Normalizer


class LookupBuilder:
    """Builds lookup tables from compiled categories."""

    def __init__(self) -> None:
        self.normalizer = Normalizer()

    def build(self, categories: Dict[str, CompiledCategory]) -> Dict[str, Dict[str, str]]:
        """
        Build lookup tables for all categories.
        Raises TaxonomyBuildError on collisions.
        """
        lookups: Dict[str, Dict[str, str]] = {}
        conflicts: List[str] = []

        for category_name, category in categories.items():
            lookup: Dict[str, str] = {}
            category_conflicts = []

            for item in category.items:
                normalized_name = self.normalizer.normalize(item.name)

                # Canonical resolves to itself
                if normalized_name in lookup:
                    if lookup[normalized_name] != item.name:
                        category_conflicts.append(
                            f"Canonical '{item.name}' conflicts with "
                            f"'{lookup[normalized_name]}' for '{normalized_name}'"
                        )
                else:
                    lookup[normalized_name] = item.name

                # Aliases resolve to canonical
                for alias in item.aliases:
                    normalized_alias = self.normalizer.normalize(alias)
                    if normalized_alias in lookup:
                        if lookup[normalized_alias] != item.name:
                            category_conflicts.append(
                                f"Alias '{alias}' for '{item.name}' conflicts with "
                                f"'{lookup[normalized_alias]}'"
                            )
                    else:
                        lookup[normalized_alias] = item.name

            if category_conflicts:
                conflicts.extend([f"{category_name}: {c}" for c in category_conflicts])

            lookups[category_name] = lookup

        if conflicts:
            raise TaxonomyBuildError("lookup", "\n".join(conflicts))

        return lookups