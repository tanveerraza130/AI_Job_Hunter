"""
Test real CRM job descriptions.
"""

import pytest


def test_real_crm_jd(extractor, profile, crm_jd):
    """Test extraction on a realistic CRM job description."""

    intelligence = extractor.extract(
        title="Senior CRM Manager",
        description=crm_jd,
    )

    # Required categories
    assert "crm_skills" in intelligence.categories
    assert "crm_platforms" in intelligence.categories
    assert "crm_concepts" in intelligence.categories

    # ------------------------------------------------------------------
    # Skills
    # ------------------------------------------------------------------

    skills = {item.name for item in intelligence.get_category("crm_skills")}

    expected_skills = {
        "Journey Builder",
        "Retention",
        "Segmentation",
        "Loyalty",
        "Churn Reduction",
        "SQL",
        "Statistical Analysis",
    }

    missing_skills = expected_skills - skills

    assert not missing_skills, (
        f"Missing expected skills: {sorted(missing_skills)}\n"
        f"Extracted: {sorted(skills)}"
    )

    # ------------------------------------------------------------------
    # Platforms
    # ------------------------------------------------------------------

    platforms = {
        item.name
        for item in intelligence.get_category("crm_platforms")
    }

    expected_platforms = {
        "CleverTap",
        "MoEngage",
        "Salesforce Marketing Cloud",
    }

    found_platforms = platforms & expected_platforms

    assert len(found_platforms) >= 2, (
        f"Expected >=2 platforms.\n"
        f"Found: {sorted(found_platforms)}"
    )

    # ------------------------------------------------------------------
    # Concepts
    # ------------------------------------------------------------------

    concepts = {
        item.name
        for item in intelligence.get_category("crm_concepts")
    }

    expected_concepts = {
        "Customer Journey",
        "Customer Lifecycle",
        "Customer Engagement",
        "Segmentation Strategy",
        "Personalization",
    }

    found_concepts = concepts & expected_concepts

    assert len(found_concepts) >= 4, (
        f"Expected >=4 concepts.\n"
        f"Found: {sorted(found_concepts)}"
    )

    # Customer Journey must stay a concept
    assert "Customer Journey" not in skills

    # Personalization must stay a concept
    assert "Personalization" not in skills


def test_crm_jd_skill_scores(extractor, profile, crm_jd):
    """Profile should overlap with extracted execution skills."""

    intelligence = extractor.extract(
        title="Senior CRM Manager",
        description=crm_jd,
    )

    extracted_skills = {
        item.name
        for item in intelligence.get_category("crm_skills")
    }

    profile_skills = set(profile.skills)

    overlap = extracted_skills & profile_skills

    assert len(overlap) >= 5, (
        f"Expected >=5 overlapping skills.\n"
        f"Overlap: {sorted(overlap)}"
    )