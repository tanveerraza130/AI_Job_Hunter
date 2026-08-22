"""
Score repository for AI Job Hunter.

Stores job scores in fact_job_scores.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any, Optional
from uuid import UUID

import duckdb

from jobs.scoring.models import ScoreResult
from jobs.version import AI_PIPELINE_VERSION

logger = logging.getLogger(__name__)


class ScoreRepository:
    """
    Repository for storing job scores.

    Attributes:
        connection: Shared DuckDB connection.
        scoring_version: Version of the scoring algorithm (e.g., "v1", "v1.1").
    """

    def __init__(
        self,
        connection: duckdb.DuckDBPyConnection,
        scoring_version: str = "v1",
    ) -> None:
        """
        Initialize the repository with a shared DuckDB connection.

        Args:
            connection: Active DuckDB connection.
            scoring_version: Version of the scoring algorithm.
        """
        self.connection: duckdb.DuckDBPyConnection = connection
        self.scoring_version: str = scoring_version

    def has_score(
        self,
        job_id: str,
        profile_id: str,
    ) -> bool:
        """
        Check whether a job has already been scored for a profile.
        """
        result = self.connection.execute(
            """
            SELECT 1
            FROM fact_job_scores
            WHERE job_id = ?
              AND profile_id = ?
            LIMIT 1
            """,
            [job_id, profile_id],
        ).fetchone()

        return result is not None

    def save_score_result(
        self,
        job_id: str,
        profile_id: str,
        search_session_id: UUID,
        score_result: ScoreResult,
        pipeline_version: Optional[str] = None,
    ) -> None:
        """
        Save a ScoreResult to the database.

        Args:
            job_id: Unique job identifier.
            profile_id: Profile identifier (e.g., "crm_manager").
            search_session_id: Search session UUID.
            score_result: ScoreResult from the scoring engine.
            pipeline_version: Version of the AI pipeline (defaults to AI_PIPELINE_VERSION).
        """

        # ============================================================

        self.connection.execute(
            """
            INSERT INTO fact_job_scores (
                job_id,
                profile_id,
                search_session_id,
                overall_score,
                skill_score,
                tool_score,
                experience_score,
                salary_score,
                work_mode_score,
                score_breakdown,
                scoring_version,
                pipeline_version,
                scored_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (
                job_id,
                profile_id,
                search_session_id
            )
            DO UPDATE SET
                overall_score = excluded.overall_score,
                skill_score = excluded.skill_score,
                tool_score = excluded.tool_score,
                experience_score = excluded.experience_score,
                salary_score = excluded.salary_score,
                work_mode_score = excluded.work_mode_score,
                score_breakdown = excluded.score_breakdown,
                scoring_version = excluded.scoring_version,
                pipeline_version = excluded.pipeline_version,
                scored_at = excluded.scored_at
            """,
            [
                job_id,
                profile_id,
                search_session_id,
                score_result.score,
                score_result.breakdown.skill_match,
                score_result.breakdown.tool_match,
                score_result.breakdown.experience_match,
                score_result.breakdown.salary_match,
                score_result.breakdown.work_mode_match,
                json.dumps(
                    score_result.breakdown.to_dict(),
                    default=str,
                ),
                self.scoring_version,
                pipeline_version or AI_PIPELINE_VERSION,
                datetime.now(UTC),
            ],
        )
