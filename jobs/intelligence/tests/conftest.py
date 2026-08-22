"""
Pytest fixtures for intelligence extractor tests.
"""

import pytest

from jobs.intelligence.extractor import IntelligenceExtractor
from jobs.profiles.loader import load_profile


@pytest.fixture
def extractor():
    """Return an IntelligenceExtractor instance for crm_manager."""
    return IntelligenceExtractor("crm_manager")


@pytest.fixture
def profile():
    """Return the crm_manager profile."""
    return load_profile("crm_manager")


@pytest.fixture
def crm_jd():
    """Return a realistic CRM Manager job description covering the full taxonomy."""
    return """
    Senior CRM Manager

    Responsibilities:
    - Lead lifecycle marketing strategy across Email, SMS, Push Notifications and WhatsApp
    - Own marketing automation workflows and campaign management across customer lifecycle
    - Develop customer segmentation and personalization frameworks
    - Drive customer engagement and retention campaigns
    - Manage loyalty programs and churn reduction initiatives
    - Design customer journeys using Journey Builder and Journey Design
    - Execute A/B testing and experimentation to optimize conversion rates
    - Analyze customer data using SQL and statistical analysis
    - Build dashboards and generate business insights for CRM performance
    - Partner with Product, Data and Engineering teams to improve customer experience

    Requirements:
    - 5+ years of CRM, Lifecycle Marketing or Marketing Automation experience
    - Hands-on experience with CleverTap, MoEngage, Braze or WebEngage
    - Experience with Salesforce Marketing Cloud is a plus
    - Strong SQL and data analysis skills
    - Experience with customer journey orchestration
    - Strong understanding of customer lifecycle management
    - Experience designing segmentation strategies and executing campaigns
    - Excellent stakeholder management and communication skills
    """