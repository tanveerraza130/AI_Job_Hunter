"""
File:
    duckdb_exporter.py

Version:
    4.0.0

Phase:
    6

Status:
    FROZEN

Purpose:
    Export jobs to DuckDB database.

Responsibilities:
    - Create DuckDB database if missing
    - Create required tables if missing
    - Insert jobs using deterministic IDs from identity layer
    - Use bulk operations for performance
    - Use transactions for atomicity

Dependencies:
    - duckdb
    - pathlib: Path
    - datetime: datetime
    - jobs.exporter.base: BaseExporter
    - jobs.job: Job
    - jobs.identity.normalizer: Normalizer
    - jobs.identity.resolver: CompanyResolver

This module does NOT:
    - Normalize data (uses identity layer)
    - Validate jobs
    - Deduplicate
    - Use pandas
    - Use SQLAlchemy
    - Use UUIDs
    - Create extra folders
    - Create repository layers
    - Create service layers
    - Create ETL layers

PEP8:     Yes
SOLID:    Yes (Single Responsibility)
DRY:      Yes
KISS:     Yes
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import duckdb

from jobs.enums import ExportFormat
from jobs.exporter.base import BaseExporter
from jobs.identity.normalizer import Normalizer
from jobs.identity.resolver import CompanyResolver
from jobs.job import Job


class DuckDBExporter(BaseExporter):
    """
    DuckDB exporter implementation.

    Exports Job objects to DuckDB database with star schema.

    Methods:
        export: Export jobs to DuckDB database.
    """

    EXPORT_FORMAT = ExportFormat.DUCKDB

    def _create_tables(self, conn: duckdb.DuckDBPyConnection) -> None:
        """
        Create required tables if they don't exist.

        Args:
            conn: DuckDB connection.
        """
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dim_company (
                company_id VARCHAR PRIMARY KEY,
                canonical_name VARCHAR,
                created_at TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS dim_location (
                location_id VARCHAR PRIMARY KEY,
                canonical_name VARCHAR,
                created_at TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS dim_skill (
                skill_id VARCHAR PRIMARY KEY,
                name VARCHAR UNIQUE,
                created_at TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS fact_jobs (
                job_id VARCHAR PRIMARY KEY,
                title VARCHAR,
                company_id VARCHAR,
                location_id VARCHAR,
                salary_min INTEGER,
                salary_max INTEGER,
                salary_currency VARCHAR,
                description TEXT,
                job_url VARCHAR,
                portal VARCHAR,
                posted_date DATE,
                experience_min INTEGER,
                experience_max INTEGER,
                employment_type VARCHAR,
                created_at TIMESTAMP,
                search_id VARCHAR,
                is_active BOOLEAN DEFAULT TRUE,
                last_seen_at TIMESTAMP,
                url_status VARCHAR DEFAULT 'unknown',
                url_checked_at TIMESTAMP,
                reported_dead_count INTEGER DEFAULT 0
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS fact_jobs_skills (
                job_id VARCHAR,
                skill_id VARCHAR,
                PRIMARY KEY (job_id, skill_id)
            )
        """)

    def _insert_companies(
        self,
        conn: duckdb.DuckDBPyConnection,
        companies: set[str],
        created_at: datetime,
    ) -> None:
        """
        Insert companies into dim_company.

        Args:
            conn: DuckDB connection.
            companies: Set of canonical company names.
            created_at: Consistent timestamp for this export.
        """
        if not companies:
            return

        data = [(c, c, created_at) for c in companies]

        placeholders = ", ".join("?" for _ in data)
        existing_ids = {
            row[0]
            for row in conn.execute(
                f"""
                SELECT company_id
                FROM dim_company
                WHERE company_id IN ({placeholders})
                """,
                [row[0] for row in data],
            ).fetchall()
        }

        missing_data = [
            row for row in data
            if row[0] not in existing_ids
        ]

        if missing_data:
            conn.executemany(
                """
                INSERT INTO dim_company (
                    company_id,
                    canonical_name,
                    created_at
                ) VALUES (?, ?, ?)
                """,
                missing_data,
            )

    def _insert_locations(
        self,
        conn: duckdb.DuckDBPyConnection,
        locations: set[str],
        created_at: datetime,
    ) -> None:
        """
        Insert locations into dim_location.

        Args:
            conn: DuckDB connection.
            locations: Set of canonical location names.
            created_at: Consistent timestamp for this export.
        """
        if not locations:
            return

        data = [(l, l, created_at) for l in locations]

        placeholders = ", ".join("?" for _ in data)
        existing_ids = {
            row[0]
            for row in conn.execute(
                f"""
                SELECT location_id
                FROM dim_location
                WHERE location_id IN ({placeholders})
                """,
                [row[0] for row in data],
            ).fetchall()
        }

        missing_data = [
            row for row in data
            if row[0] not in existing_ids
        ]

        if missing_data:
            conn.executemany(
                """
                INSERT INTO dim_location (
                    location_id,
                    canonical_name,
                    created_at
                ) VALUES (?, ?, ?)
                """,
                missing_data,
            )

    def _insert_skills(
        self,
        conn: duckdb.DuckDBPyConnection,
        skills: set[str],
        created_at: datetime,
    ) -> None:
        """
        Insert skills into dim_skill.

        Args:
            conn: DuckDB connection.
            skills: Set of normalized skill names.
            created_at: Consistent timestamp for this export.
        """
        if not skills:
            return

        data = [(s, s, created_at) for s in skills]

        placeholders = ", ".join("?" for _ in data)
        existing_ids = {
            row[0]
            for row in conn.execute(
                f"""
                SELECT skill_id
                FROM dim_skill
                WHERE skill_id IN ({placeholders})
                """,
                [row[0] for row in data],
            ).fetchall()
        }

        missing_data = [
            row for row in data
            if row[0] not in existing_ids
        ]

        if missing_data:
            conn.executemany(
                """
                INSERT INTO dim_skill (
                    skill_id,
                    name,
                    created_at
                ) VALUES (?, ?, ?)
                """,
                missing_data,
            )

    def _insert_jobs(
        self,
        conn: duckdb.DuckDBPyConnection,
        jobs: list[Job],
        resolver: CompanyResolver,
        normalizer: Normalizer,
        created_at: datetime,
    ) -> None:
        """
        Insert jobs into fact_jobs.

        Args:
            conn: DuckDB connection.
            jobs: List of Job objects.
            resolver: CompanyResolver instance.
            normalizer: Normalizer instance.
            created_at: Consistent timestamp for this export.

        Raises:
            RuntimeError: If any job has an empty job_id.
        """
        if not jobs:
            return

        fact_rows = []

        for job in jobs:
            if not job.portal or not job.job_id:
                raise RuntimeError(
                    f"Job missing portal or job_id: title='{job.title}', company='{job.company}'"
                )

            job_id = f"{job.portal}:{job.job_id}"

            fact_rows.append((
                job_id,
                job.title or "",
                resolver.resolve(job.company),
                normalizer.normalize_location(job.location),
                job.salary_min,
                job.salary_max,
                job.salary_currency,
                job.description or "",
                job.job_url or "",
                job.portal,
                job.posted_date,
                job.experience_min,
                job.experience_max,
                normalizer.normalize_employment_type(job.employment_type),
                created_at,
                None,  # search_id - reserved for future
            ))

        # Preserve the existing production fact_jobs schema, which does
        # not require a PRIMARY KEY/UNIQUE constraint. Implement the
        # existing INSERT OR REPLACE intent explicitly: remove any
        # previously persisted rows with the same deterministic IDs,
        # then insert the current rows within the surrounding transaction.
        # UPSERT: preserve row (and its liveness metadata) if job_id exists,
        # otherwise insert as new. last_seen_at is always refreshed.
        # is_active is forced TRUE on upsert (a job returned by the pipeline
        # is by definition still alive in the source portal).
        conn.executemany(
            """
            INSERT INTO fact_jobs (
                job_id,
                title,
                company_id,
                location_id,
                salary_min,
                salary_max,
                salary_currency,
                description,
                job_url,
                portal,
                posted_date,
                experience_min,
                experience_max,
                employment_type,
                created_at,
                search_id,
                is_active,
                last_seen_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE, NOW())
            ON CONFLICT (job_id) DO UPDATE SET
                title = EXCLUDED.title,
                company_id = EXCLUDED.company_id,
                location_id = EXCLUDED.location_id,
                salary_min = EXCLUDED.salary_min,
                salary_max = EXCLUDED.salary_max,
                salary_currency = EXCLUDED.salary_currency,
                description = EXCLUDED.description,
                job_url = EXCLUDED.job_url,
                portal = EXCLUDED.portal,
                posted_date = EXCLUDED.posted_date,
                experience_min = EXCLUDED.experience_min,
                experience_max = EXCLUDED.experience_max,
                employment_type = EXCLUDED.employment_type,
                search_id = EXCLUDED.search_id,
                is_active = TRUE,
                last_seen_at = NOW()
            """,
            fact_rows,
        )

    def _insert_job_skills(
        self,
        conn: duckdb.DuckDBPyConnection,
        jobs: list[Job],
        normalizer: Normalizer,
    ) -> None:
        """
        Insert job-skill relationships into fact_jobs_skills.

        Args:
            conn: DuckDB connection.
            jobs: List of Job objects.
            normalizer: Normalizer instance.
        """
        if not jobs:
            return

        bridge_rows = []

        for job in jobs:
            if not job.portal or not job.job_id:
                continue

            job_id = f"{job.portal}:{job.job_id}"
            skills = normalizer.normalize_skills(job.skills)

            for skill in skills:
                bridge_rows.append((job_id, skill))

        # Keep the bridge synchronized with the current exported job
        # state. Remove relationships for every exported job first,
        # including jobs whose current skill list is empty. Then insert
        # only the current skill relationships.
        exported_job_ids = list({
            f"{job.portal}:{job.job_id}"
            for job in jobs
            if job.portal and job.job_id
        })

        if not exported_job_ids:
            return

        placeholders = ", ".join("?" for _ in exported_job_ids)

        conn.execute(
            f"""
            DELETE FROM fact_jobs_skills
            WHERE job_id IN ({placeholders})
            """,
            exported_job_ids,
        )

        if bridge_rows:
            conn.executemany(
                """
                INSERT INTO fact_jobs_skills (
                    job_id,
                    skill_id
                ) VALUES (?, ?)
                """,
                bridge_rows,
            )

    def _collect_dimensions(
        self,
        jobs: list[Job],
        resolver: CompanyResolver,
        normalizer: Normalizer,
    ) -> tuple[set[str], set[str], set[str]]:
        """
        Collect unique dimension values from jobs.

        Args:
            jobs: List of Job objects.
            resolver: CompanyResolver instance.
            normalizer: Normalizer instance.

        Returns:
            tuple[set[str], set[str], set[str]]: (companies, locations, skills)
        """
        companies: set[str] = set()
        locations: set[str] = set()
        skills: set[str] = set()

        for job in jobs:
            if job.company:
                companies.add(resolver.resolve(job.company))
            if job.location:
                locations.add(normalizer.normalize_location(job.location))
            if job.skills:
                skills.update(normalizer.normalize_skills(job.skills))

        return companies, locations, skills

    def export(
        self,
        jobs: list[Job],
        destination: Path,
    ) -> None:
        """
        Export jobs to DuckDB database.

        Creates parent directories if they don't exist.
        Creates tables if they don't exist.
        Uses deterministic IDs from identity layer.
        Uses bulk operations for performance.

        Args:
            jobs: List of Job objects to export.
            destination: Path to DuckDB database file.

        Raises:
            RuntimeError: If export fails.
        """
        if not jobs:
            return

        # Reuse identity objects once per export
        resolver = CompanyResolver()
        normalizer = Normalizer()

        # Consistent timestamp for all rows in this export
        created_at = datetime.now()

        try:
            destination.parent.mkdir(parents=True, exist_ok=True)

            with duckdb.connect(str(destination)) as conn:
                conn.execute("BEGIN")

                try:
                    self._create_tables(conn)

                    # Collect and insert dimensions
                    companies, locations, skills = self._collect_dimensions(
                        jobs,
                        resolver,
                        normalizer,
                    )

                    self._insert_companies(conn, companies, created_at)
                    self._insert_locations(conn, locations, created_at)
                    self._insert_skills(conn, skills, created_at)

                    # Insert facts
                    self._insert_jobs(conn, jobs, resolver, normalizer, created_at)

                    # Insert bridge
                    self._insert_job_skills(conn, jobs, normalizer)

                    conn.execute("COMMIT")

                except Exception:
                    conn.execute("ROLLBACK")
                    raise

        except (duckdb.Error, OSError, RuntimeError) as e:
            raise RuntimeError(
                f"Failed to export to DuckDB at {destination}: {e}"
            ) from e


# =============================================================================
# END OF FILE
# =============================================================================