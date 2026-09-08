"""
Tests for the isolated LinkedIn Hiring Posts processor.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from jobs.linkedin_posts.models import LinkedInHiringPost
from jobs.linkedin_posts.processor import LinkedInHiringPostProcessor


def make_post(
    text: str,
    *,
    posted_at: datetime | None = None,
    location: str | None = None,
) -> LinkedInHiringPost:
    """Build a normalized post for processor tests."""
    return LinkedInHiringPost(
        post_id="activity:test-123",
        post_url="https://www.linkedin.com/posts/example-activity-123/",
        author_name="Test Recruiter",
        text=text,
        posted_at=posted_at
        or datetime.now(UTC) - timedelta(hours=2),
        location=location,
    )


def test_recent_crm_hiring_post_is_accepted():
    """A recent explicit CRM hiring post is relevant."""
    processor = LinkedInHiringPostProcessor()

    post = make_post(
        "We are hiring a CRM Manager in Gurgaon. Apply now!"
    )

    result = processor.process(post)

    assert result is not None
    assert result.post_id == post.post_id
    assert result.relevance_score > 0


def test_old_post_is_rejected():
    """Posts older than the configured freshness window are rejected."""
    processor = LinkedInHiringPostProcessor(max_age_hours=48)

    post = make_post(
        "We are hiring a CRM Manager.",
        posted_at=datetime.now(UTC) - timedelta(hours=49),
    )

    assert processor.process(post) is None


def test_missing_posted_at_is_rejected():
    """Freshness cannot be established without a publication timestamp."""
    processor = LinkedInHiringPostProcessor()

    post = make_post("We are hiring a CRM Manager.")
    post.posted_at = None

    assert processor.process(post) is None


def test_future_post_is_rejected():
    """Future publication timestamps are invalid."""
    processor = LinkedInHiringPostProcessor()

    post = make_post(
        "We are hiring a CRM Manager.",
        posted_at=datetime.now(UTC) + timedelta(minutes=5),
    )

    assert processor.process(post) is None


def test_non_hiring_crm_post_is_rejected():
    """CRM content without hiring intent is not a hiring lead."""
    processor = LinkedInHiringPostProcessor()

    post = make_post(
        "CRM Manager sharing some thoughts on lifecycle marketing."
    )

    assert processor.process(post) is None


def test_salesforce_developer_is_rejected():
    """Technical Salesforce roles are not CRM Manager hiring leads."""
    processor = LinkedInHiringPostProcessor()

    post = make_post(
        "We are hiring a Salesforce Developer in Gurgaon."
    )

    assert processor.process(post) is None


def test_business_development_noise_is_rejected():
    """Business-development hiring noise is excluded."""
    processor = LinkedInHiringPostProcessor()

    post = make_post(
        "We are hiring a Business Development Manager in Gurgaon."
    )

    assert processor.process(post) is None


def test_generic_marketing_role_without_crm_evidence_is_rejected():
    """Generic marketing hiring without CRM evidence is insufficient."""
    processor = LinkedInHiringPostProcessor()

    post = make_post(
        "We are hiring a Digital Marketing Manager. Apply now."
    )

    assert processor.process(post) is None


def test_crm_tool_plus_capability_is_accepted():
    """A CRM platform plus a core CRM capability establishes relevance."""
    processor = LinkedInHiringPostProcessor()

    post = make_post(
        "Hiring a Marketing Manager to own CleverTap lifecycle marketing "
        "and customer journeys."
    )

    result = processor.process(post)

    assert result is not None
    assert result.relevance_score > 0


def test_two_independent_crm_capabilities_are_accepted():
    """Two independent core CRM domains establish generic-role relevance."""
    processor = LinkedInHiringPostProcessor()

    post = make_post(
        "We are hiring a Customer Marketing Manager to lead "
        "segmentation and retention marketing."
    )

    result = processor.process(post)

    assert result is not None
    assert result.relevance_score > 0


def test_supported_location_is_positive_evidence():
    """Target location contributes positive relevance evidence."""
    processor = LinkedInHiringPostProcessor()

    without_location = make_post(
        "We are hiring a CRM Manager. Apply now."
    )
    with_location = make_post(
        "We are hiring a CRM Manager. Apply now.",
        location="Noida",
    )

    result_without = processor.process(without_location)
    result_with = processor.process(with_location)

    assert result_without is not None
    assert result_with is not None
    assert result_with.relevance_score > result_without.relevance_score


def test_missing_location_does_not_reject_strong_post():
    """Location absence does not reject an otherwise strong lead."""
    processor = LinkedInHiringPostProcessor()

    post = make_post(
        "We are hiring a CRM Manager. Apply now."
    )

    assert processor.process(post) is not None


def test_post_identity_and_raw_data_are_preserved():
    """Processing does not replace the source identity or raw payload."""
    processor = LinkedInHiringPostProcessor()

    post = make_post(
        "We are hiring a CRM Manager in Gurgaon."
    )
    post.raw = {"source": "linkedin-json-ld"}

    result = processor.process(post)

    assert result is not None
    assert result.post_id == post.post_id
    assert result.post_url == post.post_url
    assert result.text == post.text
    assert result.raw == {"source": "linkedin-json-ld"}

def test_generic_role_with_crm_team_reference_is_rejected():
    """A generic role is not CRM hiring merely because CRM is mentioned."""
    processor = LinkedInHiringPostProcessor()

    post = make_post(
        "We are hiring a Marketing Manager. "
        "You will work closely with our CRM team."
    )

    assert processor.process(post) is None


def test_explicit_crm_role_in_post_text_is_accepted_without_role_field():
    """Post text can establish an explicit CRM role when role is absent."""
    processor = LinkedInHiringPostProcessor()

    post = make_post(
        "We are hiring a CRM Manager in Gurgaon. Apply now!"
    )

    assert post.role is None

    result = processor.process(post)

    assert result is not None
    assert result.relevance_score > 0

def test_hiring_prefix_with_explicit_crm_role_is_accepted():
    """The common 'Hiring a CRM Manager' construction is recognized."""
    processor = LinkedInHiringPostProcessor()

    post = make_post(
        "Hiring a CRM Manager in Gurgaon. Apply now!"
    )

    result = processor.process(post)

    assert result is not None
    assert result.relevance_score > 0


def test_processing_does_not_mutate_original_relevance_score():
    """Processing returns a scored copy without mutating the source post."""
    processor = LinkedInHiringPostProcessor()

    post = make_post(
        "We are hiring a CRM Manager in Gurgaon."
    )
    post.relevance_score = 0.0

    result = processor.process(post)

    assert result is not None
    assert result is not post
    assert result.relevance_score > 0
    assert post.relevance_score == 0.0
