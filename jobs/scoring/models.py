"""
Scoring models for AI Job Hunter.

Defines the output of the Profile Scoring Engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class MatchBreakdown:
    """
    Detailed breakdown of a job match.

    Attributes:
        overall_score: Overall match score (0-100).
        skill_match: Skill match percentage (0-100) - deprecated, kept for backward compatibility.
        tool_match: Tool match percentage (0-100).
        experience_match: Experience match percentage (0-100) - deprecated, kept for backward compatibility.
        salary_match: Salary match percentage (0-100) - deprecated, kept for backward compatibility.
        work_mode_match: Work mode match percentage (0-100) - deprecated, kept for backward compatibility.
        jd_match: JD/Capability match percentage (0-100).
        title_match: Title match percentage (0-100).
        negative_penalty: Penalty applied for negative signals (0-100).
        missing_skills: Skills required by profile but not found in job.
        missing_tools: Tools required by profile but not found in job.
        strengths: Skills/tools where job exceeds profile requirements.
    """
    overall_score: float = 0.0
    skill_match: float = 0.0  # deprecated, kept for backward compatibility
    tool_match: float = 0.0
    experience_match: float = 0.0  # deprecated, kept for backward compatibility
    salary_match: float = 0.0  # deprecated, kept for backward compatibility
    work_mode_match: float = 0.0  # deprecated, kept for backward compatibility
    jd_match: float = 0.0
    title_match: float = 0.0
    negative_penalty: float = 0.0
    matched_skills: List[str] = field(default_factory=list)
    matched_tools: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    missing_tools: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "overall_score": round(self.overall_score, 1),
            "skill_match": round(self.skill_match, 1),
            "tool_match": round(self.tool_match, 1),
            "experience_match": round(self.experience_match, 1),
            "salary_match": round(self.salary_match, 1),
            "work_mode_match": round(self.work_mode_match, 1),
            "jd_match": round(self.jd_match, 1),
            "title_match": round(self.title_match, 1),
            "negative_penalty": round(self.negative_penalty, 1),
            "matched_skills": self.matched_skills,
            "matched_tools": self.matched_tools,
            "missing_skills": self.missing_skills,
            "missing_tools": self.missing_tools,
            "strengths": self.strengths,
        }


@dataclass
class ScoreResult:
    """
    Complete scoring result for a job.

    Attributes:
        job_id: Unique job identifier.
        title: Job title.
        company: Company name.
        score: Overall score (0-100).
        breakdown: Detailed match breakdown.
        intelligence: The JobIntelligence used for scoring.
    """
    job_id: str
    title: str
    company: str
    score: float
    breakdown: MatchBreakdown
    intelligence: Optional[object] = None  # JobIntelligence

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "job_id": self.job_id,
            "title": self.title,
            "company": self.company,
            "score": round(self.score, 1),
            "breakdown": self.breakdown.to_dict(),
        }


# =============================================================================
# END OF FILE
# =============================================================================