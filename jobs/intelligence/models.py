"""
Job Intelligence models for AI Job Hunter.

Defines the structured data extracted from job descriptions.
Phase 4.1: Extraction only. No scoring weights.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class WeightedItem:
    """
    A weighted item with frequency count.

    Attributes:
        name: The canonical item name (e.g., "Salesforce Marketing Cloud").
        count: Number of times it appears in the text.
    """
    name: str
    count: int


@dataclass
class JobIntelligence:
    """
    Structured intelligence extracted from a job.

    Uses a generic categories dictionary to support any profile type.
    Each category contains a list of WeightedItems with frequency counts.

    Phase 4.1: Extraction only. All scoring rules belong in Phase 4.2.

    Attributes:
        categories: Dictionary mapping category names to weighted items.
                    Example: {"crm_skills": [WeightedItem(...)], ...}
        experience_min: Minimum years of experience.
        experience_max: Maximum years of experience.
        salary_min: Minimum salary.
        salary_max: Maximum salary.
        salary_currency: Salary currency.
    """
    categories: Dict[str, List[WeightedItem]] = field(default_factory=dict)
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None

    def get_category(self, category_name: str) -> List[WeightedItem]:
        """Get weighted items for a category, or empty list if not found."""
        if not self.categories:
            return []
        return self.categories.get(category_name, [])

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "categories": {
                k: [{"name": i.name, "count": i.count} for i in v]
                for k, v in self.categories.items()
            },
            "experience_min": self.experience_min,
            "experience_max": self.experience_max,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_currency": self.salary_currency,
        }


# =============================================================================
# END OF FILE
# =============================================================================