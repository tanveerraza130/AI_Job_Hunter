"""
Taxonomy data models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class TaxonomyItem:
    """A single taxonomy item."""
    name: str
    aliases: List[str] = field(default_factory=list)
    children: List[TaxonomyItem] = field(default_factory=list)


@dataclass
class CompiledItem:
    """Compiled taxonomy item with flattened aliases."""
    name: str
    aliases: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)
    child_map: Dict[str, str] = field(default_factory=dict)


@dataclass
class CompiledCategory:
    """Compiled taxonomy category."""
    name: str
    items: List[CompiledItem] = field(default_factory=list)
    source_file: Optional[str] = None


@dataclass
class BuildManifest:
    """Build manifest."""
    version: str
    schema_version: int
    build_id: str
    build_date: str
    categories: List[str]
    statistics: Dict[str, Any]


class TaxonomyBuildError(Exception):
    """Raised when taxonomy build fails."""
    def __init__(self, stage: str, message: str):
        self.stage = stage
        self.message = message
        super().__init__(f"[{stage}] {message}")