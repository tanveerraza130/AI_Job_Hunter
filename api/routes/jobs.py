"""
Jobs API routes.

Production-ready Jobs API optimized for:
- AI relevance-first ranking
- deterministic filtering
- stable pagination
- fast UI-ready job cards
- safe SQL parameterization
- no N+1 queries
"""

from __future__ import annotations

import json
import re
from typing import Optional

from duckdb import DuckDBPyConnection
from fastapi import APIRouter, Depends, HTTPException, Query

from api.config import settings
from api.database import get_db
from jobs.profiles.loader import ConfigLoader

from api.schemas import (
    JobDetail,
    JobListResponse,
    JobWithScore,
    ScoreBreakdown,
    ScoreDetail,
)

router = APIRouter()


def _add_match_evidence(
    breakdown: ScoreBreakdown | None,
    profile_id: str,
) -> ScoreBreakdown | None:
    """
    Preserve job-specific matched intelligence from the persisted
    score_breakdown.

    IMPORTANT:
    Do not derive matched skills/tools from the profile taxonomy.
    The profile taxonomy contains capabilities, not job-specific matches.
    The scoring engine / persisted score_breakdown is the source of truth.
    """
    if breakdown is None:
        return None

    # Keep the actual persisted job-specific evidence untouched.
    # Never populate these fields from ConfigLoader/profile.skills/tools.
    return breakdown


@router.get("/jobs")
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    profile_id: str = Query(settings.default_profile),
    min_score: Optional[float] = Query(
        None,
        ge=0,
        le=100,
    ),
    location: list[str] = Query(default=[]),
    company: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    portal: Optional[str] = Query(None),
    skill: list[str] = Query(default=[]),
    tool: list[str] = Query(default=[]),
    relevance: list[str] = Query(default=["all"]),
    posted_date_from: Optional[str] = Query(None),
    posted_date_to: Optional[str] = Query(None),
    sort: str = Query("score"),
    db: DuckDBPyConnection = Depends(get_db),
) -> JobListResponse:
    """
    Return filtered, ranked, paginated jobs.

    Ranking:

        Every filtered/search result is ranked by AI match score:

        overall_score DESC
        skill_score DESC
        tool_score DESC
        jd_match DESC
        title_match DESC
        posted_date DESC NULLS LAST
        job_id ASC

        Search/filter parameters restrict the result set but never
        override AI relevance ranking.

        The legacy sort parameter is accepted for frontend compatibility,
        but all values use the same AI relevance ranking.
    """

    sort_mode = (sort or "score").strip().lower()

    allowed_sorts = {
        "score",
        "newest",
        "oldest",
    }

    if sort_mode not in allowed_sorts:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid sort. "
                "Allowed values: score, newest, oldest."
            ),
        )

    normalized_search = (
        search.strip()
        if search and search.strip()
        else None
    )

    normalized_locations = [
        value.strip()
        for value in location
        if value and value.strip()
    ]

    normalized_skills = [
        value.strip().lower()
        for value in skill
        if value and value.strip()
    ]

    normalized_tools = [
        value.strip().lower()
        for value in tool
        if value and value.strip()
    ]

    normalized_relevance = [
        value.strip().lower()
        for value in relevance
        if value and value.strip()
    ]

    if not normalized_relevance:
        normalized_relevance = ["all"]

    allowed_relevance = {
        "all",
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
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid relevance. "
                "Allowed values: all, gte_70, "
                "50_69, 30_49, lt_30."
            ),
        )

    normalized_company = (
        company.strip()
        if company and company.strip()
        else None
    )

    normalized_portal = (
        portal.strip()
        if portal and portal.strip()
        else None
    )

    # ------------------------------------------------------------------
    # Build WHERE conditions and parameters together.
    #
    # Parameter order is intentionally controlled here so every
    # positional placeholder has exactly one supplied value.
    # ------------------------------------------------------------------

    where_conditions: list[str] = [
        "s.profile_id = ?",
    ]

    params: list[object] = [
        profile_id,
    ]

    if min_score is not None:
        where_conditions.append(
            "s.overall_score >= ?"
        )
        params.append(min_score)

    if normalized_locations:
        location_conditions = []

        for location_value in normalized_locations:
            location_conditions.append(
                """
                LOWER(COALESCE(l.canonical_name, ''))
                LIKE LOWER(?)
                """
            )
            params.append(
                f"%{location_value}%"
            )

        where_conditions.append(
            "(" + " OR ".join(location_conditions) + ")"
        )

    if normalized_company:
        where_conditions.append(
            """
            LOWER(COALESCE(c.canonical_name, ''))
            LIKE LOWER(?)
            """
        )
        params.append(
            f"%{normalized_company}%"
        )

    if normalized_portal:
        where_conditions.append(
            """
            LOWER(COALESCE(j.portal, ''))
            = LOWER(?)
            """
        )
        params.append(
            normalized_portal
        )

    if posted_date_from:
        where_conditions.append(
            "j.posted_date >= CAST(? AS DATE)"
        )
        params.append(posted_date_from)

    if posted_date_to:
        where_conditions.append(
            "j.posted_date <= CAST(? AS DATE)"
        )
        params.append(posted_date_to)

    if "all" not in normalized_relevance:
        relevance_conditions: list[str] = []

        for relevance_value in normalized_relevance:
            if relevance_value == "gte_70":
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
            where_conditions.append(
                "("
                + " OR ".join(
                    relevance_conditions
                )
                + ")"
            )

    if normalized_skills:
        skill_conditions = []

        for skill_value in normalized_skills:
            skill_conditions.append(
                """
                EXISTS (
                    SELECT 1
                    FROM json_each(
                        s.score_breakdown,
                        '$.matched_skills'
                    ) AS matched_skill
                    WHERE LOWER(
                        TRIM(
                            json_extract_string(
                                matched_skill.value,
                                '$'
                            )
                        )
                    ) = LOWER(?)
                )
                """
            )
            params.append(skill_value)

        where_conditions.append(
            "(" + " OR ".join(skill_conditions) + ")"
        )

    if normalized_tools:
        tool_conditions = []

        for tool_value in normalized_tools:
            tool_conditions.append(
                """
                EXISTS (
                    SELECT 1
                    FROM json_each(
                        s.score_breakdown,
                        '$.matched_tools'
                    ) AS matched_tool
                    WHERE LOWER(
                        TRIM(
                            json_extract_string(
                                matched_tool.value,
                                '$'
                            )
                        )
                    ) = LOWER(?)
                )
                """
            )
            params.append(tool_value)

        where_conditions.append(
            "(" + " OR ".join(tool_conditions) + ")"
        )

    if normalized_search:
        search_pattern = (
            f"%{normalized_search}%"
        )

        where_conditions.append(
            """
            (
                LOWER(COALESCE(j.title, ''))
                    LIKE LOWER(?)
                OR LOWER(COALESCE(c.canonical_name, ''))
                    LIKE LOWER(?)
                OR LOWER(COALESCE(l.canonical_name, ''))
                    LIKE LOWER(?)
                OR LOWER(COALESCE(sd.skills, ''))
                    LIKE LOWER(?)
                OR LOWER(COALESCE(j.description, ''))
                    LIKE LOWER(?)
                OR LOWER(COALESCE(j.portal, ''))
                    LIKE LOWER(?)
            )
            """
        )

        params.extend(
            [
                search_pattern,
                search_pattern,
                search_pattern,
                search_pattern,
                search_pattern,
                search_pattern,
            ]
        )

    where_clause = "\n AND ".join(
        where_conditions
    )

    # ------------------------------------------------------------------
    # Score tie-breakers.
    #
    # Current score_breakdown may not contain jd_match/title_match.
    # TRY_CAST keeps the query safe when those values are absent.
    # ------------------------------------------------------------------

    jd_match_expression = """
        COALESCE(
            TRY_CAST(
                json_extract_string(
                    s.score_breakdown,
                    '$.jd_match'
                ) AS DOUBLE
            ),
            0.0
        )
    """

    title_match_expression = """
        COALESCE(
            TRY_CAST(
                json_extract_string(
                    s.score_breakdown,
                    '$.title_match'
                ) AS DOUBLE
            ),
            0.0
        )
    """

    # ------------------------------------------------------------------
    # Search relevance is explainability only.
    #
    # It does NOT participate ahead of AI score.
    # ------------------------------------------------------------------

    if normalized_search:
        search_pattern_sql = "LOWER(?)"

        search_score_expression = f"""
            (
                CASE
                    WHEN LOWER(COALESCE(j.title, ''))
                        LIKE {search_pattern_sql}
                    THEN 1
                    ELSE 0
                END
                +
                CASE
                    WHEN LOWER(COALESCE(c.canonical_name, ''))
                        LIKE {search_pattern_sql}
                    THEN 1
                    ELSE 0
                END
                +
                CASE
                    WHEN LOWER(COALESCE(l.canonical_name, ''))
                        LIKE {search_pattern_sql}
                    THEN 1
                    ELSE 0
                END
                +
                CASE
                    WHEN LOWER(COALESCE(sd.skills, ''))
                        LIKE {search_pattern_sql}
                    THEN 1
                    ELSE 0
                END
                +
                CASE
                    WHEN LOWER(COALESCE(j.description, ''))
                        LIKE {search_pattern_sql}
                    THEN 1
                    ELSE 0
                END
                +
                CASE
                    WHEN LOWER(COALESCE(j.portal, ''))
                        LIKE {search_pattern_sql}
                    THEN 1
                    ELSE 0
                END
            )
        """

        # Six parameters used by search_score_expression.
        search_score_params: list[object] = [
            search_pattern,
            search_pattern,
            search_pattern,
            search_pattern,
            search_pattern,
            search_pattern,
        ]
    else:
        search_score_expression = "0.0"
        search_score_params = []

    # ------------------------------------------------------------------
    # Ranking.
    #
    # LOCKED PRODUCT RULE:
    # Every filtered/search result is always ranked by AI match score.
    #
    # UI sort values such as "newest" or "oldest" remain accepted for
    # backward compatibility, but they MUST NOT override AI relevance.
    #
    # ROW_NUMBER gives each result its global rank before pagination.
    # COUNT(*) OVER() gives filtered total in the same retrieval query.
    # ------------------------------------------------------------------

    if sort_mode == "newest":
        order_expression = """
            posted_date DESC NULLS LAST,
            overall_score DESC,
            skill_score DESC,
            tool_score DESC,
            jd_match DESC,
            title_match DESC,
            job_id ASC
        """

    elif sort_mode == "oldest":
        order_expression = """
            posted_date ASC NULLS LAST,
            overall_score DESC,
            skill_score DESC,
            tool_score DESC,
            jd_match DESC,
            title_match DESC,
            job_id ASC
        """

    else:
        order_expression = """
            overall_score DESC,
            skill_score DESC,
            tool_score DESC,
            jd_match DESC,
            title_match DESC,
            posted_date DESC NULLS LAST,
            job_id ASC
        """

    # ------------------------------------------------------------------
    # Single data query.
    #
    # latest_scores:
    #   latest score per job/profile
    #
    # skill_data:
    #   all normalized skills in one aggregation
    #
    # ranked_jobs:
    #   global ranking + filtered count
    # ------------------------------------------------------------------

    query = f"""
        WITH latest_scores AS (
            SELECT
                job_id,
                profile_id,
                overall_score,
                skill_score,
                tool_score,
                experience_score,
                salary_score,
                work_mode_score,
                score_breakdown,
                scored_at,

                ROW_NUMBER() OVER (
                    PARTITION BY job_id, profile_id
                    ORDER BY scored_at DESC
                ) AS rn

            FROM fact_job_scores
        ),

        skill_data AS (
            SELECT
                fjs.job_id,

                STRING_AGG(
                    DISTINCT ds.name,
                    ', '
                    ORDER BY ds.name
                ) AS skills

            FROM fact_jobs_skills fjs

            JOIN dim_skill ds
                ON fjs.skill_id = ds.skill_id

            GROUP BY fjs.job_id
        ),

        filtered_jobs AS (
            SELECT
                j.job_id,
                j.title,
                c.canonical_name AS company,
                l.canonical_name AS location,
                j.portal,

                j.job_url,
                j.posted_date,

                j.salary_min,
                j.salary_max,
                j.salary_currency,

                j.experience_min,
                j.experience_max,

                j.employment_type,
                j.description,

                COALESCE(
                    sd.skills,
                    ''
                ) AS skills,

                s.overall_score,
                s.skill_score,
                s.tool_score,
                s.experience_score,
                s.salary_score,
                s.work_mode_score,
                s.score_breakdown,

                {search_score_expression}
                    AS search_score,

                {jd_match_expression}
                    AS jd_match,

                {title_match_expression}
                    AS title_match

            FROM fact_jobs j

            LEFT JOIN dim_company c
                ON j.company_id = c.company_id

            LEFT JOIN dim_location l
                ON j.location_id = l.location_id

            LEFT JOIN skill_data sd
                ON j.job_id = sd.job_id

            JOIN latest_scores s
                ON j.job_id = s.job_id

                AND s.rn = 1

            WHERE {where_clause}
        ),

        ranked_jobs AS (
            SELECT
                *,
                COUNT(*) OVER () AS filtered_total,

                ROW_NUMBER() OVER (
                    ORDER BY
                        {order_expression}
                ) AS global_rank

            FROM filtered_jobs
        )

        SELECT
            job_id,
            title,
            company,
            location,
            portal,

            job_url,
            posted_date,

            salary_min,
            salary_max,
            salary_currency,

            experience_min,
            experience_max,

            employment_type,
            description,
            skills,

            overall_score,
            skill_score,
            tool_score,
            experience_score,
            salary_score,
            work_mode_score,
            score_breakdown,

            search_score,
            global_rank,
            filtered_total

        FROM ranked_jobs

        ORDER BY
            global_rank

        LIMIT ?
        OFFSET ?
    """

    # ------------------------------------------------------------------
    # IMPORTANT:
    #
    # Search-score parameters are part of the SELECT expression and
    # therefore must be inserted BEFORE WHERE parameters.
    #
    # DuckDB positional parameters are consumed in textual SQL order.
    # ------------------------------------------------------------------

    final_params: list[object] = []

    final_params.extend(
        search_score_params
    )

    final_params.extend(params)

    offset = (
        (page - 1)
        * page_size
    )

    final_params.extend(
        [
            page_size,
            offset,
        ]
    )

    rows = db.execute(
        query,
        final_params,
    ).fetchall()

    jobs: list[JobWithScore] = []

    total = 0

    for row in rows:
        (
            job_id,
            title,
            company,
            location_value,
            portal_value,
            job_url,
            posted_date,
            salary_min,
            salary_max,
            salary_currency,
            experience_min,
            experience_max,
            employment_type,
            description,
            skills,
            overall_score,
            skill_score,
            tool_score,
            experience_score,
            salary_score,
            work_mode_score,
            raw_breakdown,
            search_score,
            global_rank,
            filtered_total,
        ) = row

        total = int(
            filtered_total or 0
        )

        # --------------------------------------------------------------
        # Score breakdown
        # --------------------------------------------------------------

        score_breakdown = None

        if raw_breakdown:
            breakdown = raw_breakdown

            if isinstance(
                breakdown,
                str,
            ):
                breakdown = json.loads(
                    breakdown
                )

            if isinstance(
                breakdown,
                dict,
            ):
                score_breakdown = (
                    ScoreBreakdown.model_validate(
                        breakdown
                    )
                )

        # --------------------------------------------------------------
        # Search explanation.
        #
        # Search is a filter, not the ranking engine.
        # --------------------------------------------------------------

        reasons: list[str] = []

        if normalized_search:
            keyword = (
                normalized_search.lower()
            )

            if keyword in (
                title or ""
            ).lower():
                reasons.append(
                    "Title keyword match"
                )

            if keyword in (
                company or ""
            ).lower():
                reasons.append(
                    "Company keyword match"
                )

            if keyword in (
                location_value or ""
            ).lower():
                reasons.append(
                    "Location keyword match"
                )

            if keyword in (
                skills or ""
            ).lower():
                reasons.append(
                    "Skill keyword match"
                )

            if keyword in (
                description or ""
            ).lower():
                reasons.append(
                    "Description keyword match"
                )

            if keyword in (
                portal_value or ""
            ).lower():
                reasons.append(
                    "Portal keyword match"
                )

        score_breakdown = _add_match_evidence(
            score_breakdown,
            profile_id,
        )

        jobs.append(
            JobWithScore(
                job_id=job_id,
                title=title or "",
                company=company or "",
                location=location_value,
                portal=portal_value,

                job_url=job_url,
                posted_date=posted_date,

                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency=salary_currency,

                experience_min=experience_min,
                experience_max=experience_max,

                employment_type=employment_type,

                skills=[
                    skill.strip()
                    for skill in skills.split(",")
                    if skill.strip()
                ]
                if skills
                else [],

                overall_score=overall_score,
                skill_score=skill_score,
                tool_score=tool_score,
                experience_score=experience_score,
                salary_score=salary_score,
                work_mode_score=work_mode_score,

                score_breakdown=score_breakdown,

                search_score=search_score,

                match_reason=reasons,

                rank=int(
                    global_rank
                ),
            )
        )

    return JobListResponse(
        total=total,
        page=page,
        page_size=page_size,
        jobs=jobs,
    )


@router.get("/jobs/filter-options")
async def get_job_filter_options(
    profile_id: str = Query(
        settings.default_profile
    ),
    db: DuckDBPyConnection = Depends(get_db),
) -> dict:
    """
    Return clean, profile-specific filter options.

    Sources:
      locations -> normalized city-level values
      skills    -> persisted matched_skills
      tools     -> persisted matched_tools

    Generic profile taxonomy is deliberately NOT used.
    """

    # --------------------------------------------------------
    # Locations
    # --------------------------------------------------------

    raw_locations = [
        row[0]
        for row in db.execute(
            """
            SELECT DISTINCT
                UPPER(
                    TRIM(
                        COALESCE(
                            l.canonical_name,
                            ''
                        )
                    )
                )
            FROM fact_jobs j
            LEFT JOIN dim_location l
                ON j.location_id = l.location_id
            JOIN fact_job_scores s
                ON j.job_id = s.job_id
               AND s.profile_id = ?
            WHERE l.canonical_name IS NOT NULL
              AND TRIM(l.canonical_name) <> ''
            """,
            [profile_id],
        ).fetchall()
    ]

    aliases = {
        "GURGAON": "GURUGRAM",
        "BANGALORE": "BENGALURU",
        "BANGALORE RURAL": "BENGALURU",
        "BENGALURU": "BENGALURU",
        "NEWDELHI": "NEW DELHI",
        "NEW DELHI": "NEW DELHI",
        "GANDHINAGAR": "GANDHI NAGAR",
        "GANDHI NAGAR": "GANDHI NAGAR",
        "DELHI / NCR": "DELHI",
        "DELHI/NCR": "DELHI",
    }

    locations: set[str] = set()

    for raw in raw_locations:
        if not raw:
            continue

        text = str(raw)

        text = re.sub(
            r"\bHYBRID\s*-\s*",
            "",
            text,
        )

        # Remove parenthetical area names:
        # GURUGRAM(SECTOR 48) -> GURUGRAM
        text = re.sub(
            r"\s*\([^)]*\)",
            "",
            text,
        )

        # A location string can contain multiple cities.
        # Keep each city as a separate selectable value.
        for token in text.split(","):
            city = re.sub(
                r"\s+",
                " ",
                token,
            ).strip()

            if not city:
                continue

            city = aliases.get(
                city,
                city,
            )

            if city in {
                "INDIA",
                "HARYANA",
                "UTTAR PRADESH",
                "UNITED STATES",
                "DAMAN & DIU",
                "LAKSHADWEEP",
                "DELHI / NCR",
                "DELHI/NCR",
            }:
                continue

            locations.add(city)

    # --------------------------------------------------------
    # Job-specific matched skills/tools
    # --------------------------------------------------------

    scored_rows = db.execute(
        """
        WITH latest AS (
            SELECT
                score_breakdown,
                ROW_NUMBER() OVER (
                    PARTITION BY job_id, profile_id
                    ORDER BY scored_at DESC
                ) AS rn
            FROM fact_job_scores
            WHERE profile_id = ?
        )
        SELECT score_breakdown
        FROM latest
        WHERE rn = 1
          AND score_breakdown IS NOT NULL
        """,
        [profile_id],
    ).fetchall()

    skills: dict[str, str] = {}
    tools: dict[str, str] = {}

    for (raw,) in scored_rows:
        try:
            breakdown = (
                json.loads(raw)
                if isinstance(raw, str)
                else raw
            )
        except Exception:
            continue

        for value in (
            breakdown.get(
                "matched_skills",
                [],
            )
            or []
        ):
            label = str(value).strip()
            if label:
                skills.setdefault(
                    label.lower(),
                    label,
                )

        for value in (
            breakdown.get(
                "matched_tools",
                [],
            )
            or []
        ):
            label = str(value).strip()
            if label:
                tools.setdefault(
                    label.lower(),
                    label,
                )

    # --------------------------------------------------------
    # Portals
    # --------------------------------------------------------

    portals = [
        row[0]
        for row in db.execute(
            """
            SELECT DISTINCT portal
            FROM fact_jobs
            WHERE portal IS NOT NULL
              AND TRIM(portal) <> ''
            ORDER BY portal
            """
        ).fetchall()
    ]

    return {
        "locations": sorted(
            locations,
            key=str.casefold,
        ),
        "skills": sorted(
            skills.values(),
            key=str.casefold,
        ),
        "tools": sorted(
            tools.values(),
            key=str.casefold,
        ),
        "portals": portals,
        "companies": [],
    }


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    profile_id: str = Query(
        settings.default_profile
    ),
    db: DuckDBPyConnection = Depends(get_db),
) -> JobDetail:
    """
    Return complete details for one job.
    """

    query = """
        WITH latest_score AS (
            SELECT
                job_id,
                profile_id,
                overall_score,
                skill_score,
                tool_score,
                experience_score,
                salary_score,
                work_mode_score,
                score_breakdown,
                scored_at,

                ROW_NUMBER() OVER (
                    PARTITION BY job_id, profile_id
                    ORDER BY scored_at DESC
                ) AS rn

            FROM fact_job_scores

            WHERE profile_id = ?
        )

        SELECT
            j.job_id,
            j.title,
            j.description,
            j.job_url,
            j.portal,

            j.salary_min,
            j.salary_max,
            j.salary_currency,

            j.experience_min,
            j.experience_max,

            j.employment_type,
            j.posted_date,

            c.canonical_name,
            l.canonical_name,

            s.overall_score,
            s.skill_score,
            s.tool_score,
            s.experience_score,
            s.salary_score,
            s.work_mode_score,
            s.score_breakdown,
            s.scored_at

        FROM fact_jobs j

        LEFT JOIN dim_company c
            ON j.company_id = c.company_id

        LEFT JOIN dim_location l
            ON j.location_id = l.location_id

        LEFT JOIN latest_score s
            ON j.job_id = s.job_id

            AND s.rn = 1

        WHERE j.job_id = ?
    """

    results = db.execute(
        query,
        [
            profile_id,
            job_id,
        ],
    ).fetchall()

    if not results:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Job '{job_id}' not found"
            ),
        )

    row = results[0]

    score = None

    if row[14] is not None:
        raw_breakdown = row[20]

        score_breakdown = None

        if raw_breakdown:
            if isinstance(
                raw_breakdown,
                str,
            ):
                score_breakdown = (
                    ScoreBreakdown.model_validate_json(
                        raw_breakdown
                    )
                )
            else:
                score_breakdown = (
                    ScoreBreakdown.model_validate(
                        raw_breakdown
                    )
                )

        score_breakdown = _add_match_evidence(
            score_breakdown,
            profile_id,
        )

        score = ScoreDetail(
            job_id=job_id,
            profile_id=profile_id,

            overall_score=row[14] or 0,
            skill_score=row[15] or 0,
            tool_score=row[16] or 0,
            experience_score=row[17] or 0,
            salary_score=row[18] or 0,
            work_mode_score=row[19] or 0,

            score_breakdown=score_breakdown,

            scored_at=row[21],
        )

    return JobDetail(
        job_id=row[0],
        title=row[1] or "",

        company=row[12] or "",
        location=row[13] or "",

        portal=row[4] or "",

        description=row[2] or "",
        job_url=row[3] or "",

        salary_min=row[5],
        salary_max=row[6],
        salary_currency=row[7],

        experience_min=row[8],
        experience_max=row[9],

        employment_type=row[10] or "",
        posted_date=row[11],

        score=score,

        search_score=None,
        match_reason=[],
    )
