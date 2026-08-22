"""
Tests for ProfileJobFilter.
"""

import pytest

from jobs.filtering.profile_filter import ProfileJobFilter
from jobs.job import Job
from jobs.profiles.profile import Profile
from jobs.scoring.engine import ProfileScoringEngine


def create_profile(negative_titles=None, negative_keywords=None):
    """Create a test profile."""
    return Profile(
        profile_id="test",
        profile_name="Test Profile",
        version=1,
        enabled=True,
        search_keywords=["test"],
        skills=[],
        tools=[],
        negative_titles=negative_titles or [],
        negative_keywords=negative_keywords or [],
        locations=[],
        work_modes=[],
    )


def create_crm_profile():
    """Load the real CRM Manager scoring profile."""
    return ProfileScoringEngine("crm_manager").profile


def create_job(title: str, description: str = "") -> Job:
    """Create a test job."""
    return Job(
        job_id="test",
        title=title,
        company="Test Company",
        location="Test Location",
        description=description,
        portal="test",
        job_url="https://test.com",
    )


class TestProfileJobFilter:
    """Tests for ProfileJobFilter."""

    def test_accept_crm_manager(self):
        """Test that CRM Manager is accepted."""
        profile = create_profile(
            negative_titles=["Sales", "BPO"],
            negative_keywords=["cold calling", "pre-sales"],
        )
        filter_obj = ProfileJobFilter(profile)

        job = create_job("CRM Manager", "CleverTap lifecycle campaigns")
        accepted, rejected = filter_obj.filter_jobs([job])

        assert len(accepted) == 1
        assert len(rejected) == 0
        assert accepted[0].title == "CRM Manager"

    def test_reject_voice_process_executive(self):
        """Test that Voice Process Executive is rejected."""
        profile = create_profile(
            negative_titles=[],
            negative_keywords=["voice process", "outbound calling"],
        )
        filter_obj = ProfileJobFilter(profile)

        job = create_job("Voice Process Executive", "BPO customer support")
        accepted, rejected = filter_obj.filter_jobs([job])

        assert len(accepted) == 0
        assert len(rejected) == 1
        assert rejected[0].title == "Voice Process Executive"

    def test_reject_pre_sales(self):
        """Test that Pre Sales Executive is rejected."""
        profile = create_profile(
            negative_titles=[],
            negative_keywords=["pre-sales", "presales", "cold calling"],
        )
        filter_obj = ProfileJobFilter(profile)

        job = create_job("Pre Sales Executive", "Cold calling for lead generation")
        accepted, rejected = filter_obj.filter_jobs([job])

        assert len(accepted) == 0
        assert len(rejected) == 1
        assert rejected[0].title == "Pre Sales Executive"

    def test_accept_salesforce_crm(self):
        """Test that Salesforce CRM Manager is accepted."""
        profile = create_profile(
            negative_titles=["Sales", "BPO"],
            negative_keywords=["cold calling", "pre-sales"],
        )
        filter_obj = ProfileJobFilter(profile)

        job = create_job("Salesforce CRM Manager", "Marketing Cloud experience")
        accepted, rejected = filter_obj.filter_jobs([job])

        assert len(accepted) == 1
        assert len(rejected) == 0
        assert accepted[0].title == "Salesforce CRM Manager"

    def test_reject_cold_calling_in_description(self):
        """Test that job with cold calling in description is rejected."""
        profile = create_profile(
            negative_titles=[],
            negative_keywords=["cold calling"],
        )
        filter_obj = ProfileJobFilter(profile)

        job = create_job("Sales Representative", "Responsible for cold calling clients")
        accepted, rejected = filter_obj.filter_jobs([job])

        assert len(accepted) == 0
        assert len(rejected) == 1

    def test_accept_crm_analyst(self):
        """Test that CRM Analyst is accepted."""
        profile = create_profile(
            negative_titles=["Sales", "BPO"],
            negative_keywords=["cold calling", "pre-sales"],
        )
        filter_obj = ProfileJobFilter(profile)

        job = create_job("CRM Analyst", "Data analysis and customer insights")
        accepted, rejected = filter_obj.filter_jobs([job])

        assert len(accepted) == 1
        assert len(rejected) == 0

    def test_reject_lead_generation(self):
        """Test that Lead Generation role is rejected."""
        profile = create_profile(
            negative_titles=[],
            negative_keywords=["lead generation", "cold calling"],
        )
        filter_obj = ProfileJobFilter(profile)

        job = create_job("Lead Generation Specialist", "Outbound calling for leads")
        accepted, rejected = filter_obj.filter_jobs([job])

        assert len(accepted) == 0
        assert len(rejected) == 1

    def test_reject_telesales(self):
        """Test that Telesales is rejected."""
        profile = create_profile(
            negative_titles=["Telesales"],
            negative_keywords=["outbound calling"],
        )
        filter_obj = ProfileJobFilter(profile)

        job = create_job("Telesales Executive", "Outbound calling")
        accepted, rejected = filter_obj.filter_jobs([job])

        assert len(accepted) == 0
        assert len(rejected) == 1

    def test_mixed_jobs_filtering(self):
        """Test filtering a mix of accepted and rejected jobs."""
        profile = create_profile(
            negative_titles=["Sales Executive", "BPO"],
            negative_keywords=["cold calling", "pre-sales", "voice process"],
        )
        filter_obj = ProfileJobFilter(profile)

        jobs = [
            create_job("CRM Manager", "CleverTap lifecycle campaigns"),
            create_job("Pre Sales Executive", "Cold calling for lead generation"),
            create_job("CRM Lead", "Customer journey mapping"),
            create_job("Voice Process Executive", "BPO customer support"),
            create_job("Retention Manager", "Customer retention strategies"),
        ]
        accepted, rejected = filter_obj.filter_jobs(jobs)

        assert len(accepted) == 3
        assert len(rejected) == 2

        accepted_titles = [j.title for j in accepted]
        rejected_titles = [j.title for j in rejected]

        assert "CRM Manager" in accepted_titles
        assert "CRM Lead" in accepted_titles
        assert "Retention Manager" in accepted_titles
        assert "Pre Sales Executive" in rejected_titles
        assert "Voice Process Executive" in rejected_titles

    def test_case_insensitive_keyword_matching(self):
        """Test that negative keyword matching is case insensitive."""
        profile = create_profile(
            negative_titles=[],
            negative_keywords=["cold calling"],
        )
        filter_obj = ProfileJobFilter(profile)

        job = create_job("Sales Rep", "COLD CALLING experience")
        accepted, rejected = filter_obj.filter_jobs([job])

        assert len(accepted) == 0
        assert len(rejected) == 1

    def test_partial_keyword_not_matched(self):
        """Test that partial keyword matches are not rejected."""
        profile = create_profile(
            negative_titles=[],
            negative_keywords=["sales"],
        )
        filter_obj = ProfileJobFilter(profile)

        job = create_job("Salesforce Developer", "Salesforce CRM development")
        accepted, rejected = filter_obj.filter_jobs([job])

        assert len(accepted) == 1
        assert len(rejected) == 0

    def test_empty_description(self):
        """Test that jobs with empty description are handled."""
        profile = create_profile(
            negative_titles=[],
            negative_keywords=["cold calling"],
        )
        filter_obj = ProfileJobFilter(profile)

        job = create_job("CRM Manager", "")
        accepted, rejected = filter_obj.filter_jobs([job])

        assert len(accepted) == 1
        assert len(rejected) == 0

    def test_empty_negative_keywords(self):
        """Test that all jobs are accepted when no negative keywords."""
        profile = create_profile(negative_titles=[], negative_keywords=[])
        filter_obj = ProfileJobFilter(profile)

        jobs = [
            create_job("CRM Manager", "Lifecycle campaigns"),
            create_job("Sales Executive", "Sales"),
        ]
        accepted, rejected = filter_obj.filter_jobs(jobs)

        assert len(accepted) == 2
        assert len(rejected) == 0

def test_reject_technical_job_with_crm_tool():
    profile = create_profile(
        negative_titles=[
            "Salesforce Developer",
            "Technical Architect",
            "Data Engineer",
            "Backend Developer",
        ],
        negative_keywords=[],
    )
    filter_obj = ProfileJobFilter(profile)

    jobs = [
        create_job(
            "Technical Architect",
            "Experience with Netcore Cloud and enterprise integrations.",
        ),
        create_job(
            "Data Engineer",
            "Build pipelines using Adobe Experience Cloud and SQL.",
        ),
        create_job(
            "Salesforce Developer",
            "Develop Salesforce Marketing Cloud integrations.",
        ),
    ]

    accepted, rejected = filter_obj.filter_jobs(jobs)

    assert accepted == []
    assert len(rejected) == 3


def test_accept_crm_role_with_real_lifecycle_evidence():
    profile = create_profile(
        negative_titles=["Sales", "BPO"],
        negative_keywords=[],
    )
    filter_obj = ProfileJobFilter(profile)

    job = create_job(
        "CRM Manager",
        (
            "Hands-on experience with MoEngage for journey setup, "
            "segmentation and analytics. Manage Email, SMS, WhatsApp "
            "and Push campaigns."
        ),
    )

    accepted, rejected = filter_obj.filter_jobs([job])

    assert len(accepted) == 1
    assert rejected == []


def test_reject_generic_marketing_without_crm_evidence():
    profile = create_crm_profile()
    profile.negative_titles = ["Sales", "BPO"]
    profile.negative_keywords = []
    filter_obj = ProfileJobFilter(profile)

    job = create_job(
        "Marketing Manager",
        (
            "Manage SEO, Google Ads, content marketing and website "
            "performance."
        ),
    )

    accepted, rejected = filter_obj.filter_jobs([job])

    assert accepted == []
    assert len(rejected) == 1
