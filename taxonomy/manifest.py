"""
ManifestWriter: Writes build manifest.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict

import yaml

from taxonomy.models import BuildManifest, CompiledCategory


class ManifestWriter:
    """Writes build manifests."""

    VERSION = "3.2.0"
    SCHEMA_VERSION = 2

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def write(self, categories: Dict[str, CompiledCategory]) -> BuildManifest:
        """Generate and write manifest."""
        total_items = sum(len(cat.items) for cat in categories.values())

        manifest = BuildManifest(
            version=self.VERSION,
            schema_version=self.SCHEMA_VERSION,
            build_id=hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8],
            build_date=datetime.now().isoformat(),
            categories=list(categories.keys()),
            statistics={
                "canonical_items": total_items,
                "flatten_depth": 1,
                "compiler_version": self.VERSION,
            },
        )

        manifest_dict = {
            "version": manifest.version,
            "schema_version": manifest.schema_version,
            "build_id": manifest.build_id,
            "build_date": manifest.build_date,
            "categories": manifest.categories,
            "statistics": manifest.statistics,
        }

        filepath = self.output_dir.parent / "taxonomy_manifest.yaml"
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(
                manifest_dict,
                f,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
                indent=2,
            )

        return manifest