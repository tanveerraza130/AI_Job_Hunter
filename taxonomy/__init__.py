"""
Taxonomy management for AI Job Hunter.

Provides:
- Hierarchical source taxonomy
- Build-time compilation
- Flat runtime dictionaries
- Lookup table generation
"""

from taxonomy.build import TaxonomyBuilder
from taxonomy.models import (
    TaxonomyItem,
    CompiledItem,
    CompiledCategory,
    BuildManifest,
    TaxonomyBuildError,
)

__version__ = "3.2.0"
__all__ = [
    "TaxonomyBuilder",
    "TaxonomyItem",
    "CompiledItem",
    "CompiledCategory",
    "BuildManifest",
    "TaxonomyBuildError",
]