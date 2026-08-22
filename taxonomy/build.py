#!/usr/bin/env python3
"""
Taxonomy Build System - Orchestrator

Usage:
    python -m taxonomy.build --profile crm_manager
    python -m taxonomy.build --profile data_analyst

Phase: 4.2
Status: PRODUCTION
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict

from taxonomy.compiler import Compiler
from taxonomy.validator import Validator
from taxonomy.lookup import LookupBuilder
from taxonomy.dictionary_writer import DictionaryWriter
from taxonomy.manifest import ManifestWriter
from taxonomy.models import CompiledCategory, TaxonomyBuildError


class TaxonomyBuilder:
    """Orchestrates the complete build pipeline."""

    def __init__(self, seed_dir: Path, output_dir: Path) -> None:
        self.seed_dir = seed_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.compiler = Compiler()
        self.validator = Validator()
        self.lookup_builder = LookupBuilder()
        self.dictionary_writer = DictionaryWriter(output_dir)
        self.manifest_writer = ManifestWriter(output_dir)

    def build(self) -> bool:
        """Run the complete build pipeline. Returns True on success."""
        print("=" * 60)
        print("TAXONOMY BUILDER")
        print("=" * 60)
        print(f"Seed directory:  {self.seed_dir}")
        print(f"Output directory: {self.output_dir}")
        print("=" * 60 + "\n")

        categories: Dict[str, CompiledCategory] = {}

        # Step 1: Compile
        print(f"📂 Compiling seeds from {self.seed_dir}...")
        seed_files = list(self.seed_dir.glob("*.yaml"))

        if not seed_files:
            print(f"  ❌ No YAML files found in {self.seed_dir}")
            return False

        for seed_file in sorted(seed_files):
            if seed_file.name.startswith("_"):
                continue

            try:
                category = self.compiler.compile_file(seed_file)
                categories[category.name] = category
                print(f"  ✅ {category.name}: {len(category.items)} items")
            except Exception as e:
                print(f"  ❌ {seed_file.name}: {e}")
                return False

        # Step 2: Validate
        print("\n🔍 Validating compiled output...")
        try:
            self.validator.validate(categories)
            print("  ✅ Validation passed")
        except TaxonomyBuildError as e:
            print(f"  ❌ {e}")
            return False

        # Step 3: Build lookup
        print("\n🔍 Building lookup tables...")
        try:
            lookups = self.lookup_builder.build(categories)
            print(f"  ✅ Lookup built for {len(lookups)} categories")
        except TaxonomyBuildError as e:
            print(f"  ❌ {e}")
            return False

        # Step 4: Write dictionaries
        print("\n📝 Generating dictionaries...")
        try:
            self.dictionary_writer.write(categories, lookups)
            print(f"  ✅ Generated {len(categories)} dictionaries")
        except Exception as e:
            print(f"  ❌ {e}")
            return False

        # Step 5: Write manifest
        print("\n📝 Generating manifest...")
        try:
            manifest = self.manifest_writer.write(categories)
            print(f"  ✅ taxonomy_manifest.yaml (build_id: {manifest.build_id})")
        except Exception as e:
            print(f"  ❌ {e}")
            return False

        # Summary
        total_items = sum(len(cat.items) for cat in categories.values())

        print("\n" + "=" * 60)
        print("BUILD SUMMARY")
        print("=" * 60)
        print(f"Categories: {len(categories)}")
        print(f"Canonical items: {total_items}")
        print(f"Build ID: {manifest.build_id}")
        print(f"Output: {self.output_dir}")
        print("=" * 60)

        return True


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Taxonomy Build System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m taxonomy.build --profile crm_manager
  python -m taxonomy.build --profile data_analyst
        """,
    )
    parser.add_argument(
        "--profile",
        type=str,
        default="crm_manager",
        help=(
            "Profile name (e.g., crm_manager, data_analyst). "
            "Defaults to crm_manager."
        ),
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent

    # Seed directory: taxonomy/seed/{profile}/
    seed_dir = script_dir / "seed" / args.profile

    if not seed_dir.exists():
        print(f"❌ Profile seed directory not found: {seed_dir}")
        print(f"   Please create: {seed_dir}/")
        print(f"   And add taxonomy YAML files for profile '{args.profile}'")
        return 1

    seed_files = list(seed_dir.glob("*.yaml"))
    if not seed_files:
        print(f"❌ No YAML files found in: {seed_dir}")
        print(f"   Please add taxonomy YAML files for profile '{args.profile}'")
        return 1

    # Output directory: jobs/profiles/{profile}/dictionaries/
    output_dir = (
        script_dir / ".." / "jobs" / "profiles" / args.profile / "dictionaries"
    )

    builder = TaxonomyBuilder(seed_dir, output_dir)
    return 0 if builder.build() else 1


if __name__ == "__main__":
    sys.exit(main())