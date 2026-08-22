"""
DictionaryWriter: Writes compiled taxonomy to YAML.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import yaml

from taxonomy.models import CompiledCategory


class DictionaryWriter:
    """Writes compiled taxonomy to YAML dictionaries."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write(
        self,
        categories: Dict[str, CompiledCategory],
        lookups: Dict[str, Dict[str, str]],
    ) -> None:
        """Write all categories to YAML."""

        for category_name, category in categories.items():

            # Sort items alphabetically
            sorted_items = sorted(category.items, key=lambda x: x.name.lower())

            for item in sorted_items:
                item.aliases = sorted(set(item.aliases))

            # ============================================================
            # DEBUG START
            # ============================================================
            print("\n" + "=" * 80)
            print(f"WRITING CATEGORY : {category_name}")
            print(f"TOTAL ITEMS      : {len(sorted_items)}")

            journey_items = [
                item.name
                for item in sorted_items
                if "Journey" in item.name
            ]

            print(f"JOURNEY ITEMS    : {journey_items}")

            customer_items = [
                item.name
                for item in sorted_items
                if "Customer" in item.name
            ]

            print(f"CUSTOMER ITEMS   : {customer_items}")

            print("=" * 80)
            # ============================================================
            # DEBUG END
            # ============================================================

            output = {
                "category": {
                    "name": category_name,
                },
                "items": [
                    {
                        "name": item.name,
                        "aliases": item.aliases,
                    }
                    for item in sorted_items
                ],
                "lookup": lookups[category_name],
            }

            filepath = self.output_dir / f"{category_name}.yaml"

            print(f"OUTPUT FILE      : {filepath}")

            with open(filepath, "w", encoding="utf-8") as f:
                yaml.dump(
                    output,
                    f,
                    allow_unicode=True,
                    sort_keys=False,
                    default_flow_style=False,
                    indent=2,
                    width=1000,
                )

            print("WRITE COMPLETE")