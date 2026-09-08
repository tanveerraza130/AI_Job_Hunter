"""
Tests for the isolated LinkedIn Hiring Posts repository.

These tests use an in-memory DuckDB database and the isolated
jobs/linkedin_posts/schema.sql. They must not touch the existing
job storage schema or production database.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pytest

from jobs.linkedin_posts.models import LinkedInHiringPost


class TestLinkedInHiringPostRepository:
    """Contract tests for the LinkedIn Hiring Posts repository."""

    @pytest.fixture
    def conn(self):
        """Create an isolated in-memory DuckDB connection."""
        conn = duckdb.connect(":memory:")

        schema_path = (
            Path(__file__).resolve().parents[2]
            / "linkedin_posts"
            / "schema.sql"
        )

        schema_sql = schema_path.read_text(encoding="utf-8")
        conn.execute(schema_sql)

        yield conn
        conn.close()

    @pytest.fixture
    def post(self):
        """Create a representative normalized hiring post."""
        return LinkedInHiringPost(
            post_id="activity:123456789",
            post_url="https://www.linkedin.com/posts/example",
            author_name="Test Recruiter",
            author_url="https://www.linkedin.com/in/test-recruiter",
            author_headline="Talent Acquisition",
            text="We are hiring a CRM Manager in Gurgaon.",
            posted_at=datetime(2026, 9, 8, 10, 0, tzinfo=UTC),
            company="Test Corp",
            company_url="https://www.linkedin.com/company/test-corp",
            location="Gurgaon",
            role="CRM Manager",
            application_url="https://example.com/apply",
            contact_email="jobs@example.com",
            discovery_query='"CRM Manager" AND hiring',
            discovered_at=datetime.now(UTC),
            relevance_score=0.95,
            raw={"source": "test"},
        )

    def test_insert_and_get_contract(self, conn, post):
        """A post can be inserted and retrieved by stable post ID."""
        from jobs.linkedin_posts.repository import LinkedInHiringPostRepository

        repo = LinkedInHiringPostRepository(conn)

        inserted = repo.insert_or_ignore(post)

        assert inserted is True
        assert repo.exists(post.post_id) is True

        result = repo.get(post.post_id)

        assert result is not None
        assert result.post_id == post.post_id
        assert result.post_url == post.post_url
        assert result.author_name == post.author_name
        assert result.text == post.text
        assert result.company == post.company
        assert result.location == post.location
        assert result.role == post.role
        assert result.application_url == post.application_url
        assert result.contact_email == post.contact_email
        assert result.discovery_query == post.discovery_query
        assert result.relevance_score == post.relevance_score

    def test_duplicate_post_id_is_ignored(self, conn, post):
        """The stable LinkedIn post ID prevents duplicate persistence."""
        from jobs.linkedin_posts.repository import LinkedInHiringPostRepository

        repo = LinkedInHiringPostRepository(conn)

        assert repo.insert_or_ignore(post) is True
        assert repo.insert_or_ignore(post) is False

        count = conn.execute(
            "SELECT COUNT(*) FROM linkedin_hiring_posts"
        ).fetchone()[0]

        assert count == 1

    def test_missing_post_returns_none(self, conn):
        """Unknown post IDs return None."""
        from jobs.linkedin_posts.repository import LinkedInHiringPostRepository

        repo = LinkedInHiringPostRepository(conn)

        assert repo.exists("activity:does-not-exist") is False
        assert repo.get("activity:does-not-exist") is None

    def test_raw_json_round_trip(self, conn, post):
        """Raw discovery payload survives persistence and retrieval."""
        from jobs.linkedin_posts.repository import LinkedInHiringPostRepository

        repo = LinkedInHiringPostRepository(conn)

        repo.insert_or_ignore(post)

        result = repo.get(post.post_id)

        assert result is not None
        assert result.raw == {"source": "test"}

    def test_database_contains_only_isolated_table(self, conn):
        """The isolated test database contains no existing job tables."""
        tables = conn.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
            ORDER BY table_name
            """
        ).fetchall()

        assert tables == [("linkedin_hiring_posts",)]
