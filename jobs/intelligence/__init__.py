"""
Job Intelligence Engine for AI Job Hunter.

Extracts structured intelligence from job descriptions using profile-specific
knowledge bases. Profile-driven: uses the profile type from the loaded profile.

Phase 4.1: Extraction only. Scoring weights belong in Phase 4.2.
"""

from __future__ import annotations

from jobs.intelligence.models import JobIntelligence, WeightedItem
from jobs.intelligence.extractor import IntelligenceExtractor
from jobs.intelligence.classifier import JobClassifier

__all__ = [
    "JobIntelligence",
    "WeightedItem",
    "IntelligenceExtractor",
    "JobClassifier",
]


# =============================================================================
# END OF FILE
# =============================================================================