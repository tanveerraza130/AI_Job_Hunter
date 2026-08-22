#!/usr/bin/env python3
"""
Debug script for Scoring Engine.

This script captures the ACTUAL runtime behavior of the scoring engine.
Do not compare against predetermined values.

Use the printed output as the ground truth for writing regression tests.
"""

from jobs.intelligence.models import JobIntelligence, WeightedItem
from jobs.profiles.loader import load_profile
from jobs.scoring.engine import ProfileScoringEngine


def create_perfect_intelligence():
    """Create JobIntelligence with all profile skills and tools."""
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


def create_partial_intelligence():
    """Create JobIntelligence with partial skills and tools."""
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


def print_result(title, result):
    """Print scoring result in a readable format."""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print(f"{'=' * 60}")
    print(f"Skill Score:      {result.breakdown.skill_match}")
    print(f"Tool Score:       {result.breakdown.tool_match}")
    print(f"Experience Score: {result.breakdown.experience_match}")
    print(f"Salary Score:     {result.breakdown.salary_match}")
    print(f"Work Mode Score:  {result.breakdown.work_mode_match}")
    print(f"Final Score:      {result.score}")
    print(f"{'=' * 60}")

    print("\nBreakdown Object:")
    print(result.breakdown)

    print("\nScore Object:")
    print(result)


def main():
    """Run debug scenarios."""
    print("\n" + "=" * 60)
    print("SCORING ENGINE DEBUG")
    print("=" * 60)

    # Load profile
    profile = load_profile("crm_manager")
    print(f"\nProfile: {profile.profile_name}")
    print(f"Skills: {len(profile.skills)}")
    print(f"Tools: {len(profile.tools)}")
    print(f"Experience: {profile.experience_min}-{profile.experience_max} years")
    print(f"Salary: {profile.salary_min}-{profile.salary_max}")
    print(f"Work Modes: {profile.work_modes}")

    # Create engine
    engine = ProfileScoringEngine("crm_manager")

    # Scenario 1: Perfect match
    perfect_intelligence = create_perfect_intelligence()
    result = engine.score_job(perfect_intelligence)
    print_result("PERFECT MATCH", result)

    # Scenario 2: Partial match
    partial_intelligence = create_partial_intelligence()
    result = engine.score_job(partial_intelligence)
    print_result("PARTIAL MATCH", result)

    # Scenario 3: Empty intelligence
    empty_intelligence = JobIntelligence()
    result = engine.score_job(empty_intelligence)
    print_result("EMPTY INTELLIGENCE", result)

    print("\n" + "=" * 60)
    print("DEBUG COMPLETE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()