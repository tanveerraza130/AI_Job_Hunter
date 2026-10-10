"""
Profile-based job filter.

Filters jobs based on profile negative titles and negative keywords.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Tuple

import yaml

from jobs.job import Job
from jobs.profiles.profile import Profile

logger = logging.getLogger(__name__)


class ProfileJobFilter:
    """
    Filters jobs based on profile criteria.

    Responsibilities:
    - Exclude jobs with negative titles
    - Exclude jobs with negative keywords in title/description
    - (Future) Apply location filters
    """

    def __init__(self, profile: Profile):
        """
        Initialize the profile relevance filter.

        Filtering is intentionally two-sided:

        1. Negative exclusion rules reject known noise.
        2. Positive relevance rules require evidence that the job belongs
           to the active profile.

        This prevents broad portal search results from entering the
        scoring/persistence pipeline merely because they did not match
        a negative rule.
        """
        self.profile = profile

        self._negative_title_patterns = (
            self._compile_negative_title_patterns()
        )
        self._negative_keyword_patterns = (
            self._compile_negative_keyword_patterns()
        )

        self._strong_titles = []
        self._weak_titles = []
        self._mandatory_skills = []
        self._core_skills = []
        self._preferred_skills = []

        self._load_positive_relevance_rules()

    def _compile_negative_title_patterns(self) -> List[re.Pattern]:
        """
        Compile negative title patterns for efficient matching.

        Uses word boundaries to avoid false positives.
        Example: "Sales" should not match "Salesforce".
        """
        patterns = []
        for title in self.profile.negative_titles:
            pattern = re.compile(r"\b" + re.escape(title) + r"\b", re.IGNORECASE)
            patterns.append(pattern)
        return patterns

    def _compile_negative_keyword_patterns(self) -> List[re.Pattern]:
        """
        Compile negative keyword patterns for efficient matching.

        Uses word boundaries to avoid false positives.
        """
        patterns = []
        for keyword in self.profile.negative_keywords:
            pattern = re.compile(r"\b" + re.escape(keyword) + r"\b", re.IGNORECASE)
            patterns.append(pattern)
        return patterns

    def _load_positive_relevance_rules(self) -> None:
        """
        Load positive relevance rules from the active profile.

        The filter remains generic: all rules are read from the profile
        configuration directory. If a synthetic/test profile has no
        scoring configuration, the historical negative-only behaviour
        remains available for backwards-compatible unit tests.
        """
        profile_id = getattr(self.profile, "profile_id", "")
        if not profile_id:
            return

        profile_dir = (
            Path(__file__).resolve().parents[1]
            / "profiles"
            / profile_id
        )

        matching_path = profile_dir / "scoring" / "matching.yaml"
        titles_path = profile_dir / "scoring" / "titles.yaml"
        weights_path = profile_dir / "scoring" / "weights.yaml"

        if not matching_path.exists():
            return

        with matching_path.open("r", encoding="utf-8") as handle:
            matching = yaml.safe_load(handle) or {}

        self._mandatory_skills = [
            str(x).strip().lower()
            for x in matching.get("mandatory_skills", [])
            if str(x).strip()
        ]

        self._preferred_skills = [
            str(x).strip().lower()
            for x in matching.get("preferred_skills", [])
            if str(x).strip()
        ]

        if weights_path.exists():
            with weights_path.open(
                "r",
                encoding="utf-8",
            ) as handle:
                weights = yaml.safe_load(handle) or {}

            skill_weights = weights.get(
                "skill_weights",
                {},
            )

            self._core_skills = [
                str(x).strip().lower()
                for x in skill_weights.get(
                    "core_skills",
                    [],
                )
                if str(x).strip()
            ]

        if titles_path.exists():
            with titles_path.open(
                "r",
                encoding="utf-8",
            ) as handle:
                titles = yaml.safe_load(handle) or {}

            strong = titles.get("strong", {})
            weak = titles.get("weak", {})

            self._strong_titles = [
                str(x).strip().lower()
                for x in strong.get("titles", [])
                if str(x).strip()
            ]

            self._weak_titles = [
                str(x).strip().lower()
                for x in weak.get("titles", [])
                if str(x).strip()
            ]

    def _positive_relevance(self, job: Job) -> bool:
        """
        Require substantive CRM/MarTech role evidence.

        Rules:
        1. Explicit CRM/MarTech/lifecycle/retention title qualifies.
        2. Technical titles never qualify merely because a CRM tool
           appears in the JD.
        3. Generic titles require either:
           - a dedicated CRM/MarTech tool + CRM capability, or
           - two independent CRM capability groups.
        4. A single generic CRM taxonomy term is insufficient.
        """
        if (
            not self._mandatory_skills
            and not self._core_skills
        ):
            return True

        title = (job.title or "").strip().lower()
        description = (job.description or "").strip().lower()
        combined = f"{title} {description}"

        # ------------------------------------------------------
        # Technical / engineering roles MUST be checked FIRST.
        #
        # A title like "Dynamics 365 CRM Developer" contains "crm"
        # but is still a technical role and must be rejected.
        # ------------------------------------------------------
        technical_title_signals = (
            "developer",
            "engineer",
            "technical consultant",
            "technical architect",
            "solution architect",
            "data scientist",
            "data engineer",
            "software engineer",
            "software developer",
            "machine learning",
            "ml ops",
            "full stack",
            "backend",
            "frontend",
            "implementation consultant",
            "system administrator",
            "powerbuilder",
            "technical lead",
            "technical manager",
            "d365",
            "dynamics 365",
            "dynamics crm",
            "salesforce developer",
            "salesforce admin",
            "salesforce administrator",
            "copilot",
            "power platform",
            # Added: reject these non-CRM roles
            "architect",
            "data analyst",
            "business analyst",
            "system admin",
            "administrator",
            "veeva",
            "zoho",
            "shopify",
            "back office",
            "banking",
            "real estate",
            "field executive",
            "field sales",
            "offline sales",
            "it sales",
            "pre-sale",
            "pre sale",
            "pre sales",
            "investor relations",
            "political",
            "publisher",
            "meta ads",
            "google ads",
            "search ads",
            "social media",
            "debt recovery",
            "loan against",
            "franchise service",
            "sales transformation",
            # Final additions
            "immigration",
            "social campaign",
            "publisher campaign",
            "political campaign",
            "meta ads campaign",
            "google ads campaign",
            "search ads campaign",
            "hyper personalization",
            "hyperpersonalization",
            "email marketing specialist",
            "ecommerce",
            "e-commerce",
        )

        if any(signal in title for signal in technical_title_signals):
            return False

        # ------------------------------------------------------
        # Reject if title contains sales-specific signals
        # even when CRM/retention keyword is present
        # ------------------------------------------------------
        sales_overrides = (
            "sales",
            "client servicing",
            "client success",
            "client retention",
            "upsell",
            "cross-sell",
            "cross sell",
            "field",
            "door to door",
            "real estate",
            "insurance",
            "loan",
        )

        # Only reject if title has "sales" AND not other strong CRM signals
        title_sales = any(sig in title for sig in sales_overrides)
        title_strong_crm = any(
            sig in title for sig in (
                "crm manager", "crm executive", "crm lead", "crm head",
                "head of crm", "crm specialist", "crm analyst",
                "lifecycle marketing", "retention marketing",
                "loyalty marketing", "marketing automation",
                "marketing automation manager", "martech manager",
                "customer lifecycle", "crm campaign",
            )
        )

        if title_sales and not title_strong_crm:
            return False

        # ------------------------------------------------------
        # Explicit CRM / MarTech role titles
        # ------------------------------------------------------
        strong_role_signals = (
            "crm",
            "martech",
            "mar tech",
            "lifecycle marketing",
            "retention marketing",
            "retention manager",
            "retention lead",
            "retention head",
            "retention specialist",
            "retention executive",
            "retention analyst",
            "customer lifecycle",
            "customer engagement",
            "marketing automation",
            "campaign management",
            "campaign automation",
            "campaign manager",
            "customer journey",
            "journey orchestration",
            "personalization",
            "loyalty marketing",
            "loyalty manager",
            "loyalty lead",
            "customer marketing",
            "customer retention",
            "growth crm",
        )

        if any(signal in title for signal in strong_role_signals):
            return True

        # ------------------------------------------------------
        # Dedicated CRM / MarTech platforms
        # ------------------------------------------------------
        crm_tools = {
            "clevertap",
            "moengage",
            "webengage",
            "netcore cloud",
            "braze",
            "insider",
            "customer.io",
            "mailmodo",
            "onesignal",
            "salesforce marketing cloud",
            "adobe experience cloud",
            "adobe campaign",
            "marketo",
            "klaviyo",
            "activecampaign",
            "blueshift",
            "airship",
            "hubspot",
            "leadsquared",
            "tealium",
            "segment",
            "mparticle",
            "rudderstack",
            "hightouch",
            "census",
        }

        tool_hits = {
            tool
            for tool in crm_tools
            if re.search(
                r"\b" + re.escape(tool) + r"\b",
                combined,
                re.IGNORECASE,
            )
        }

        # ------------------------------------------------------
        # Independent CRM capability groups.
        #
        # Do NOT count five aliases from the same capability as
        # five independent signals.
        # ------------------------------------------------------
        capability_groups = {
            "lifecycle_retention": (
                "lifecycle marketing",
                "customer lifecycle",
                "retention marketing",
                "retention",
                "churn reduction",
                "win back",
                "win-back",
            ),
            "campaign_automation": (
                "campaign management",
                "campaign automation",
                "marketing automation",
                "journey orchestration",
                "journey builder",
                "triggered campaigns",
            ),
            "engagement_personalization": (
                "customer engagement",
                "customer journey",
                "personalization",
                "segmentation",
                "loyalty program",
                "loyalty marketing",
            ),
            "crm_strategy": (
                "crm strategy",
                "crm analytics",
                "customer marketing",
                "customer lifecycle strategy",
            ),
            "crm_channels": (
                "whatsapp marketing",
                "sms marketing",
                "push notification",
                "omnichannel communication",
            ),
        }

        matched_groups = set()

        for group, signals in capability_groups.items():
            if any(
                re.search(
                    r"\b" + re.escape(signal) + r"\b",
                    combined,
                    re.IGNORECASE,
                )
                for signal in signals
            ):
                matched_groups.add(group)

        # Tool + one core CRM capability.
        #
        # Communication channels alone (SMS / WhatsApp / Push /
        # Omnichannel) do not establish that a generic role is a
        # CRM/MarTech role. They are supporting evidence only.
        core_groups = matched_groups - {
            "crm_channels",
        }

        if tool_hits and core_groups:
            return True

        # Generic title/JD requires two independent CORE CRM domains.
        return len(core_groups) >= 2

    def filter_jobs(self, jobs: List[Job]) -> Tuple[List[Job], List[Job]]:
        """
        Filter jobs based on profile criteria.

        Diagnostic mode reports the exact rejection stage and
        per-rule counts without changing filtering behaviour.
        """
        from collections import Counter

        accepted = []
        rejected = []

        title_rejections = Counter()
        keyword_rejections = Counter()
        positive_rejections = []

        for job in jobs:

            # ------------------------------------------------------
            # 1. Negative title
            # ------------------------------------------------------
            if self._has_negative_title(job):
                rejected.append(job)

                title_lower = (job.title or "").lower()

                matched = [
                    title
                    for title in self.profile.negative_titles
                    if re.search(
                        r"\b" + re.escape(title) + r"\b",
                        title_lower,
                        re.IGNORECASE,
                    )
                ]

                if matched:
                    for title in matched:
                        title_rejections[title] += 1
                else:
                    title_rejections["<matched-but-unidentified>"] += 1

                continue

            # ------------------------------------------------------
            # 2. Negative keyword
            # ------------------------------------------------------
            if self._has_negative_keyword(job):
                rejected.append(job)

                combined_text = (
                    f"{job.title or ''} {job.description or ''}"
                ).lower()

                matched = [
                    keyword
                    for keyword in self.profile.negative_keywords
                    if re.search(
                        r"\b" + re.escape(keyword) + r"\b",
                        combined_text,
                        re.IGNORECASE,
                    )
                ]

                if matched:
                    for keyword in matched:
                        keyword_rejections[keyword] += 1
                else:
                    keyword_rejections["<matched-but-unidentified>"] += 1

                continue

            # ------------------------------------------------------
            # 3. Positive relevance
            # ------------------------------------------------------
            if self._positive_relevance(job):
                accepted.append(job)
            else:
                rejected.append(job)
                positive_rejections.append(job)

        # ----------------------------------------------------------
        # Detailed diagnostic report
        # ----------------------------------------------------------

        print("")
        print("=" * 72)
        print("CRM PROFILE FILTER — DETAILED RECONCILIATION")
        print("=" * 72)

        print(f"Jobs entering profile filter : {len(jobs):,}")
        print(f"Accepted by CRM profile      : {len(accepted):,}")
        print(f"Rejected by CRM profile      : {len(rejected):,}")
        print("")

        print("-" * 72)
        print("REJECTION STAGE SUMMARY")
        print("-" * 72)

        title_total = sum(title_rejections.values())
        keyword_total = sum(keyword_rejections.values())
        positive_total = len(positive_rejections)

        print(f"Negative TITLE rejection     : {title_total:,}")
        print(f"Negative KEYWORD rejection   : {keyword_total:,}")
        print(f"Positive relevance rejection : {positive_total:,}")
        print(f"Accepted                     : {len(accepted):,}")
        print(
            f"Reconciled total             : "
            f"{title_total + keyword_total + positive_total + len(accepted):,}"
        )

        print("")
        print("-" * 72)
        print("NEGATIVE TITLE — PER RULE")
        print("-" * 72)

        if title_rejections:
            for rule, count in title_rejections.most_common():
                print(f"{count:6,}  |  {rule}")
        else:
            print("No negative-title rejections.")

        print("")
        print("-" * 72)
        print("NEGATIVE KEYWORD — PER RULE")
        print("-" * 72)

        if keyword_rejections:
            for rule, count in keyword_rejections.most_common():
                print(f"{count:6,}  |  {rule}")
        else:
            print("No negative-keyword rejections.")

        print("")
        print("-" * 72)
        print("POSITIVE RELEVANCE REJECTIONS — SAMPLE")
        print("-" * 72)

        for job in positive_rejections[:30]:
            print(
                f"- {job.title or '<NO TITLE>'} | "
                f"{job.company or '<NO COMPANY>'}"
            )

        print("")
        print("-" * 72)
        print("ACCEPTED CRM JOBS — SAMPLE")
        print("-" * 72)

        for job in accepted[:30]:
            print(
                f"+ {job.title or '<NO TITLE>'} | "
                f"{job.company or '<NO COMPANY>'}"
            )

        print("=" * 72)
        print("END CRM PROFILE FILTER DIAGNOSTIC")
        print("=" * 72)
        print("")

        logger.info(
            "PROFILE FILTER RESULT: accepted=%s rejected=%s "
            "negative_title=%s negative_keyword=%s "
            "positive_relevance=%s",
            len(accepted),
            len(rejected),
            title_total,
            keyword_total,
            positive_total,
        )

        return accepted, rejected

    def _is_accepted(self, job: Job) -> bool:
        """
        Check if a job passes all filters.

        Args:
            job: Job to check.

        Returns:
            True if accepted, False if rejected.
        """
        # Negative exclusions always take precedence.
        if self._has_negative_title(job):
            return False

        if self._has_negative_keyword(job):
            return False

        # Positive profile relevance is required for configured profiles.
        return self._positive_relevance(job)

    def _has_negative_title(self, job: Job) -> bool:
        """
        Check if job title matches any negative pattern.

        Args:
            job: Job to check.

        Returns:
            True if job title matches a negative pattern.
        """
        if not job.title:
            return False

        title_lower = job.title.lower()

        for pattern in self._negative_title_patterns:
            if pattern.search(title_lower):
                return True

        return False

    def _has_negative_keyword(self, job: Job) -> bool:
        """
        Check if job title or description matches any negative keyword pattern.

        Args:
            job: Job to check.

        Returns:
            True if job title or description matches a negative keyword pattern.
        """
        # Build combined text for checking
        combined_text = ""
        if job.title:
            combined_text += job.title.lower() + " "
        if job.description:
            combined_text += job.description.lower()

        if not combined_text:
            return False

        for pattern in self._negative_keyword_patterns:
            if pattern.search(combined_text):
                return True

        return False