"""
Tests for the isolated LinkedIn Hiring Posts parser.
"""

from __future__ import annotations

from datetime import UTC

from jobs.linkedin_posts.parser import LinkedInHiringPostParser


class FakeResponse:
    """Minimal requests response replacement."""

    status_code = 200

    def __init__(self, text: str) -> None:
        self.text = text


class FakeSession:
    """Minimal session used to test parsing without network access."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.headers: dict[str, str] = {}
        self.requested_url: str | None = None

    def get(self, url: str, **kwargs):
        self.requested_url = url
        return FakeResponse(self.text)


def test_social_media_posting_is_normalized():
    """The verified public LinkedIn JSON-LD shape maps to the model."""
    json_ld = """
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@id": "https://www.linkedin.com/posts/example-activity-123456789/",
      "@type": "SocialMediaPosting",
      "headline": "We are hiring a CRM Manager in Gurgaon.",
      "datePublished": "2026-09-08T10:00:00.000Z",
      "author": {
        "@type": "Person",
        "name": "Test Recruiter",
        "url": "https://www.linkedin.com/in/test-recruiter"
      },
      "articleBody": "We are hiring a CRM Manager in Gurgaon. #hiring"
    }
    </script>
    """

    session = FakeSession(json_ld)
    parser = LinkedInHiringPostParser(session=session)

    post = parser.parse(
        "https://www.linkedin.com/posts/example-activity-123456789/",
        discovery_query='"CRM Manager" AND hiring',
    )

    assert post is not None
    assert post.post_id == "activity:123456789"
    assert post.author_name == "Test Recruiter"
    assert post.author_url == "https://www.linkedin.com/in/test-recruiter"
    assert post.text == "We are hiring a CRM Manager in Gurgaon. #hiring"
    assert post.posted_at is not None
    assert post.posted_at.tzinfo == UTC
    assert post.discovery_query == '"CRM Manager" AND hiring'
    assert post.raw["@type"] == "SocialMediaPosting"


def test_article_body_is_preferred_over_headline():
    """Full articleBody is preferred when both fields exist."""
    json_ld = """
    <script type="application/ld+json">
    {
      "@type": "SocialMediaPosting",
      "@id": "https://www.linkedin.com/posts/example-activity-1/",
      "headline": "Short headline",
      "articleBody": "Complete post body"
    }
    </script>
    """

    parser = LinkedInHiringPostParser(session=FakeSession(json_ld))

    post = parser.parse(
        "https://www.linkedin.com/posts/example-activity-1/"
    )

    assert post is not None
    assert post.text == "Complete post body"


def test_headline_is_fallback_when_article_body_missing():
    """Headline is used when articleBody is unavailable."""
    json_ld = """
    <script type="application/ld+json">
    {
      "@type": "SocialMediaPosting",
      "@id": "https://www.linkedin.com/posts/example-activity-2/",
      "headline": "Hiring CRM Manager"
    }
    </script>
    """

    parser = LinkedInHiringPostParser(session=FakeSession(json_ld))

    post = parser.parse(
        "https://www.linkedin.com/posts/example-activity-2/"
    )

    assert post is not None
    assert post.text == "Hiring CRM Manager"


def test_non_linkedin_post_url_is_rejected():
    """Only LinkedIn member post URLs are accepted."""
    session = FakeSession("unused")
    parser = LinkedInHiringPostParser(session=session)

    assert parser.parse("https://example.com/posts/activity-123") is None
    assert session.requested_url is None


def test_non_200_response_is_rejected():
    """Non-success HTTP responses do not produce posts."""

    class ErrorSession:
        def __init__(self) -> None:
            self.headers: dict[str, str] = {}

        def get(self, url: str, **kwargs):
            response = FakeResponse("")
            response.status_code = 999
            return response

    parser = LinkedInHiringPostParser(session=ErrorSession())

    assert parser.parse(
        "https://www.linkedin.com/posts/example-activity-123/"
    ) is None


def test_missing_social_media_posting_is_rejected():
    """Pages without SocialMediaPosting JSON-LD are rejected."""
    html = """
    <script type="application/ld+json">
    {
      "@type": "WebPage",
      "headline": "Not a LinkedIn post"
    }
    </script>
    """

    parser = LinkedInHiringPostParser(session=FakeSession(html))

    assert parser.parse(
        "https://www.linkedin.com/posts/example-activity-123/"
    ) is None
