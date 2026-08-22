"""
Pytest fixtures for scoring engine tests.
"""

import pytest

from jobs.intelligence.models import JobIntelligence, WeightedItem
from jobs.profiles.loader import load_profile
from jobs.scoring.engine import ProfileScoringEngine


@pytest.fixture
def profile():
    """Return the crm_manager profile."""
    return load_profile("crm_manager")


@pytest.fixture
def scoring_engine(profile):
    """Return a ProfileScoringEngine instance."""
    return ProfileScoringEngine("crm_manager")


@pytest.fixture
def perfect_intelligence():
    """JobIntelligence with all profile skills and tools."""
    return JobIntelligence(
        categories={
            "crm_skills": [
                WeightedItem("Lifecycle Marketing", 1),
                WeightedItem("Retention", 1),
                WeightedItem("Segmentation", 1),
                WeightedItem("Automation", 1),
                WeightedItem("Journey Builder", 1),
                WeightedItem("Journey Design", 1),
                WeightedItem("Campaign Management", 1),
                WeightedItem("Loyalty", 1),
                WeightedItem("Churn Reduction", 1),
                WeightedItem("Customer Engagement", 1),
                WeightedItem("Data Analysis", 1),
                WeightedItem("SQL", 1),
                WeightedItem("A/B Testing", 1),
                WeightedItem("Dashboarding", 1),
            ],
            "crm_platforms": [
                WeightedItem("CleverTap", 1),
                WeightedItem("MoEngage", 1),
                WeightedItem("WebEngage", 1),
                WeightedItem("Netcore", 1),
                WeightedItem("Braze", 1),
                WeightedItem("Salesforce Marketing Cloud", 1),
                WeightedItem("Iterable", 1),
            ],
        },
        experience_min=5,
        experience_max=8,
        salary_min=2000000,
        salary_max=2500000,
    )


@pytest.fixture
def partial_intelligence():
    """JobIntelligence with partial skills and tools."""
    return JobIntelligence(
        categories={
            "crm_skills": [
                WeightedItem("Retention", 1),
                WeightedItem("Segmentation", 1),
                WeightedItem("SQL", 1),
                WeightedItem("A/B Testing", 1),
            ],
            "crm_platforms": [
                WeightedItem("CleverTap", 1),
                WeightedItem("Braze", 1),
            ],
        },
        experience_min=3,
        experience_max=5,
        salary_min=1200000,
        salary_max=1800000,
    )


@pytest.fixture
def empty_intelligence():
    """Empty JobIntelligence."""
    return JobIntelligence()


@pytest.fixture
def high_salary_intelligence():
    """JobIntelligence with high salary range."""
    return JobIntelligence(
        categories={},
        experience_min=5,
        experience_max=8,
        salary_min=4000000,
        salary_max=5000000,
    )


@pytest.fixture
def low_salary_intelligence():
    """JobIntelligence with low salary range."""
    return JobIntelligence(
        categories={},
        experience_min=5,
        experience_max=8,
        salary_min=500000,
        salary_max=700000,
    )