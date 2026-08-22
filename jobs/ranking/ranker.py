"""
Ranker for AI Job Hunter.

Deterministically ranks already-scored jobs based on ScoreResult.
Ranking is based on overall_score DESC, then tie-breakers.
"""

from jobs.scoring.models import ScoreResult


class JobRanker:
    """
    Deterministic ranker for scored jobs.

    Sorts jobs based on overall_score DESC with tie-breakers:
    1. skill_score DESC
    2. tool_score DESC
    3. experience_score DESC
    4. salary_score DESC
    5. work_mode_score DESC
    6. job_id ASC (stable ordering)

    Returns sorted list. No mutation of ScoreResult objects.
    """

    def rank_jobs(self, score_results: list[ScoreResult]) -> list[ScoreResult]:
        """
        Rank a list of scored jobs.

        Args:
            score_results: List of ScoreResult objects to rank.

        Returns:
            list[ScoreResult]: Sorted list according to ranking rules.
        """
        if not score_results:
            return []

        return sorted(
            score_results,
            key=self._sort_key,
        )

    @staticmethod
    def _sort_key(result: ScoreResult) -> tuple:
        """
        Generate a sort key tuple for a ScoreResult.

        The tuple order matches the ranking rules:
        1. overall_score DESC
        2. skill_score DESC
        3. tool_score DESC
        4. experience_score DESC
        5. salary_score DESC
        6. work_mode_score DESC
        7. job_id ASC (stable ordering)

        Python sorting is stable. job_id is the final ascending key to
        guarantee deterministic ordering when all scores are equal.

        Returns:
            tuple: Sort key with negative values for DESC fields.
        """
        return (
            -result.score,
            -result.breakdown.skill_match,
            -result.breakdown.tool_match,
            -result.breakdown.experience_match,
            -result.breakdown.salary_match,
            -result.breakdown.work_mode_match,
            result.job_id,
        )