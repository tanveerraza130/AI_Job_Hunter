"""
Tests for ProfileJobFilter.
"""

import pytest

from jobs.filtering.profile_filter import ProfileJobFilter
from jobs.job import Job
from jobs.profiles.profile import Profile
from jobs.profiles.loader import ConfigLoader
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



def test_accept_sfmc_platform_implementation_lead():
    profile = ConfigLoader.load_profile("crm_implementation_manager")
    filter_obj = ProfileJobFilter(profile)

    job = Job(
        job_id="sfmc-regression",
        title="SFMC Platform Implementation Lead",
        company="Test Company",
        location="India",
        description=(
            "Experience with SFDC, SF Personalization, architecting, "
            "design and strong hands-on experience with Marketing Cloud."
        ),
        job_url="https://example.com/sfmc",
        portal="naukri",
    )

    assert filter_obj._positive_relevance(job) is True


def test_reject_concur_implementation_manager_for_crm_profile():
    profile = ConfigLoader.load_profile("crm_implementation_manager")
    filter_obj = ProfileJobFilter(profile)

    job = Job(
        job_id="concur-regression",
        title="Concur Implementation Manager",
        company="Test Company",
        location="India",
        description=(
            "SAP Concur spend management, financial and payroll systems, "
            "SAP ICS native integration and Concur Web API."
        ),
        job_url="https://example.com/concur",
        portal="naukri",
    )

    assert filter_obj._positive_relevance(job) is False


def test_reject_generic_saas_implementation_manager_for_crm_profile():
    profile = ConfigLoader.load_profile("crm_implementation_manager")
    filter_obj = ProfileJobFilter(profile)

    job = Job(
        job_id="saas-regression",
        title="Technical Implementation Manager",
        company="Test Company",
        location="India",
        description=(
            "Experience in SaaS, ecommerce, retail tech, logistics, "
            "enterprise platforms, customer experience and adoption."
        ),
        job_url="https://example.com/saas",
        portal="naukri",
    )

    assert filter_obj._positive_relevance(job) is False


def test_accept_salesforce_implementation_lead_with_short_description():
    profile = ConfigLoader.load_profile("crm_implementation_manager")
    filter_obj = ProfileJobFilter(profile)
    job = Job(
        job_id="salesforce-implementation-lead",
        title="Salesforce Implementation Lead",
        company="Test Company",
        location="India",
        description="Salesforce Administrator and Consultant experience required.",
        job_url="https://example.com/salesforce-implementation",
        portal="naukri",
    )
    assert filter_obj._positive_relevance(job) is True


def test_accept_salesforce_delivery_manager_with_delivery_ownership():
    profile = ConfigLoader.load_profile("crm_implementation_manager")
    filter_obj = ProfileJobFilter(profile)
    job = Job(
        job_id="salesforce-delivery-manager",
        title="Salesforce Delivery Manager",
        company="Test Company",
        location="India",
        description=(
            "Own Salesforce project delivery across client engagements, "
            "manage stakeholders, integrations, deployment and go-live."
        ),
        job_url="https://example.com/salesforce-delivery",
        portal="naukri",
    )
    assert filter_obj._positive_relevance(job) is True


def test_accept_salesforce_service_delivery_manager():
    profile = ConfigLoader.load_profile("crm_implementation_manager")
    filter_obj = ProfileJobFilter(profile)
    job = Job(
        job_id="salesforce-service-delivery",
        title="Salesforce Service Delivery Manager",
        company="Test Company",
        location="India",
        description=(
            "Lead Salesforce implementation projects, manage client "
            "stakeholders, delivery governance, UAT and platform adoption."
        ),
        job_url="https://example.com/salesforce-service-delivery",
        portal="naukri",
    )
    assert filter_obj._positive_relevance(job) is True


def test_accept_salesforce_technical_delivery_manager_with_integration_scope():
    profile = ConfigLoader.load_profile("crm_implementation_manager")
    filter_obj = ProfileJobFilter(profile)
    job = Job(
        job_id="salesforce-technical-delivery",
        title="Salesforce Technical Delivery Manager",
        company="Test Company",
        location="India",
        description=(
            "Own Salesforce multi-cloud implementation and client delivery, "
            "including integrations, project governance, deployment and UAT."
        ),
        job_url="https://example.com/salesforce-technical-delivery",
        portal="naukri",
    )
    assert filter_obj._positive_relevance(job) is True


def test_reject_generic_implementation_consultant_with_only_crm_familiarity():
    profile = ConfigLoader.load_profile("crm_implementation_manager")
    filter_obj = ProfileJobFilter(profile)
    job = Job(
        job_id="generic-crm-familiarity",
        title="Implementation Consultant",
        company="Test Company",
        location="India",
        description=(
            "Commerce platform onboarding. Experience using a CRM platform "
            "is preferred."
        ),
        job_url="https://example.com/generic-consultant",
        portal="naukri",
    )
    assert filter_obj._positive_relevance(job) is False


def test_reject_salesforce_technical_delivery_role_that_is_pure_development():
    profile = ConfigLoader.load_profile("crm_implementation_manager")
    filter_obj = ProfileJobFilter(profile)
    job = Job(
        job_id="salesforce-pure-development",
        title="Salesforce Technical Delivery Manager",
        company="Test Company",
        location="India",
        description=(
            "Hands-on Apex Triggers, Batch Classes, LWC, Aura components "
            "and Apex development."
        ),
        job_url="https://example.com/salesforce-development",
        portal="naukri",
    )
    assert filter_obj._positive_relevance(job) is False


def test_reject_erp_implementation_with_incidental_dynamics_reference():
    profile = ConfigLoader.load_profile("crm_implementation_manager")
    filter_obj = ProfileJobFilter(profile)
    job = Job(
        job_id="erp-incidental-dynamics",
        title="ERP Implementation Manager",
        company="Test Company",
        location="India",
        description=(
            "Lead ERP implementation. Microsoft Dynamics 365 experience "
            "is preferred."
        ),
        job_url="https://example.com/erp-implementation",
        portal="naukri",
    )
    assert filter_obj._positive_relevance(job) is False
