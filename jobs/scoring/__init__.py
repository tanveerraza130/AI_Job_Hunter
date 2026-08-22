"""
Profile Scoring Engine for AI Job Hunter.

Scores jobs against a user's profile using deterministic rules.
Phase 4.2: Scoring only. All weights and rules are configurable per profile.
"""

from __future__ import annotations

from jobs.scoring.models import ScoreResult, MatchBreakdown
from jobs.scoring.engine import ProfileScoringEngine

__all__ = [
    "ScoreResult",
    "MatchBreakdown",
    "ProfileScoringEngine",
]


# =============================================================================
# END OF FILE
# =============================================================================