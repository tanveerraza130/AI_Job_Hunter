"""
Generic component scoring tests for AI Job Hunter.

These tests validate the ENGINE CONTRACTS, not profile-specific behavior.
All profile-specific data is loaded dynamically from the active profile configuration.

Tests verify:
- Score ranges (0-100)
- Relative ordering (stronger matches score higher)
- Config-driven behavior (values come from profile config)
- Safe handling of missing configuration
- Generic invariants that hold for any profile

IMPORTANT: No profile-specific assumptions or hard-coded values.
The active profile must be supplied via the existing project configuration mechanism.
"""

from __future__ import annotations

import os
import re
import pytest

from jobs.intelligence.extractor import IntelligenceExtractor
from jobs.models import Job
from jobs.scoring.engine import ProfileScoringEngine


def _get_matching_string_for_signal(signal: str) -> str | None:
    """
    Generate a string that matches a given regex signal.
    Supports common patterns like \bword\b.
    """
    clean = signal.replace("\\b", "")
    clean = clean.replace("\\", "")
    clean = re.sub(r"[^a-zA-Z0-9\s]", "", clean)
    return clean.capitalize() if clean else None


def _get_non_matching_string_for_signal(signal: str) -> str:
    """
    Generate a string guaranteed NOT to match a given regex signal.
    For patterns like \bword\b, we add a unique suffix.
    """
    clean = signal.replace("\\b", "")
    clean = clean.replace("\\", "")
    clean = re.sub(r"[^a-zA-Z0-9\s]", "", clean)
    if clean:
        return clean + "XYZNonExistent999"
    return "XYZNonExistent999"


def _get_configured_concept(scoring_engine) -> str | None:
    """
    Get a canonical concept directly from the active profile taxonomy.

    The test needs a deterministic, configured concept to construct a JD
    fixture. It must not depend on an arbitrary generic sentence containing
    a taxonomy concept by chance.
    """
    concepts_category = scoring_engine.category_mappings.get("concepts")

    if not concepts_category:
        return None

    extractor = IntelligenceExtractor(scoring_engine.profile_type)
    concepts = extractor._canonical_items.get(concepts_category, [])

    if not concepts:
        return None

    first_concept = concepts[0]

    if isinstance(first_concept, tuple):
        return first_concept[0]

    if isinstance(first_concept, str):
        return first_concept

    name = getattr(first_concept, "name", None)
    return name if name else None


def _get_configured_title(scoring_engine, title_type: str = "strong") -> str | None:
    """
    Get a configured title from the profile's title rules.
    Uses ONLY the actual title configuration.
    """
    title_rules = scoring_engine.title_rules
    titles = title_rules.get(title_type, [])
    if titles:
        return titles[0]
    return None


@pytest.fixture
def scoring_engine():
    """
    Create a scoring engine for testing.
    Profile type must be supplied via environment variable.
    """
    profile_type = os.environ.get("AI_JOB_HUNTER_PROFILE")
    if not profile_type:
        pytest.skip("AI_JOB_HUNTER_PROFILE environment variable not set")
    return ProfileScoringEngine(profile_type)


class TestSkillMatch:
    """Generic skill matching contract tests."""

    def test_skill_match_range(self, scoring_engine):
        """Skill match score must always be between 0 and 100."""
        profile_skills = scoring_engine.profile.skills
        if not profile_skills:
            pytest.skip("Profile has no skills configured")

        from jobs.intelligence.models import WeightedItem
        job_skills = [WeightedItem(name=profile_skills[0], count=1)]

        match, missing, strengths = scoring_engine._calculate_skill_match(
            profile_skills,
            job_skills,
        )

        assert 0.0 <= match <= 100.0

    def test_skill_match_perfect_is_maximum(self, scoring_engine):
        """Perfect skill match should produce the highest possible score."""
        profile_skills = scoring_engine.profile.skills
        if not profile_skills:
            pytest.skip("Profile has no skills configured")

        from jobs.intelligence.models import WeightedItem
        job_skills = [WeightedItem(name=s, count=1) for s in profile_skills]

        perfect_match, _, _ = scoring_engine._calculate_skill_match(
            profile_skills,
            job_skills,
        )

        partial_job_skills = job_skills[:max(1, len(job_skills)//2)]
        partial_match, _, _ = scoring_engine._calculate_skill_match(
            profile_skills,
            partial_job_skills,
        )

        assert perfect_match >= partial_match

    def test_skill_match_empty_profile(self, scoring_engine):
        """Empty profile skills should return 100% (no missing skills to penalize)."""
        match, missing, strengths = scoring_engine._calculate_skill_match(
            [],
            [],
        )

        assert match == 100.0
        assert len(missing) == 0

    def test_skill_match_empty_job_skills(self, scoring_engine):
        """Empty job skills with non-empty profile should return 0."""
        profile_skills = scoring_engine.profile.skills
        if not profile_skills:
            pytest.skip("Profile has no skills configured")

        match, missing, strengths = scoring_engine._calculate_skill_match(
            profile_skills,
            [],
        )

        assert match == 0.0
        assert len(missing) == len(profile_skills)

    def test_skill_match_scales_with_number_of_matches(self, scoring_engine):
        """Skill match score should increase with more matched skills."""
        profile_skills = scoring_engine.profile.skills
        if len(profile_skills) < 2:
            pytest.skip("Profile needs at least 2 skills for this test")

        from jobs.intelligence.models import WeightedItem

        job_skills_one = [WeightedItem(name=profile_skills[0], count=1)]
        match_one, _, _ = scoring_engine._calculate_skill_match(
            profile_skills,
            job_skills_one,
        )

        job_skills_two = [
            WeightedItem(name=profile_skills[0], count=1),
            WeightedItem(name=profile_skills[1], count=1),
        ]
        match_two, _, _ = scoring_engine._calculate_skill_match(
            profile_skills,
            job_skills_two,
        )

        assert match_two >= match_one


class TestToolMatch:
    """Generic tool matching contract tests."""

    def test_tool_match_range(self, scoring_engine):
        """Tool match score must always be between 0 and 100."""
        profile_tools = scoring_engine.profile.tools
        if not profile_tools:
            pytest.skip("Profile has no tools configured")

        from jobs.intelligence.models import WeightedItem
        job_tools = [WeightedItem(name=profile_tools[0], count=1)]

        match, missing, strengths = scoring_engine._calculate_tool_match(
            profile_tools,
            job_tools,
        )

        assert 0.0 <= match <= 100.0

    def test_tool_match_increases_with_matches(self, scoring_engine):
        """Tool match score should increase with more matched tools."""
        profile_tools = scoring_engine.profile.tools
        if len(profile_tools) < 2:
            pytest.skip("Profile needs at least 2 tools for this test")

        from jobs.intelligence.models import WeightedItem

        job_tools_one = [WeightedItem(name=profile_tools[0], count=1)]
        match_one, _, _ = scoring_engine._calculate_tool_match(
            profile_tools,
            job_tools_one,
        )

        job_tools_two = [
            WeightedItem(name=profile_tools[0], count=1),
            WeightedItem(name=profile_tools[1], count=1),
        ]
        match_two, _, _ = scoring_engine._calculate_tool_match(
            profile_tools,
            job_tools_two,
        )

        assert match_two >= match_one


class TestJDMatch:
    """Generic JD/concept matching contract tests.

    JD matching is concept-based and deduplicates concepts already in skills/tools.
    Tests use dynamically loaded concepts from the profile via IntelligenceExtractor.
    """

    def test_jd_match_range(self, scoring_engine):
        """JD match score must always be between 0 and 100."""
        # Get a concept using the IntelligenceExtractor
        concept = _get_configured_concept(scoring_engine)
        if not concept:
            pytest.skip("No configured concept available for this profile")

        job = Job(
            job_id="test_jd_range",
            title="Sample Job",
            company="Test Company",
            location="Bangalore",
            description=concept,
            job_url="https://test.com/job/range",
            source="test",
        )

        extractor = IntelligenceExtractor(scoring_engine.profile_type)
        intelligence = extractor.extract_from_job(job)

        concepts_category = scoring_engine._get_category_mapping("concepts")
        skills_category = scoring_engine._get_category_mapping("skills")
        tools_category = scoring_engine._get_category_mapping("tools")

        job_concepts = intelligence.get_category(concepts_category)
        job_skills = intelligence.get_category(skills_category)
        job_tools = intelligence.get_category(tools_category)

        jd_match = scoring_engine._calculate_jd_match(
            job_concepts,
            job_skills,
            job_tools,
        )

        assert 0.0 <= jd_match <= 100.0

    def test_jd_match_concept_contribution(self, scoring_engine):
        """
        A job with a configured concept should score higher than one without.
        """
        concept = _get_configured_concept(scoring_engine)
        if not concept:
            pytest.skip("No configured concept available for this profile")

        concept_job = Job(
            job_id="test_jd_concept",
            title="Sample Job",
            company="Test Company",
            location="Bangalore",
            description=concept,
            job_url="https://test.com/job/concept",
            source="test",
        )

        non_matching_title = _get_non_matching_string_for_signal(concept)
        non_matching_job = Job(
            job_id="test_jd_no_concept",
            title="Sample Job",
            company="Test Company",
            location="Bangalore",
            description=non_matching_title,
            job_url="https://test.com/job/no_concept",
            source="test",
        )

        extractor = IntelligenceExtractor(scoring_engine.profile_type)
        concept_intelligence = extractor.extract_from_job(concept_job)
        no_concept_intelligence = extractor.extract_from_job(non_matching_job)

        concepts_category = scoring_engine._get_category_mapping("concepts")
        skills_category = scoring_engine._get_category_mapping("skills")
        tools_category = scoring_engine._get_category_mapping("tools")

        concept_concepts = concept_intelligence.get_category(concepts_category)
        concept_skills = concept_intelligence.get_category(skills_category)
        concept_tools = concept_intelligence.get_category(tools_category)

        no_concept_concepts = no_concept_intelligence.get_category(concepts_category)
        no_concept_skills = no_concept_intelligence.get_category(skills_category)
        no_concept_tools = no_concept_intelligence.get_category(tools_category)

        jd_match_with_concept = scoring_engine._calculate_jd_match(
            concept_concepts,
            concept_skills,
            concept_tools,
        )

        jd_match_without_concept = scoring_engine._calculate_jd_match(
            no_concept_concepts,
            no_concept_skills,
            no_concept_tools,
        )

        assert jd_match_with_concept >= jd_match_without_concept

    def test_jd_match_empty_concepts(self, scoring_engine):
        """Empty job concepts should return 0."""
        from jobs.intelligence.models import WeightedItem

        jd_match = scoring_engine._calculate_jd_match(
            [],  # job_concepts
            [],  # job_skills
            [],  # job_tools
        )

        assert jd_match == 0.0


class TestTitleMatch:
    """Generic title matching contract tests."""

    def test_title_match_range(self, scoring_engine):
        """Title match score must always be between 0 and 100."""
        title_rules = scoring_engine.title_rules
        all_titles = []
        all_titles.extend(title_rules.get("strong", []))
        all_titles.extend(title_rules.get("weak", []))
        patterns = title_rules.get("patterns", [])

        non_matching_title = "XYZNonExistent999"
        for pattern in patterns:
            non_matching_title = _get_non_matching_string_for_signal(pattern.get("pattern", ""))

        match = scoring_engine._calculate_title_match(non_matching_title)

        assert match == 0.0

    def test_title_match_strong_beats_weak(self, scoring_engine):
        """Strong title matches should score higher than weak title matches."""
        title_rules = scoring_engine.title_rules
        strong_titles = title_rules.get("strong", [])
        weak_titles = title_rules.get("weak", [])

        if not strong_titles or not weak_titles:
            pytest.skip("Profile has insufficient title rules for this test")

        strong_match = scoring_engine._calculate_title_match(strong_titles[0])
        weak_match = scoring_engine._calculate_title_match(weak_titles[0])

        assert strong_match >= weak_match

    def test_title_match_empty_title(self, scoring_engine):
        """Empty title should always return 0."""
        match = scoring_engine._calculate_title_match("")
        assert match == 0.0

    def test_title_match_pattern_matches(self, scoring_engine):
        """Pattern matching should work for configured patterns."""
        title_rules = scoring_engine.title_rules
        patterns = title_rules.get("patterns", [])

        if not patterns:
            pytest.skip("No title patterns configured for this profile")

        first_pattern = patterns[0].get("pattern", "")
        if not first_pattern:
            pytest.skip("First pattern is empty")

        test_title = _get_matching_string_for_signal(first_pattern)
        if not test_title:
            pytest.skip("Could not generate matching string for first pattern")

        match = scoring_engine._calculate_title_match(test_title)

        assert match > 0.0


class TestNegativePenalty:
    """Generic negative penalty contract tests."""

    def test_negative_penalty_range(self, scoring_engine):
        """Negative penalty must always be between 0 and configured max."""
        negative_config = scoring_engine.negative_signals
        max_penalty = negative_config.get("max_penalty", 100.0)

        signals = negative_config.get("signals", [])
        non_matching_title = "XYZNonExistent999"
        if signals:
            non_matching_title = _get_non_matching_string_for_signal(signals[0])

        penalty = scoring_engine._calculate_negative_penalty(
            non_matching_title,
            "Clean description"
        )

        assert 0.0 <= penalty <= max_penalty

    def test_negative_penalty_no_signal_zero(self, scoring_engine):
        """No matching negative signal should result in 0 penalty."""
        negative_config = scoring_engine.negative_signals
        signals = negative_config.get("signals", [])

        non_matching_title = "XYZNonExistent999"
        if signals:
            non_matching_title = _get_non_matching_string_for_signal(signals[0])

        penalty = scoring_engine._calculate_negative_penalty(
            non_matching_title,
            "Clean description"
        )

        assert penalty == 0.0

    def test_negative_penalty_single_signal(self, scoring_engine):
        """A single matching signal should apply the configured penalty."""
        negative_config = scoring_engine.negative_signals
        signals = negative_config.get("signals", [])
        penalty_per_signal = negative_config.get("penalty_per_signal", 0.0)
        max_penalty = negative_config.get("max_penalty", 100.0)

        if not signals:
            pytest.skip("No negative signals configured for this profile")

        matched = False
        for signal in signals:
            test_title = _get_matching_string_for_signal(signal)
            if not test_title:
                continue

            penalty = scoring_engine._calculate_negative_penalty(test_title, "")
            if penalty > 0:
                matched = True
                expected = min(penalty_per_signal, max_penalty)
                assert penalty == expected
                break

        if not matched:
            pytest.skip("Could not find a matching test string for any configured signal")

    def test_negative_penalty_multiple_signals(self, scoring_engine):
        """Multiple matching signals should accumulate but be capped at max."""
        negative_config = scoring_engine.negative_signals
        signals = negative_config.get("signals", [])
        penalty_per_signal = negative_config.get("penalty_per_signal", 0.0)
        max_penalty = negative_config.get("max_penalty", 100.0)

        if len(signals) < 2:
            pytest.skip("Need at least 2 signals for accumulation test")

        matching_titles = []
        for signal in signals[:3]:
            test_title = _get_matching_string_for_signal(signal)
            if test_title:
                matching_titles.append(test_title)

        if len(matching_titles) < 2:
            pytest.skip("Could not generate matching strings for multiple signals")

        penalty_one = scoring_engine._calculate_negative_penalty(matching_titles[0], "")
        expected_one = min(penalty_per_signal, max_penalty)
        assert penalty_one == expected_one

        combined_two = " ".join(matching_titles[:2])
        penalty_two = scoring_engine._calculate_negative_penalty(combined_two, "")
        expected_two = min(penalty_per_signal * 2, max_penalty)
        assert penalty_two == expected_two

        combined_three = " ".join(matching_titles[:3])
        penalty_three = scoring_engine._calculate_negative_penalty(combined_three, "")
        expected_three = min(penalty_per_signal * 3, max_penalty)
        assert penalty_three == expected_three


class TestOverallScore:
    """Generic overall score contract tests."""

    def test_overall_score_range(self, scoring_engine):
        """Overall score must always be between 0 and 100."""
        title = _get_configured_title(scoring_engine, "strong")
        if not title:
            pytest.skip("No title rules configured for this profile")

        job = Job(
            job_id="test_overall_range",
            title=title,
            company="Test Company",
            location="Bangalore",
            description="Test job description",
            job_url="https://test.com/job/range",
            source="test",
        )

        extractor = IntelligenceExtractor(scoring_engine.profile_type)
        intelligence = extractor.extract_from_job(job)

        result = scoring_engine.score_job(
            intelligence,
            job_title=job.title,
            job_description=job.description,
        )

        assert 0.0 <= result.score <= 100.0

    def test_overall_score_components_are_valid(self, scoring_engine):
        """All scoring components should be within valid ranges."""
        title = _get_configured_title(scoring_engine, "strong")
        if not title:
            pytest.skip("No title rules configured for this profile")

        job = Job(
            job_id="test_overall_components",
            title=title,
            company="Test Company",
            location="Bangalore",
            description="Test job description",
            job_url="https://test.com/job/components",
            source="test",
        )

        extractor = IntelligenceExtractor(scoring_engine.profile_type)
        intelligence = extractor.extract_from_job(job)

        result = scoring_engine.score_job(
            intelligence,
            job_title=job.title,
            job_description=job.description,
        )

        assert 0.0 <= result.breakdown.skill_match <= 100.0
        assert 0.0 <= result.breakdown.tool_match <= 100.0
        assert 0.0 <= result.breakdown.jd_match <= 100.0
        assert 0.0 <= result.breakdown.title_match <= 100.0
        assert 0.0 <= result.breakdown.negative_penalty <= 100.0

    def test_overall_score_better_match_scores_higher(self, scoring_engine):
        """Better job matches should score higher than weaker matches."""
        profile = scoring_engine.profile
        if not profile.skills or not profile.tools:
            pytest.skip("Profile has insufficient skills/tools for this test")

        title = _get_configured_title(scoring_engine, "strong")
        if not title:
            pytest.skip("No title rules configured for this profile")

        strong_description = "\n".join([f"- {skill}" for skill in profile.skills[:3]]) + "\n" + "\n".join([f"- {tool}" for tool in profile.tools[:3]])

        strong_job = Job(
            job_id="test_overall_strong",
            title=title,
            company="Test Company",
            location="Bangalore",
            description=strong_description,
            job_url="https://test.com/job/strong",
            source="test",
        )

        weak_job = Job(
            job_id="test_overall_weak",
            title="XYZNonExistent999",
            company="Test Company",
            location="Bangalore",
            description="Completely unrelated job description with no matching terms",
            job_url="https://test.com/job/weak",
            source="test",
        )

        extractor = IntelligenceExtractor(scoring_engine.profile_type)

        strong_intelligence = extractor.extract_from_job(strong_job)
        weak_intelligence = extractor.extract_from_job(weak_job)

        strong_result = scoring_engine.score_job(
            strong_intelligence,
            job_title=strong_job.title,
            job_description=strong_job.description,
        )

        weak_result = scoring_engine.score_job(
            weak_intelligence,
            job_title=weak_job.title,
            job_description=weak_job.description,
        )

        assert strong_result.score >= weak_result.score

    def test_overall_score_empty_input(self, scoring_engine):
        """Empty input should produce a valid score."""
        from jobs.intelligence.models import JobIntelligence

        empty_intelligence = JobIntelligence(categories={})
        result = scoring_engine.score_job(
            empty_intelligence,
            job_title="",
            job_description="",
        )

        assert 0.0 <= result.score <= 100.0


class TestFullPipeline:
    """Generic full pipeline contract tests."""

    def test_full_pipeline_returns_valid_score(self, scoring_engine):
        """Full pipeline should always return a valid score."""
        title = _get_configured_title(scoring_engine, "strong")
        if not title:
            pytest.skip("No title rules configured for this profile")

        job = Job(
            job_id="test_pipeline_valid",
            title=title,
            company="Test Company",
            location="Bangalore",
            description="Test job description",
            job_url="https://test.com/job/pipeline",
            source="test",
        )

        extractor = IntelligenceExtractor(scoring_engine.profile_type)
        intelligence = extractor.extract_from_job(job)

        result = scoring_engine.score_job(
            intelligence,
            job_title=job.title,
            job_description=job.description,
        )

        assert 0.0 <= result.score <= 100.0

    def test_full_pipeline_handles_empty_intelligence(self, scoring_engine):
        """Pipeline should handle empty intelligence gracefully."""
        from jobs.intelligence.models import JobIntelligence

        empty_intelligence = JobIntelligence(categories={})
        result = scoring_engine.score_job(
            empty_intelligence,
            job_title="",
            job_description="",
        )

        assert 0.0 <= result.score <= 100.0

    def test_full_pipeline_handles_empty_title_description(self, scoring_engine):
        """Pipeline should handle empty title and description."""
        job = Job(
            job_id="test_pipeline_empty",
            title="",
            company="Test Company",
            location="Bangalore",
            description="",
            job_url="https://test.com/job/empty",
            source="test",
        )

        extractor = IntelligenceExtractor(scoring_engine.profile_type)
        intelligence = extractor.extract_from_job(job)

        result = scoring_engine.score_job(
            intelligence,
            job_title=job.title,
            job_description=job.description,
        )

        assert 0.0 <= result.score <= 100.0