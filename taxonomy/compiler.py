"""
Compiler: Seed → CompiledCategory.
No validation. No lookup. Just conversion.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set

import yaml

from taxonomy.models import CompiledItem, CompiledCategory
from taxonomy.normalizer import Normalizer


class Compiler:
    """Compiles hierarchical taxonomy seeds into flat compiled output."""

    MAX_FLATTEN_DEPTH = 1

    def __init__(self) -> None:
        self.normalizer = Normalizer()

    def compile_file(self, filepath: Path) -> CompiledCategory:
        """Compile a single seed file to CompiledCategory."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        category = data.get("category", {})
        category_name = category.get("name", filepath.stem)
        items = data.get("items", [])

        # Track aliases and canonicals for compilation
        all_aliases: Set[str] = set()
        all_canonicals: Set[str] = set()
        compiled_items = []

        for item in items:
            compiled, _ = self._compile_item(
                item, all_aliases, all_canonicals
            )
            if compiled:
                compiled_items.append(compiled)

        return CompiledCategory(
            name=category_name,
            items=compiled_items,
            source_file=str(filepath),
        )

    def _compile_item(
        self,
        item: Dict,
        all_aliases: Set[str],
        all_canonicals: Set[str],
    ) -> Tuple[Optional[CompiledItem], List[str]]:
        """Compile a single hierarchical item."""
        name = item.get("name", "")
        aliases = item.get("aliases", [])
        children = item.get("children", [])
        warnings = []

        if not name:
            return None, warnings

        # Normalize canonical
        normalized_name = self.normalizer.normalize(name)
        all_canonicals.add(normalized_name)

        # Start with aliases only - do NOT add canonical
        all_item_aliases = list(aliases)

        # Process children - flatten only one level
        child_names = []
        child_map = {}

        for child in children:
            child_name = child.get("name", "")
            child_aliases = child.get("aliases", [])

            if not child_name:
                continue

            child_names.append(child_name)
            child_map[child_name] = name

            # Child's name becomes alias of parent
            if child_name not in all_item_aliases:
                all_item_aliases.append(child_name)

            # Child's aliases become aliases of parent
            for child_alias in child_aliases:
                if child_alias not in all_item_aliases:
                    all_item_aliases.append(child_alias)
                    child_map[child_alias] = name

        # Normalize all aliases
        normalized_aliases = []
        for alias in all_item_aliases:
            normalized = self.normalizer.normalize(alias)
            if not normalized:
                continue

            # Skip if alias equals canonical
            if normalized == normalized_name:
                continue

            # Track for validation
            if normalized not in all_aliases:
                normalized_aliases.append(normalized)
                all_aliases.add(normalized)

        return CompiledItem(
            name=name,
            aliases=normalized_aliases,
            children=child_names,
            child_map=child_map,
        ), warnings