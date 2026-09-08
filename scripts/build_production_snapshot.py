#!/usr/bin/env python3
"""
Build production and minimal DuckDB snapshots from the Master DB.

Production scope:
    Jobs posted within the rolling last 30 calendar days.

Flow:
    Master DB
        ↓
    30-day production snapshot
        ↓
    Minimal snapshot

The Master DB is NEVER modified.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_MASTER_DB = PROJECT_ROOT / "output" / "job_hunter.duckdb"
DEFAULT_PRODUCTION_DB = PROJECT_ROOT / "output" / "job_hunter_production.duckdb"
DEFAULT_MINIMAL_DB = PROJECT_ROOT / "output" / "job_hunter_production_minimal.duckdb"


def build_production_snapshot(master_db: Path, production_db: Path) -> None:
    """Build the rolling 30-day production database."""

    source = duckdb.connect(
        str(master_db),
        read_only=True,
    )

    target = duckdb.connect(
        str(production_db),
    )

    try:
        target.execute(
            f"ATTACH '{master_db}' AS source_db (READ_ONLY)"
        )

        print("Creating production job set...")

        target.execute("""
            CREATE TEMP TABLE production_job_ids AS
            SELECT job_id
            FROM source_db.fact_jobs
            WHERE posted_date >= CURRENT_DATE - INTERVAL 29 DAY
        """)

        production_jobs = target.execute("""
            SELECT COUNT(*)
            FROM production_job_ids
        """).fetchone()[0]

        print(f"  ✓ Production jobs: {production_jobs:,}")

        # ---------------------------------------------------------
        # Dimensions
        # ---------------------------------------------------------

        print("Copying dim_company...")

        target.execute("""
            CREATE TABLE dim_company AS
            SELECT DISTINCT c.*
            FROM source_db.dim_company c
            INNER JOIN source_db.fact_jobs j
                ON j.company_id = c.company_id
            INNER JOIN production_job_ids p
                ON p.job_id = j.job_id
        """)

        print(
            f"  ✓ {target.execute('SELECT COUNT(*) FROM dim_company').fetchone()[0]:,} rows"
        )

        print("Copying dim_location...")

        target.execute("""
            CREATE TABLE dim_location AS
            SELECT DISTINCT l.*
            FROM source_db.dim_location l
            INNER JOIN source_db.fact_jobs j
                ON j.location_id = l.location_id
            INNER JOIN production_job_ids p
                ON p.job_id = j.job_id
        """)

        print(
            f"  ✓ {target.execute('SELECT COUNT(*) FROM dim_location').fetchone()[0]:,} rows"
        )

        print("Copying dim_skill...")

        target.execute("""
            CREATE TABLE dim_skill AS
            SELECT DISTINCT s.*
            FROM source_db.dim_skill s
            INNER JOIN source_db.fact_jobs_skills js
                ON js.skill_id = s.skill_id
            INNER JOIN production_job_ids p
                ON p.job_id = js.job_id
        """)

        print(
            f"  ✓ {target.execute('SELECT COUNT(*) FROM dim_skill').fetchone()[0]:,} rows"
        )

        # ---------------------------------------------------------
        # Jobs
        # ---------------------------------------------------------

        print("Copying fact_jobs...")

        target.execute("""
            CREATE TABLE fact_jobs AS
            SELECT j.*
            FROM source_db.fact_jobs j
            INNER JOIN production_job_ids p
                ON p.job_id = j.job_id
        """)

        print(
            f"  ✓ {target.execute('SELECT COUNT(*) FROM fact_jobs').fetchone()[0]:,} rows"
        )

        # ---------------------------------------------------------
        # Scores
        # ---------------------------------------------------------

        print("Copying fact_job_scores...")

        target.execute("""
            CREATE TABLE fact_job_scores AS
            SELECT s.*
            FROM source_db.fact_job_scores s
            INNER JOIN production_job_ids p
                ON p.job_id = s.job_id
        """)

        print(
            f"  ✓ {target.execute('SELECT COUNT(*) FROM fact_job_scores').fetchone()[0]:,} rows"
        )

        # ---------------------------------------------------------
        # Skills
        # ---------------------------------------------------------

        print("Copying fact_jobs_skills...")

        target.execute("""
            CREATE TABLE fact_jobs_skills AS
            SELECT js.*
            FROM source_db.fact_jobs_skills js
            INNER JOIN production_job_ids p
                ON p.job_id = js.job_id
        """)

        print(
            f"  ✓ {target.execute('SELECT COUNT(*) FROM fact_jobs_skills').fetchone()[0]:,} rows"
        )

        # ---------------------------------------------------------
        # Registry
        # ---------------------------------------------------------

        print("Copying job_registry...")

        target.execute("""
            CREATE TABLE job_registry AS
            SELECT DISTINCT r.*
            FROM source_db.job_registry r
            INNER JOIN source_db.fact_jobs j
                ON r.portal = j.portal
               AND r.portal_job_id = split_part(j.job_id, ':', 2)
            INNER JOIN production_job_ids p
                ON p.job_id = j.job_id
        """)

        registry_count = target.execute(
            "SELECT COUNT(*) FROM job_registry"
        ).fetchone()[0]

        print(f"  ✓ {registry_count:,} rows")

        # ---------------------------------------------------------
        # Search sessions
        #
        # Keep recent sessions associated with the production period.
        # ---------------------------------------------------------

        print("Copying search_session...")

        target.execute("""
            CREATE TABLE search_session AS
            SELECT *
            FROM source_db.search_session
            WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL 30 DAY
        """)

        session_count = target.execute(
            "SELECT COUNT(*) FROM search_session"
        ).fetchone()[0]

        print(f"  ✓ {session_count:,} rows")

        target.execute("DETACH source_db")

    finally:
        source.close()
        target.close()


def build_minimal_snapshot(production_db: Path, minimal_db: Path) -> None:
    """Build the GitHub/minimal snapshot from production."""

    source = duckdb.connect(
        str(production_db),
        read_only=True,
    )

    target = duckdb.connect(
        str(minimal_db),
    )

    try:
        target.execute(
            f"ATTACH '{production_db}' AS production_db (READ_ONLY)"
        )

        tables = [
            "dim_company",
            "dim_location",
            "dim_skill",
            "fact_job_scores",
            "fact_jobs",
            "fact_jobs_skills",
            "job_registry",
            "search_session",
        ]

        for table in tables:
            print(f"Copying {table} to minimal DB...")

            target.execute(
                f'''
                CREATE TABLE "{table}" AS
                SELECT *
                FROM production_db."{table}"
                '''
            )

            count = target.execute(
                f'SELECT COUNT(*) FROM "{table}"'
            ).fetchone()[0]

            print(f"  ✓ {count:,} rows")

        target.execute("DETACH production_db")

    finally:
        source.close()
        target.close()


def validate_database(
    path: Path,
    expected_jobs: int | None = None,
) -> None:
    """Validate a generated database."""
    print()
    print("=" * 70)
    print(f"VALIDATING: {path.name}")
    print("=" * 70)

    con = duckdb.connect(
        str(path),
        read_only=True,
    )

    jobs = con.execute(
        "SELECT COUNT(*) FROM fact_jobs"
    ).fetchone()[0]

    scores = con.execute(
        "SELECT COUNT(*) FROM fact_job_scores"
    ).fetchone()[0]

    skills = con.execute(
        "SELECT COUNT(*) FROM fact_jobs_skills"
    ).fetchone()[0]

    print(f"fact_jobs          {jobs:,}")
    print(f"fact_job_scores    {scores:,}")
    print(f"fact_jobs_skills   {skills:,}")

    if expected_jobs is not None and jobs != expected_jobs:
        raise RuntimeError(
            f"{path.name}: expected {expected_jobs:,} jobs, found {jobs:,}"
        )

    # Referential integrity checks.
    orphan_scores = con.execute("""
        SELECT COUNT(*)
        FROM fact_job_scores s
        LEFT JOIN fact_jobs j
            ON j.job_id = s.job_id
        WHERE j.job_id IS NULL
    """).fetchone()[0]

    orphan_skills = con.execute("""
        SELECT COUNT(*)
        FROM fact_jobs_skills s
        LEFT JOIN fact_jobs j
            ON j.job_id = s.job_id
        WHERE j.job_id IS NULL
    """).fetchone()[0]

    if orphan_scores:
        raise RuntimeError(
            f"{path.name}: {orphan_scores:,} orphan score records"
        )

    if orphan_skills:
        raise RuntimeError(
            f"{path.name}: {orphan_skills:,} orphan skill records"
        )

    print("✓ Referential integrity PASS")

    con.close()

    print(f"✓ {path.name} validation PASS")


def main() -> int:
    """Build and validate production snapshots."""

    import argparse

    parser = argparse.ArgumentParser(
        description="Build rolling 30-day production and minimal snapshots."
    )
    parser.add_argument(
        "--master-db",
        type=Path,
        default=DEFAULT_MASTER_DB,
        help="Source Master DuckDB.",
    )
    parser.add_argument(
        "--production-db",
        type=Path,
        default=DEFAULT_PRODUCTION_DB,
        help="Production snapshot DuckDB.",
    )
    parser.add_argument(
        "--minimal-db",
        type=Path,
        default=DEFAULT_MINIMAL_DB,
        help="Minimal snapshot DuckDB.",
    )

    args = parser.parse_args()

    master_db = args.master_db.resolve()
    production_db = args.production_db.resolve()
    minimal_db = args.minimal_db.resolve()

    if not master_db.exists():
        raise FileNotFoundError(
            f"Master DB not found: {master_db}"
        )

    production_db.parent.mkdir(parents=True, exist_ok=True)
    minimal_db.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("AI JOB HUNTER — 30-DAY PRODUCTION SNAPSHOT")
    print("=" * 70)

    print()
    print("Master DB:")
    print(f"  {master_db}")
    print(
        f"  {master_db.stat().st_size / 1024 / 1024:.2f} MB"
    )

    print()
    print("===== BUILD SNAPSHOT CANDIDATES =====")

    with TemporaryDirectory(
        prefix="ai_job_hunter_snapshot_",
        dir=production_db.parent,
    ) as temp_dir:
        temp_root = Path(temp_dir)
        production_candidate = temp_root / production_db.name
        minimal_candidate = temp_root / minimal_db.name

        print()
        print("Building production candidate...")
        build_production_snapshot(
            master_db,
            production_candidate,
        )

        production_con = duckdb.connect(
            str(production_candidate),
            read_only=True,
        )
        production_jobs = production_con.execute(
            "SELECT COUNT(*) FROM fact_jobs"
        ).fetchone()[0]
        production_con.close()

        print()
        print("Building minimal candidate...")
        build_minimal_snapshot(
            production_candidate,
            minimal_candidate,
        )

        print()
        print("===== VALIDATION =====")

        validate_database(
            production_candidate,
            expected_jobs=production_jobs,
        )

        validate_database(
            minimal_candidate,
            expected_jobs=production_jobs,
        )

        print()
        print("===== PROMOTE VALIDATED SNAPSHOTS =====")

        production_candidate.replace(production_db)
        print(f"✓ Promoted production snapshot: {production_db}")

        minimal_candidate.replace(minimal_db)
        print(f"✓ Promoted minimal snapshot: {minimal_db}")

    print()
    print("=" * 70)
    print("30-DAY SNAPSHOT BUILD COMPLETE")
    print("=" * 70)

    print()
    print("Production DB:")
    print(f"  {production_db}")
    print(
        f"  {production_db.stat().st_size / 1024 / 1024:.2f} MB"
    )

    print("Minimal DB:")
    print(f"  {minimal_db}")
    print(
        f"  {minimal_db.stat().st_size / 1024 / 1024:.2f} MB"
    )

    print()
    print("✓ Master DB was read-only")
    print("✓ Production = rolling last 30 days")
    print("✓ Minimal = Production snapshot")
    print("✓ Referential integrity passed")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
