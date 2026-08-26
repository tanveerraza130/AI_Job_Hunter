"""
Dashboard API routes.
"""

from __future__ import annotations

import json
import re
from typing import Optional

from duckdb import DuckDBPyConnection
from fastapi import APIRouter, Depends, Query

from api.config import settings
from api.database import get_db
from api.schemas import DashboardSummaryResponse

router = APIRouter()


def _location_filter(
    values: list[str],
    params: list[object],
) -> str | None:
    normalized = [
        value.strip().lower()
        for value in values
        if value and value.strip()
    ]

    if not normalized:
        return None

    parts: list[str] = []

    for value in normalized:
        parts.append(
            """
            LOWER(
                COALESCE(
                    l.canonical_name,
                    ''
                )
            ) LIKE ?
            """
        )
        params.append(f"%{value}%")

    return "(" + " OR ".join(parts) + ")"


def _json_match_filter(
    column_path: str,
    values: list[str],
    params: list[object],
) -> str | None:
    normalized = [
        value.strip().lower()
        for value in values
        if value and value.strip()
    ]

    if not normalized:
        return None

    parts: list[str] = []

    for value in normalized:
        parts.append(
            f"""
            EXISTS (
                SELECT 1
                FROM json_each(
                    s.score_breakdown,
                    '{column_path}'
                ) AS matched_value
                WHERE LOWER(
                    TRIM(
                        json_extract_string(
                            matched_value.value,
                            '$'
                        )
                    )
                ) = LOWER(?)
            )
            """
        )
        params.append(value)

    return "(" + " OR ".join(parts) + ")"


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    profile_id: str = Query(
        settings.default_profile
    ),
    search: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    location: list[str] = Query(default=[]),
    portal: Optional[str] = Query(None),
    skill: list[str] = Query(default=[]),
    tool: list[str] = Query(default=[]),
    relevance: list[str] = Query(default=["all"]),
    posted_date_from: Optional[str] = Query(None),
    posted_date_to: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None),
    db: DuckDBPyConnection = Depends(get_db),
) -> DashboardSummaryResponse:
    """
    Return KPI values for exactly the same filtered population
    used by the jobs result set.
    """

    params: list[object] = [
        profile_id,
    ]

    conditions: list[str] = []

    if min_score is not None:
        conditions.append(
            "s.overall_score >= ?"
        )
        params.append(min_score)

    normalized_relevance = [
        value.strip().lower()
        for value in relevance
        if value and value.strip()
    ]

    if not normalized_relevance:
        normalized_relevance = ["all"]

    allowed_relevance = {
        "all",
        "gte_30",
        "gte_70",
        "50_69",
        "30_49",
        "lt_30",
    }

    invalid_relevance = (
        set(normalized_relevance)
        - allowed_relevance
    )

    if invalid_relevance:
        raise ValueError(
            "Invalid relevance filter."
        )

    if "all" not in normalized_relevance:
        relevance_conditions: list[str] = []

        for relevance_value in normalized_relevance:
            if relevance_value == "gte_30":
                relevance_conditions.append(
                    "s.overall_score >= 30"
                )

            elif relevance_value == "gte_70":
                relevance_conditions.append(
                    "s.overall_score >= 70"
                )

            elif relevance_value == "50_69":
                relevance_conditions.append(
                    """
                    (
                        s.overall_score >= 50
                        AND s.overall_score < 70
                    )
                    """
                )

            elif relevance_value == "30_49":
                relevance_conditions.append(
                    """
                    (
                        s.overall_score >= 30
                        AND s.overall_score < 50
                    )
                    """
                )

            elif relevance_value == "lt_30":
                relevance_conditions.append(
                    "s.overall_score < 30"
                )

        if relevance_conditions:
            conditions.append(
                "("
                + " OR ".join(
                    relevance_conditions
                )
                + ")"
            )

    location_clause = _location_filter(
        location,
        params,
    )
    if location_clause:
        conditions.append(location_clause)

    if company and company.strip():
        conditions.append(
            """
            LOWER(
                COALESCE(
                    c.canonical_name,
                    ''
                )
            ) LIKE LOWER(?)
            """
        )
        params.append(
            f"%{company.strip()}%"
        )

    if portal and portal.strip():
        conditions.append(
            """
            LOWER(
                COALESCE(
                    j.portal,
                    ''
                )
            ) = LOWER(?)
            """
        )
        params.append(
            portal.strip()
        )

    skill_clause = _json_match_filter(
        "$.matched_skills",
        skill,
        params,
    )
    if skill_clause:
        conditions.append(skill_clause)

    tool_clause = _json_match_filter(
        "$.matched_tools",
        tool,
        params,
    )
    if tool_clause:
        conditions.append(tool_clause)

    if posted_date_from:
        conditions.append(
            "j.posted_date >= CAST(? AS DATE)"
        )
        params.append(posted_date_from)

    if posted_date_to:
        conditions.append(
            "j.posted_date <= CAST(? AS DATE)"
        )
        params.append(posted_date_to)

    if search and search.strip():
        pattern = f"%{search.strip()}%"

        conditions.append(
            """
            (
                LOWER(
                    COALESCE(j.title, '')
                ) LIKE LOWER(?)
                OR LOWER(
                    COALESCE(
                        c.canonical_name,
                        ''
                    )
                ) LIKE LOWER(?)
                OR LOWER(
                    COALESCE(
                        l.canonical_name,
                        ''
                    )
                ) LIKE LOWER(?)
                OR LOWER(
                    COALESCE(
                        j.description,
                        ''
                    )
                ) LIKE LOWER(?)
                OR EXISTS (
                    SELECT 1
                    FROM json_each(
                        s.score_breakdown,
                        '$.matched_skills'
                    ) AS matched_skill
                    WHERE LOWER(
                        json_extract_string(
                            matched_skill.value,
                            '$'
                        )
                    ) LIKE LOWER(?)
                )
                OR EXISTS (
                    SELECT 1
                    FROM json_each(
                        s.score_breakdown,
                        '$.matched_tools'
                    ) AS matched_tool
                    WHERE LOWER(
                        json_extract_string(
                            matched_tool.value,
                            '$'
                        )
                    ) LIKE LOWER(?)
                )
            )
            """
        )

        params.extend(
            [
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
            ]
        )

    where_clause = (
        "\n AND ".join(conditions)
        if conditions
        else "TRUE"
    )

    query = f"""
        WITH latest_score AS (
            SELECT
                job_id,
                profile_id,
                overall_score,
                score_breakdown,
                scored_at,
                ROW_NUMBER() OVER (
                    PARTITION BY
                        job_id,
                        profile_id
                    ORDER BY scored_at DESC
                ) AS rn
            FROM fact_job_scores
            WHERE profile_id = ?
        ),

        filtered AS (
            SELECT
                j.job_id,
                j.company_id,
                j.location_id,
                c.canonical_name AS company,
                l.canonical_name AS location,
                s.overall_score
            FROM fact_jobs j

            LEFT JOIN dim_company c
                ON j.company_id = c.company_id

            LEFT JOIN dim_location l
                ON j.location_id = l.location_id

            JOIN latest_score s
                ON j.job_id = s.job_id
               AND s.rn = 1

            WHERE {where_clause}
        )

        SELECT
            COUNT(DISTINCT job_id) AS total_jobs,
            COALESCE(
                AVG(overall_score),
                0
            ) AS average_score,
            COUNT(
                DISTINCT
                CASE
                    WHEN overall_score >= 70
                    THEN job_id
                END
            ) AS high_match_jobs,
            COUNT(DISTINCT company_id)
                AS companies_count,
            COUNT(DISTINCT location_id)
                AS locations_count
        FROM filtered
    """

    # latest_score CTE has profile_id as its first parameter,
    # Parameters follow the SQL placeholder order:
    # latest_score.profile_id, JOIN profile_id, filters.
    final_params = params
    result = db.execute(
        query,
        final_params,
    ).fetchone()

    latest_date = db.execute(
        """
        SELECT MAX(created_at)
        FROM search_session
        """
    ).fetchone()

    latest_value = (
        latest_date[0]
        if latest_date
        else None
    )

    if not result:
        return DashboardSummaryResponse(
            total_jobs=0,
            average_score=0.0,
            high_match_jobs=0,
            companies_count=0,
            locations_count=0,
            latest_search_date=None,
        )

    return DashboardSummaryResponse(
        total_jobs=int(result[0] or 0),
        average_score=round(
            float(result[1] or 0.0),
            2,
        ),
        high_match_jobs=int(
            result[2] or 0
        ),
        companies_count=int(
            result[3] or 0
        ),
        locations_count=int(
            result[4] or 0
        ),
        latest_search_date=(
            latest_value.date()
            if latest_value
            else None
        ),
    )
