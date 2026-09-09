"""
End-to-end tests for the isolated LinkedIn Hiring Posts processing path.
"""

from __future__ import annotations

from datetime import UTC, datetime

import duckdb

from jobs.linkedin_posts.parser import LinkedInHiringPostParser
from jobs.linkedin_posts.processor import LinkedInHiringPostProcessor
from jobs.linkedin_posts.repository import LinkedInHiringPostRepository


class FakeResponse:
    """Minimal requests response replacement."""

    status_code = 200

    def __init__(self, text: str) -> None:
        self.text = text


class FakeSession:
    """Minimal network-free session for the parser."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.headers: dict[str, str] = {}

    def get(self, url: str, **kwargs):
        return FakeResponse(self.text)


def _schema(connection: duckdb.DuckDBPyConnection) -> None:
    """Create only the isolated LinkedIn Hiring Posts table."""
    connection.execute(
        """
        CREATE TABLE linkedin_hiring_posts (
            post_id VARCHAR PRIMARY KEY,
            post_url VARCHAR NOT NULL,
            portal VARCHAR NOT NULL DEFAULT 'linkedin_post',
            author_name VARCHAR,
            author_url VARCHAR,
            author_headline VARCHAR,
            text TEXT NOT NULL,
            posted_at TIMESTAMP,
            company VARCHAR,
            company_url VARCHAR,
            location VARCHAR,
            role VARCHAR,
            application_url VARCHAR,
            contact_email VARCHAR,
            discovery_query VARCHAR,
            discovered_at TIMESTAMP NOT NULL,
            relevance_score DOUBLE NOT NULL DEFAULT 0,
            raw JSON
        )
        """
    )


def test_parse_process_and_persist_hiring_post():
    """A parsed qualifying post survives the complete isolated pipeline."""
    html = """
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@id": "https://www.linkedin.com/posts/example-activity-987654321/",
      "@type": "SocialMediaPosting",
      "headline": "We are hiring a CRM Manager in Gurgaon.",
      "datePublished": "2026-09-09T18:00:00.000Z",
      "author": {
        "@type": "Person",
        "name": "Test Recruiter",
        "url": "https://www.linkedin.com/in/test-recruiter"
      },
      "articleBody": "We are hiring a CRM Manager in Gurgaon. Apply now! #hiring"
    }
    </script>
    """

    parser = LinkedInHiringPostParser(
        session=FakeSession(html),
    )

    post = parser.parse(
        "https://www.linkedin.com/posts/example-activity-987654321/",
        discovery_query='"CRM Manager" AND hiring',
    )

    assert post is not None
    assert post.post_id == "activity:987654321"
    assert post.portal == "linkedin_post"
    assert post.author_name == "Test Recruiter"
    assert post.text.startswith("We are hiring a CRM Manager")
    assert post.posted_at == datetime(
        2026,
        9,
        9,
        18,
        0,
        tzinfo=UTC,
    )
    assert post.discovery_query == '"CRM Manager" AND hiring'

    processor = LinkedInHiringPostProcessor(
        now=datetime(
            2026,
            9,
            9,
            20,
            0,
            tzinfo=UTC,
        ),
        max_age_hours=48,
    )

    processed = processor.process(post)

    assert processed is not None
    assert processed.post_id == post.post_id
    assert processed.relevance_score > 0.0
    assert post.relevance_score == 0.0

    connection = duckdb.connect(":memory:")
    try:
        _schema(connection)

        repository = LinkedInHiringPostRepository(connection)

        assert repository.insert_or_ignore(processed) is True
        assert repository.insert_or_ignore(processed) is False

        stored = repository.get(processed.post_id)

        assert stored is not None
        assert stored.post_id == processed.post_id
        assert stored.portal == "linkedin_post"
        assert stored.post_url == processed.post_url
        assert stored.author_name == processed.author_name
        assert stored.text == processed.text
        assert stored.posted_at == processed.posted_at
        assert stored.discovery_query == processed.discovery_query
        assert stored.relevance_score == processed.relevance_score
        assert stored.raw == processed.raw

        count = connection.execute(
            "SELECT COUNT(*) FROM linkedin_hiring_posts"
        ).fetchone()[0]

        assert count == 1
    finally:
        connection.close()
