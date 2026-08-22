"""
Test overlap handling.
"""

import pytest


def test_overlap_customer_journey_optimization(extractor):
    """
    Customer Journey is a CRM CONCEPT.

    Customer Journey Optimization should resolve to the
    Customer Journey concept, not a CRM skill.
    """

    jd = """
    Experience with Customer Journey Optimization.
    """

    intelligence = extractor.extract(
        title="Test Job",
        description=jd,
    )

    assert "crm_concepts" in intelligence.categories

    concepts = intelligence.get_category("crm_concepts")
    concept_names = {item.name for item in concepts}

    assert "Customer Journey" in concept_names

    # Ensure it is NOT extracted as a skill
    skills = intelligence.get_category("crm_skills")
    skill_names = {item.name for item in skills}

    assert "Customer Journey" not in skill_names


def test_overlap_multi_channel_marketing(extractor):
    """
    Multi-Channel Marketing should resolve to its canonical
    CRM concept without duplicate extraction.
    """

    jd = """
    Multi-channel marketing experience required.
    """

    intelligence = extractor.extract(
        title="Test Job",
        description=jd,
    )

    assert "crm_concepts" in intelligence.categories

    concepts = intelligence.get_category("crm_concepts")
    concept_names = {item.name for item in concepts}

    assert "Multi-Channel Marketing" in concept_names