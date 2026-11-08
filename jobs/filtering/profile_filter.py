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

    def _profile_specific_positive_relevance(self, job: Job) -> bool:
        """
        Positive relevance for non-crm_manager profiles.

        Accept only when:
          1. Title matches a strong title from this profile's titles.yaml, or
          2. Title matches a weak title AND JD contains >=1 mandatory skill, or
          3. Title contains a recognised domain word AND JD contains >=2 mandatory skills.

        Rejects titles like "Grants Manager", "Trainer", "Finops Manager",
        "Scrum Master", "Hardware Sales Head" that slipped through with the
        earlier permissive fallback.
        """
        import re as _re

        title = (job.title or "").strip().lower()
        description = (job.description or "").strip().lower()
        if not title:
            return False

        def _wb(candidate: str, haystack: str) -> bool:
            c = candidate.strip().lower()
            if not c:
                return False
            return _re.search(
                r"(?<![a-z0-9])" + _re.escape(c) + r"(?![a-z0-9])",
                haystack,
            ) is not None

        def _count_mandatory() -> int:
            n = 0
            for skill in self._mandatory_skills:
                if _wb(skill, description):
                    n += 1
            return n

        # 1. Strong title -> accept
        if any(_wb(t, title) for t in self._strong_titles):
            return True

        # 2. Weak title + >=1 mandatory skill -> accept
        if any(_wb(t, title) for t in self._weak_titles):
            return _count_mandatory() >= 1

        # 3. Domain words in title -> require CRM context.
        #    crm_implementation_manager must only accept roles with an
        #    explicit CRM signal (platform / acronym / CRM-adjacent tool).
        domain_words = (
            "implementation",
            "onboarding",
            "delivery",
            "go-live",
            "deployment",
            "professional services",
            "solution delivery",
            "solutions delivery",
        )
        if any(_wb(dw, title) for dw in domain_words):
            crm_signals = (
                "salesforce", "sfdc",
                "dynamics", "d365", "microsoft dynamic", "ms dynamic",
                "crm", "hubspot", "zoho", "leadsquared", "freshsales",
                "freshworks", "sugarcrm", "pipedrive", "netsuite", "sap cx",
                "customer relationship", "customer lifecycle",
                "coupa", "jaggaer", "clm", "contract lifecycle",
                "professional services",
            )
            haystack = title + " " + description
            if not any(_wb(sig, haystack) for sig in crm_signals):
                return False
            return _count_mandatory() >= 1

        return False

    def _crm_implementation_positive_relevance(self, job: Job) -> bool:
        """Require CRM platform relevance and genuine implementation/delivery scope."""

        title = (job.title or "").strip().lower()
        description = (job.description or "").strip().lower()
        combined = f"{title} {description}"

        if not title:
            return False

        def has_any(text: str, terms: tuple[str, ...]) -> bool:
            return any(
                re.search(
                    r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])",
                    text,
                )
                for term in terms
            )

        unrelated_title = (
            "erp implementation", "hris implementation",
            "hrms implementation", "payroll implementation",
            "database implementation", "db implementation",
            "wms implementation", "pos implementation",
        )
        unrelated_body = (
            "pension administration", "defined benefit plans",
            "cybersecurity suite", "endpoint management",
            "manufacturing plant operations", "workday implementation",
            "sap abap",
        )
        if has_any(title, unrelated_title) or has_any(combined, unrelated_body):
            return False

        technical_exclusions = (
            "software developer", "salesforce developer",
            "dynamics developer", "software engineer",
            "data engineer", "backend developer",
            "frontend developer", "application developer",
        )
        if has_any(title, technical_exclusions):
            return False

        implementation_role = has_any(
            title,
            (
                "implementation", "deployment",
                "professional services", "onboarding manager",
            ),
        )
        delivery_role = has_any(
            title,
            (
                "solution delivery", "solutions delivery",
                "delivery manager", "service delivery manager",
                "technical delivery manager", "delivery lead",
            ),
        )

        if not implementation_role and not delivery_role:
            return False

        crm_platforms = (
            "salesforce", "sfdc", "sales cloud", "service cloud",
            "salesforce marketing cloud", "sfmc", "dynamics 365",
            "dynamics crm", "microsoft dynamics", "hubspot",
            "zoho crm", "freshsales", "leadsquared", "sugarcrm",
            "pipedrive", "sap crm", "oracle cx",
            "oracle customer experience",
        )

        platform_in_title = has_any(title, crm_platforms)
        platform_in_description = has_any(description, crm_platforms)

        if not platform_in_title and not platform_in_description:
            return False

        lifecycle_evidence = has_any(
            description,
            (
                "requirements gathering", "requirements discovery",
                "discovery workshop", "solution design", "process mapping",
                "data migration", "configuration", "workflow", "go-live",
                "user acceptance testing", "uat", "deployment",
                "implementation lifecycle", "integration",
            ),
        )

        delivery_evidence = has_any(
            description,
            (
                "customer onboarding", "client onboarding",
                "stakeholder management", "project management",
                "implementation project", "project delivery",
                "program delivery", "portfolio delivery",
                "delivery governance", "client delivery",
                "user training", "change management",
                "data integration", "workflow automation",
                "platform adoption",
            ),
        )

        coding_evidence = has_any(
            description,
            (
                "apex triggers", "batch classes", "batch apex",
                "lightning web components", "lwc", "aura components",
                "apex development", "software coding",
                "developing custom code",
            ),
        )

        # Explicit CRM implementation titles are strong enough to qualify.
        if platform_in_title and implementation_role:
            return True

        # CRM delivery titles must demonstrate actual delivery ownership.
        if platform_in_title and delivery_role:
            if coding_evidence and not delivery_evidence:
                return False
            return lifecycle_evidence or delivery_evidence

        # Generic CRM-implementation titles are strong signals on their own,
        # even when the platform name is only implied.
        if implementation_role:
            if lifecycle_evidence or delivery_evidence:
                return True

        # Generic implementation titles with platform evidence but no
        # implementation_role in title still need both pieces.
        _final = (
            platform_in_description
            and lifecycle_evidence
            and delivery_evidence
        )
        return _final

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

        # CRM Implementation Manager uses a dedicated strict gate.
        # This must run before generic strong/weak title matching.
        if getattr(self.profile, "profile_id", "") == "crm_implementation_manager":
            return self._crm_implementation_positive_relevance(job)

        # -- Honor profile-owned titles.yaml (strong / weak) first.
        # A title that explicitly matches the profile's own strong/weak
        # title list qualifies as positive relevance regardless of the
        # hardcoded CRM-Manager-shaped heuristics below.
        if self._strong_titles or self._weak_titles:
            import re as _re
            def _title_match(candidate: str) -> bool:
                c = candidate.strip().lower()
                if not c:
                    return False
                pattern = r"(?<![a-z0-9])" + _re.escape(c) + r"(?![a-z0-9])"
                return _re.search(pattern, title) is not None

            if any(_title_match(t) for t in self._strong_titles):
                return True
            if any(_title_match(t) for t in self._weak_titles):
                return True
        combined = f"{title} {description}"

        # ------------------------------------------------------
        # Hardcoded CRM-Manager heuristics — only apply to crm_manager.
        # Other profiles must be driven by their own titles.yaml /
        # matching.yaml configuration (see profile-owned titles check
        # above). Applying these to crm_implementation_manager was
        # rejecting valid "Implementation Manager" titles.
        # ------------------------------------------------------
        if getattr(self.profile, "profile_id", "") != "crm_manager":
            return self._profile_specific_positive_relevance(job)

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

        if getattr(self.profile, "profile_id", "") == "crm_implementation_manager":
            allow_functional_titles = {
                "implementation consultant",
                "technical implementation manager",
                "technical manager",
                "d365",
                "dynamics 365",
                "dynamics crm",
                "copilot",
                "power platform",
                "architect",
                "system admin",
                "administrator",
                "veeva",
                "zoho",
                "shopify",
                "engineer",
                "publisher",
            }
            technical_title_signals = tuple(
                signal for signal in technical_title_signals
                if signal not in allow_functional_titles
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
        # CRM Implementation Manager: require relevant CRM platform
        # evidence and implementation responsibilities. Keep this
        # profile-specific so other profiles retain their existing rules.
        if getattr(self.profile, "profile_id", "") == "crm_implementation_manager":
            title_text = title
            body_text = combined

            # Exclude clearly unrelated implementation domains.
            unrelated_title = any(
                term in title_text for term in (
                    "erp implementation",
                    "hris implementation",
                    "hrms implementation",
                    "payroll implementation",
                    "database implementation",
                    "db implementation",
                    "wms implementation",
                    "pos implementation",
                )
            )
            unrelated_body = any(
                term in body_text for term in (
                    "pension administration",
                    "defined benefit plans",
                    "cybersecurity suite",
                    "endpoint management",
                    "manufacturing plant operations",
                    "workday implementation",
                    "sap abap",
                )
            )
            if unrelated_title or unrelated_body:
                return False

            implementation_role = any(
                term in title_text for term in (
                    "implementation", "deployment", "solution delivery",
                    "professional services", "onboarding manager",
                )
            )

            # Explicit Salesforce Marketing Cloud implementation titles
            # are strong platform evidence even when the captured JD is short.
            sfmc_implementation_title = (
                implementation_role
                and any(
                    term in title_text
                    for term in (
                        "sfmc",
                        "salesforce marketing cloud",
                        "marketing cloud",
                    )
                )
            )
            if sfmc_implementation_title:
                return True

            crm_platform = any(
                term in body_text for term in (
                    "salesforce", "dynamics 365", "dynamics crm",
                    "hubspot", "zoho crm", "freshsales", "leadsquared",
                    "sugarcrm", "pipedrive", "sap crm", "oracle cx",
                    "oracle customer experience",
                )
            )

            lifecycle = any(
                term in body_text for term in (
                    "requirements gathering", "requirements discovery",
                    "discovery workshop", "solution design",
                    "process mapping", "data migration",
                    "configuration", "workflow", "go-live",
                    "user acceptance testing", "uat", "deployment",
                    "implementation lifecycle", "integration",
                )
            )

            delivery_support = any(
                term in body_text for term in (
                    "customer onboarding", "client onboarding",
                    "stakeholder management", "project management",
                    "implementation project", "user training",
                    "change management", "data integration",
                    "workflow automation", "platform adoption",
                )
            )

            # A named CRM platform in the job title is strong evidence,
            # but unrelated ERP/HRIS roles were excluded above.
            direct_platform_title = any(
                term in title_text for term in (
                    "salesforce", "dynamics 365", "dynamics crm",
                    "hubspot", "zoho crm", "freshsales", "leadsquared",
                    "sugarcrm", "pipedrive",
                )
            )

            if direct_platform_title and implementation_role:
                return bool(lifecycle or delivery_support)

            return bool(
                implementation_role
                and crm_platform
                and lifecycle
                and delivery_support
            )

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
        title_rejection_jobs = 0
        keyword_rejection_jobs = 0

        for job in jobs:

            # ------------------------------------------------------
            # 1. Negative title
            # ------------------------------------------------------
            if self._has_negative_title(job):
                title_rejection_jobs += 1
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
                keyword_rejection_jobs += 1
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

        title_total = title_rejection_jobs
        keyword_total = keyword_rejection_jobs
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