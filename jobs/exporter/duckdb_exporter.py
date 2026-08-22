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
                search_id VARCHAR
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

        conn.executemany(
            """
            INSERT OR IGNORE INTO dim_company (
                company_id,
                canonical_name,
                created_at
            ) VALUES (?, ?, ?)
            """,
            data,
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

        conn.executemany(
            """
            INSERT OR IGNORE INTO dim_location (
                location_id,
                canonical_name,
                created_at
            ) VALUES (?, ?, ?)
            """,
            data,
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

        conn.executemany(
            """
            INSERT OR IGNORE INTO dim_skill (
                skill_id,
                name,
                created_at
            ) VALUES (?, ?, ?)
            """,
            data,
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

        conn.executemany(
            """
            INSERT OR REPLACE INTO fact_jobs (
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
                search_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

        if not bridge_rows:
            return

        conn.executemany(
            """
            INSERT OR IGNORE INTO fact_jobs_skills (
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