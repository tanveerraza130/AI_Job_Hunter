"""
Test negative inputs (non-CRM JDs should not hallucinate).
"""

import pytest


def test_no_crm_vocabulary(extractor):
    """Test that non-CRM JDs don't hallucinate CRM skills."""
    jd = """
    Java Backend Engineer

    Responsibilities:
    - Develop REST APIs using Spring Boot
    - Build Kafka consumers and producers
    - Deploy Docker containers on Kubernetes
    - Optimize database queries for PostgreSQL
    - Implement CI/CD pipelines with Jenkins
    """

    intelligence = extractor.extract(title="Backend Engineer", description=jd)
    skills = intelligence.get_category("crm_skills")
    skill_names = {item.name for item in skills}

    # These should NOT be extracted from a backend JD
    crm_terms = {"Lifecycle Marketing", "Retention", "Customer Journey", "Customer Engagement"}
    for term in crm_terms:
        assert term not in skill_names


def test_sales_jd(extractor):
    """Test that sales JDs don't hallucinate CRM skills."""
    jd = """
    Account Executive

    Responsibilities:
    - Close enterprise deals
    - Build relationships with C-level executives
    - Manage sales pipeline
    - Achieve quarterly quotas
    """

    intelligence = extractor.extract(title="Account Executive", description=jd)
    skills = intelligence.get_category("crm_skills")
    skill_names = {item.name for item in skills}

    # These should NOT be extracted from a sales JD
    crm_terms = {"Lifecycle Marketing", "Retention", "Segmentation", "Personalization"}
    for term in crm_terms:
        assert term not in skill_names


def test_html_jd(extractor):
    """Test that HTML content is handled gracefully."""
    jd = """
    <html>
    <body>
    <h1>CRM Manager</h1>
    <p>Experience with <b>CleverTap</b> and <b>MoEngage</b>.</p>
    </body>
    </html>
    """

    intelligence = extractor.extract(title="CRM Manager", description=jd)
    # Should not raise exceptions
    assert isinstance(intelligence.categories, dict)