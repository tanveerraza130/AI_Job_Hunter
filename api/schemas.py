"""
Pydantic schemas for API responses.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Score Schemas
# =============================================================================


class ScoreBreakdown(BaseModel):
    """
    Detailed score breakdown for a job.

    Existing fields are preserved for backward compatibility.
    jd_match and title_match are optional because older score records
    may not contain these values.
    """

    skill_match: float = 0.0
    tool_match: float = 0.0
    experience_match: float = 0.0
    salary_match: float = 0.0
    work_mode_match: float = 0.0

    jd_match: Optional[float] = None
    title_match: Optional[float] = None

    matched_skills: List[str] = Field(
        default_factory=list
    )

    matched_tools: List[str] = Field(
        default_factory=list
    )

    missing_skills: List[str] = Field(
        default_factory=list
    )

    missing_tools: List[str] = Field(
        default_factory=list
    )

    strengths: List[str] = Field(
        default_factory=list
    )


class ScoreDetail(BaseModel):
    """
    Complete score information for a job.
    """

    job_id: str
    profile_id: str

    overall_score: float
    skill_score: float
    tool_score: float
    experience_score: float
    salary_score: float
    work_mode_score: float

    score_breakdown: Optional[ScoreBreakdown] = None

    scored_at: Optional[datetime] = None


class ScoreListResponse(BaseModel):
    total: int
    scores: List[ScoreDetail] = Field(
        default_factory=list
    )


# =============================================================================
# Job Schemas
# =============================================================================


class JobBase(BaseModel):
    job_id: str
    title: str
    company: str

    location: Optional[str] = None
    portal: Optional[str] = None


class JobDetail(JobBase):
    """
    Complete job details returned by the job-detail endpoint.
    """

    description: Optional[str] = None

    job_url: Optional[str] = None

    posted_date: Optional[date] = None

    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None

    experience_min: Optional[int] = None
    experience_max: Optional[int] = None

    employment_type: Optional[str] = None

    score: Optional[ScoreDetail] = None

    search_score: Optional[float] = None

    match_reason: List[str] = Field(
        default_factory=list
    )


class JobWithScore(JobBase):
    """
    UI-ready job card representation.

    Contains the complete job information required by the
    Jobs listing UI together with AI relevance scoring.
    """

    # -------------------------------------------------------------------------
    # Job information
    # -------------------------------------------------------------------------

    job_url: Optional[str] = None

    posted_date: Optional[date] = None

    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None

    experience_min: Optional[int] = None
    experience_max: Optional[int] = None

    employment_type: Optional[str] = None

    skills: List[str] = Field(
        default_factory=list
    )

    # -------------------------------------------------------------------------
    # Existing scoring fields
    # -------------------------------------------------------------------------

    overall_score: Optional[float] = None
    skill_score: Optional[float] = None
    tool_score: Optional[float] = None
    experience_score: Optional[float] = None
    salary_score: Optional[float] = None
    work_mode_score: Optional[float] = None

    score_breakdown: Optional[ScoreBreakdown] = None

    # -------------------------------------------------------------------------
    # Search relevance
    # -------------------------------------------------------------------------

    search_score: Optional[float] = None

    # -------------------------------------------------------------------------
    # Why this job matched
    # -------------------------------------------------------------------------

    match_reason: List[str] = Field(
        default_factory=list
    )

    # -------------------------------------------------------------------------
    # Global rank within the filtered/sorted result set
    # -------------------------------------------------------------------------

    rank: Optional[int] = None


class JobListResponse(BaseModel):
    total: int
    page: int
    page_size: int

    jobs: List[JobWithScore] = Field(
        default_factory=list
    )


# =============================================================================
# Dashboard Schemas
# =============================================================================


class DashboardSummaryResponse(BaseModel):
    total_jobs: int
    average_score: float
    high_match_jobs: int
    companies_count: int
    locations_count: int
    latest_search_date: Optional[date] = None


class DashboardStats(BaseModel):
    total_jobs: int
    total_scored: int
    average_score: float

    top_job: Optional[JobWithScore] = None

    profile_name: str


class ScoreDistribution(BaseModel):
    bucket: str
    count: int


class TopSkill(BaseModel):
    skill_name: str
    count: int


class DashboardData(BaseModel):
    stats: DashboardStats

    distribution: List[ScoreDistribution] = Field(
        default_factory=list
    )

    top_skills: List[TopSkill] = Field(
        default_factory=list
    )

    recent_jobs: List[JobWithScore] = Field(
        default_factory=list
    )


# =============================================================================
# Profile Schemas
# =============================================================================


class ProfileSkill(BaseModel):
    name: str
    weight: Optional[float] = 1.0


class ProfileResponse(BaseModel):
    profile_id: str
    profile_name: str

    skills: List[ProfileSkill] = Field(
        default_factory=list
    )

    tools: List[str] = Field(
        default_factory=list
    )

    experience_min: Optional[int] = None
    experience_max: Optional[int] = None

    salary_min: Optional[float] = None
    salary_max: Optional[float] = None

    work_modes: List[str] = Field(
        default_factory=list
    )


class ProfileListResponse(BaseModel):
    profiles: List[str] = Field(
        default_factory=list
    )


# =============================================================================
# Session Schemas
# =============================================================================


class SessionSummary(BaseModel):
    execution_id: str

    keyword: str
    location: str
    portal: str

    status: str

    jobs_found: int
    valid_jobs: int
    exported_jobs: int

    created_at: datetime

    completed_at: Optional[datetime] = None


class SessionListResponse(BaseModel):
    total: int

    sessions: List[SessionSummary] = Field(
        default_factory=list
    )


# =============================================================================
# Pagination
# =============================================================================


class PaginationParams(BaseModel):
    page: int = Field(
        default=1,
        ge=1,
    )

    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
    )

    sort_by: Optional[str] = None

    sort_order: Optional[str] = "desc"