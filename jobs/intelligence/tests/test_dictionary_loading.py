"""
Test dictionary loading.
"""

from jobs.intelligence.extractor import IntelligenceExtractor


def test_dictionary_loading():
    """Verify all dictionaries are loaded via behavior."""
    extractor = IntelligenceExtractor("crm_manager")

    jd = "Experience with CleverTap."
    intelligence = extractor.extract(
        title="Test",
        description=jd,
    )

    assert "crm_platforms" in intelligence.categories

    platforms = intelligence.get_category("crm_platforms")

    assert any(
        item.name == "CleverTap"
        for item in platforms
    )


def test_crm_skills_extracts_skill():
    """
    Verify crm_skills extracts execution skills.

    NOTE:
    Customer Journey is intentionally modeled as a CRM CONCEPT,
    not a CRM SKILL.
    """

    extractor = IntelligenceExtractor("crm_manager")

    jd = """
    Experience with Journey Builder,
    journey orchestration,
    and journey automation.
    """

    intelligence = extractor.extract(
        title="Test",
        description=jd,
    )

    assert "crm_skills" in intelligence.categories

    skills = intelligence.get_category("crm_skills")
    skill_names = {item.name for item in skills}

    assert "Journey Builder" in skill_names


def test_crm_concepts_extracts_concept():
    """
    Verify crm_concepts extracts business concepts.
    """

    extractor = IntelligenceExtractor("crm_manager")

    jd = """
    Experience with customer journey mapping.
    """

    intelligence = extractor.extract(
        title="Test",
        description=jd,
    )

    assert "crm_concepts" in intelligence.categories

    concepts = intelligence.get_category("crm_concepts")
    concept_names = {item.name for item in concepts}

    assert "Customer Journey" in concept_names


def test_crm_platforms_extracts_platform():
    """Verify crm_platforms works via behavior."""

    extractor = IntelligenceExtractor("crm_manager")

    jd = "Experience with MoEngage."

    intelligence = extractor.extract(
        title="Test",
        description=jd,
    )

    assert "crm_platforms" in intelligence.categories

    platforms = intelligence.get_category("crm_platforms")

    assert any(
        item.name == "MoEngage"
        for item in platforms
    )