"""
Regression test for the original skill_score/tool_score = 0 bug.
"""

import pytest

from jobs.intelligence.extractor import IntelligenceExtractor
from jobs.profiles.loader import load_profile
from jobs.scoring.engine import ProfileScoringEngine


def test_zero_score_regression():
    """
    Regression test: Ensure skill_score and tool_score are > 0
    for a realistic CRM job description.
    
    This prevents the original bug from reappearing where
    skill_score and tool_score were always 0.
    """
    # Setup
    profile = load_profile("crm_manager")
    extractor = IntelligenceExtractor("crm_manager")
    scoring_engine = ProfileScoringEngine("crm_manager")

    # Realistic CRM JD
    jd = """
    Senior CRM Manager

    Responsibilities:
    - Lead lifecycle marketing strategy across email, SMS, and push
    - Develop customer segmentation and personalization frameworks
    - Drive customer engagement and retention campaigns
    - Manage loyalty programs and churn reduction initiatives
    - Build customer journeys using journey builder tools
    - Analyze customer data using SQL and statistical analysis
    - A/B test campaigns to optimize conversion rates

    Requirements:
    - 5+ years in CRM/marketing roles
    - Experience with CleverTap, MoEngage, or Braze
    - Strong SQL skills
    - Experience with Salesforce Marketing Cloud is a plus
    - Strong understanding of customer lifecycle management
    """

    # Extract
    intelligence = extractor.extract(
        title="Senior CRM Manager",
        description=jd,
    )

    # Score
    result = scoring_engine.score_job(intelligence)

    # Assert: skill_score and tool_score are > 0
    # This is the regression check for the original bug
    assert result.breakdown.skill_match > 0, f"skill_match should be > 0, got {result.breakdown.skill_match}"
    assert result.breakdown.tool_match > 0, f"tool_match should be > 0, got {result.breakdown.tool_match}"

    # Additional validation: score should be reasonable
    assert 0 <= result.score <= 100, f"score should be between 0 and 100, got {result.score}"


def test_zero_score_regression_with_full_profile():
    """
    Test that the full scoring pipeline produces non-zero scores
    using the actual profile skills.
    """
    profile = load_profile("crm_manager")
    extractor = IntelligenceExtractor("crm_manager")
    scoring_engine = ProfileScoringEngine("crm_manager")

    # Use a JD that contains profile skills explicitly
    jd = """
    CRM Manager

    Experience with:
    - Lifecycle Marketing
    - Retention
    - Segmentation
    - Automation
    - Journey Builder
    - Journey Design
    - Campaign Management
    - Loyalty
    - Churn Reduction
    - Customer Engagement
    - Data Analysis
    - SQL
    - A/B Testing
    - Dashboarding
    """

    intelligence = extractor.extract(
        title="CRM Manager",
        description=jd,
    )

    result = scoring_engine.score_job(intelligence)

    # With all profile skills in the JD, skill_match should be high
    assert result.breakdown.skill_match > 50, f"skill_match should be > 50, got {result.breakdown.skill_match}"
    assert result.score > 0, f"score should be > 0, got {result.score}"


def test_zero_score_regression_tools():
    """
    Test that tool_score works for CRM platforms.
    """
    profile = load_profile("crm_manager")
    extractor = IntelligenceExtractor("crm_manager")
    scoring_engine = ProfileScoringEngine("crm_manager")

    # JD with profile tools
    jd = """
    CRM Manager

    Experience with:
    - CleverTap
    - MoEngage
    - Braze
    - Salesforce Marketing Cloud
    """

    intelligence = extractor.extract(
        title="CRM Manager",
        description=jd,
    )

    result = scoring_engine.score_job(intelligence)

    # tool_score should be > 0
    assert result.breakdown.tool_match > 0, f"tool_match should be > 0, got {result.breakdown.tool_match}"