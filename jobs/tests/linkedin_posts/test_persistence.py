from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import duckdb

from jobs.linkedin_posts.models import LinkedInHiringPost
from jobs.linkedin_posts.persistence import initialize_linkedin_hiring_posts


def test_initialize_creates_schema_and_returns_repository():
    connection = duckdb.connect(":memory:")

    try:
        repository = initialize_linkedin_hiring_posts(connection)

        tables = connection.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
              AND table_name = 'linkedin_hiring_posts'
            """
        ).fetchall()

        assert tables == [("linkedin_hiring_posts",)]
        assert not repository.exists("activity:123")
    finally:
        connection.close()


def test_initialize_is_idempotent_on_existing_schema():
    connection = duckdb.connect(":memory:")

    try:
        first = initialize_linkedin_hiring_posts(connection)
        second = initialize_linkedin_hiring_posts(connection)

        post = LinkedInHiringPost(
            post_id="activity:123",
            post_url="https://www.linkedin.com/posts/example-123/",
            text="We're hiring a CRM Manager in Gurgaon.",
            posted_at=datetime(2026, 9, 9, 10, 0, tzinfo=UTC),
            company="Example Co",
            location="Gurgaon",
            role="CRM Manager",
            discovered_at=datetime(2026, 9, 9, 11, 0, tzinfo=UTC),
            relevance_score=0.95,
        )

        assert first.insert_or_ignore(post) is True
        assert second.exists("activity:123") is True

        stored = second.get("activity:123")

        assert stored is not None
        assert stored.post_id == "activity:123"
        assert stored.company == "Example Co"
        assert stored.role == "CRM Manager"
    finally:
        connection.close()

def test_initialize_works_with_master_db_copy(tmp_path):
    """LinkedIn schema can coexist with the real Master DB schema."""
    master_db = Path("output/job_hunter.duckdb")
    test_db = tmp_path / "job_hunter_master_copy.duckdb"

    test_db.write_bytes(master_db.read_bytes())

    connection = duckdb.connect(str(test_db))

    try:
        repository = initialize_linkedin_hiring_posts(connection)

        assert repository is not None

        assert connection.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'main'
              AND table_name = 'linkedin_hiring_posts'
            """
        ).fetchone()[0] == 1

        job_count = connection.execute(
            "SELECT COUNT(*) FROM fact_jobs"
        ).fetchone()[0]

        assert job_count > 0
    finally:
        connection.close()
