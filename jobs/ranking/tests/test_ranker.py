"""
Tests for the JobRanker.

Verifies deterministic ranking rules:
1. Primary: overall_score DESC
2. Tie-breakers: skill_score DESC, tool_score DESC, experience_score DESC,
   salary_score DESC, work_mode_score DESC
3. Stable ordering: job_id ASC
"""

from jobs.ranking.ranker import JobRanker
from jobs.scoring.models import MatchBreakdown, ScoreResult


def create_score_result(
    job_id: str,
    overall_score: float,
    skill_match: float = 0.0,
    tool_match: float = 0.0,
    experience_match: float = 0.0,
    salary_match: float = 0.0,
    work_mode_match: float = 0.0,
) -> ScoreResult:
    """Helper to create a ScoreResult with specified values."""
    breakdown = MatchBreakdown(
        overall_score=overall_score,
        skill_match=skill_match,
        tool_match=tool_match,
        experience_match=experience_match,
        salary_match=salary_match,
        work_mode_match=work_mode_match,
        missing_skills=[],
        missing_tools=[],
        strengths=[],
    )
    return ScoreResult(
        job_id=job_id,
        title=f"Job {job_id}",
        company="Test Company",
        score=overall_score,
        breakdown=breakdown,
    )


class TestJobRanker:
    """Test suite for JobRanker."""

    def test_sort_by_overall_score_desc(self) -> None:
        """Test that jobs are sorted by overall_score DESC."""
        ranker = JobRanker()

        job_a = create_score_result("A", 91.0)
        job_b = create_score_result("B", 95.0)
        job_c = create_score_result("C", 87.0)

        results = ranker.rank_jobs([job_a, job_b, job_c])

        assert len(results) == 3
        assert results[0].job_id == "B"  # 95
        assert results[1].job_id == "A"  # 91
        assert results[2].job_id == "C"  # 87

    def test_tie_breaker_skill_score(self) -> None:
        """Test tie-breaker: skill_score DESC."""
        ranker = JobRanker()

        job_a = create_score_result("A", 95.0, skill_match=90.0)
        job_b = create_score_result("B", 95.0, skill_match=95.0)
        job_c = create_score_result("C", 95.0, skill_match=80.0)

        results = ranker.rank_jobs([job_a, job_b, job_c])

        assert len(results) == 3
        assert results[0].job_id == "B"  # 95 skill
        assert results[1].job_id == "A"  # 90 skill
        assert results[2].job_id == "C"  # 80 skill

    def test_tie_breaker_tool_score(self) -> None:
        """Test tie-breaker: tool_score DESC."""
        ranker = JobRanker()

        job_a = create_score_result("A", 95.0, skill_match=95.0, tool_match=80.0)
        job_b = create_score_result("B", 95.0, skill_match=95.0, tool_match=95.0)
        job_c = create_score_result("C", 95.0, skill_match=95.0, tool_match=70.0)

        results = ranker.rank_jobs([job_a, job_b, job_c])

        assert len(results) == 3
        assert results[0].job_id == "B"  # 95 tool
        assert results[1].job_id == "A"  # 80 tool
        assert results[2].job_id == "C"  # 70 tool

    def test_tie_breaker_experience_score(self) -> None:
        """Test tie-breaker: experience_score DESC."""
        ranker = JobRanker()

        job_a = create_score_result(
            "A", 95.0,
            skill_match=95.0,
            tool_match=95.0,
            experience_match=80.0,
        )
        job_b = create_score_result(
            "B", 95.0,
            skill_match=95.0,
            tool_match=95.0,
            experience_match=95.0,
        )

        results = ranker.rank_jobs([job_a, job_b])

        assert len(results) == 2
        assert results[0].job_id == "B"  # 95 experience
        assert results[1].job_id == "A"  # 80 experience

    def test_tie_breaker_salary_score(self) -> None:
        """Test tie-breaker: salary_score DESC."""
        ranker = JobRanker()

        job_a = create_score_result(
            "A", 95.0,
            skill_match=95.0,
            tool_match=95.0,
            experience_match=95.0,
            salary_match=80.0,
        )
        job_b = create_score_result(
            "B", 95.0,
            skill_match=95.0,
            tool_match=95.0,
            experience_match=95.0,
            salary_match=95.0,
        )

        results = ranker.rank_jobs([job_a, job_b])

        assert len(results) == 2
        assert results[0].job_id == "B"  # 95 salary
        assert results[1].job_id == "A"  # 80 salary

    def test_tie_breaker_work_mode_score(self) -> None:
        """Test tie-breaker: work_mode_score DESC."""
        ranker = JobRanker()

        job_a = create_score_result(
            "A", 95.0,
            skill_match=95.0,
            tool_match=95.0,
            experience_match=95.0,
            salary_match=95.0,
            work_mode_match=80.0,
        )
        job_b = create_score_result(
            "B", 95.0,
            skill_match=95.0,
            tool_match=95.0,
            experience_match=95.0,
            salary_match=95.0,
            work_mode_match=95.0,
        )

        results = ranker.rank_jobs([job_a, job_b])

        assert len(results) == 2
        assert results[0].job_id == "B"  # 95 work_mode
        assert results[1].job_id == "A"  # 80 work_mode

    def test_stable_ordering_job_id_asc(self) -> None:
        """Test stable ordering: job_id ASC when all scores equal."""
        ranker = JobRanker()

        job_a = create_score_result("A", 95.0, skill_match=95.0, tool_match=95.0)
        job_b = create_score_result("B", 95.0, skill_match=95.0, tool_match=95.0)
        job_c = create_score_result("C", 95.0, skill_match=95.0, tool_match=95.0)

        results = ranker.rank_jobs([job_b, job_a, job_c])

        assert len(results) == 3
        assert results[0].job_id == "A"
        assert results[1].job_id == "B"
        assert results[2].job_id == "C"

    def test_empty_list_returns_empty(self) -> None:
        """Test that empty input returns empty list."""
        ranker = JobRanker()
        results = ranker.rank_jobs([])
        assert results == []

    def test_rank_jobs_realistic_mix(self) -> None:
        """Test a realistic mix of jobs with different scores."""
        ranker = JobRanker()

        job_a = create_score_result("A", 91.0, skill_match=90.0, tool_match=85.0)
        job_b = create_score_result("B", 95.0, skill_match=70.0, tool_match=60.0)
        job_c = create_score_result("C", 95.0, skill_match=95.0, tool_match=90.0)

        results = ranker.rank_jobs([job_a, job_b, job_c])

        assert len(results) == 3
        # Job C: overall=95, skill=95 (highest skill among 95s)
        assert results[0].job_id == "C"
        # Job B: overall=95, skill=70 (second among 95s)
        assert results[1].job_id == "B"
        # Job A: overall=91 (lowest overall)
        assert results[2].job_id == "A"