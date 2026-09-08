"""
Processor for normalized LinkedIn member hiring posts.

This module is intentionally isolated from the existing Job model,
production job pipeline, and ProfileJobFilter.

It applies deterministic freshness, hiring-intent, negative-noise,
CRM-relevance, and location-evidence rules to a normalized
LinkedInHiringPost.
"""

from __future__ import annotations

import re
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from jobs.linkedin_posts.models import LinkedInHiringPost


class LinkedInHiringPostProcessor:
    """Qualify normalized LinkedIn posts as potential hiring leads."""

    _HIRING_SIGNALS = (
        "hiring",
        "we're hiring",
        "we are hiring",
        "looking for",
        "seeking",
        "open role",
        "job opening",
        "vacancy",
        "join our team",
    )

    _STRONG_ROLE_SIGNALS = (
        "crm",
        "head of crm",
        "vp crm",
        "crm executive",
        "crm analyst",
        "crm analytics manager",
        "crm specialist",
        "crm manager",
        "crm lead",
        "crm team lead",
        "crm head",
        "crm & retention head",
        "lifecycle marketing",
        "lifecycle marketing manager",
        "retention marketing",
        "retention marketing manager",
        "customer lifecycle",
        "customer engagement",
        "customer engagement manager",
        "customer engagement lead",
        "marketing automation",
        "marketing automation manager",
        "marketing automation specialist",
        "marketing automation lead",
        "campaign management",
        "campaign manager",
        "crm campaign manager",
        "campaign manager crm",
        "campaign automation",
        "customer journey",
        "journey orchestration",
        "personalization",
        "loyalty marketing",
        "crm & loyalty",
        "database marketing",
        "growth crm",
        "growth crm manager",
        "martech",
        "mar tech",
    )

    _TECHNICAL_ROLE_SIGNALS = (
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
    )

    _CRM_TOOLS = (
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
    )

    _CAPABILITY_GROUPS = {
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

    _TARGET_LOCATIONS = (
        "delhi",
        "delhi ncr",
        "gurgaon",
        "gurugram",
        "noida",
    )

    _NEGATIVE_TITLES = (
        "key accounts manager",
        "sales executive",
        "sales manager",
        "sales crm",
        "business development executive",
        "business development manager",
        "bdm",
        "inside sales",
        "field sales",
        "telesales",
        "bpo",
        "call center",
        "telecaller",
        "customer support",
        "customer care",
        "technical support",
        "it support",
        "helpdesk",
        "salesforce developer",
        "salesforce administrator",
        "salesforce consultant",
        "crm developer",
        "crm business analyst",
        "crm implementation consultant",
        "crm trainer",
        "marketing automation developer",
        "martech engineer",
        "martech architect",
        "zoho developer",
        "hubspot developer",
        "dynamics crm developer",
        "dynamics 365 crm functional consultant",
        "sap crm consultant",
        "performance marketing manager",
        "media planner",
        "digital marketing executive",
        "growth hacker",
    )

    _NEGATIVE_KEYWORDS = (
        "pre-sales",
        "presales",
        "cold calling",
        "lead generation",
        "lead gen",
        "outbound calling",
        "outbound sales",
        "telemarketing",
        "telesales",
        "cold call",
        "voice process",
        "calling executive",
        "customer support",
        "call center agent",
        "bpo",
        "business development",
        "client acquisition",
        "new client acquisition",
        "hunting",
        "field sales",
        "inside sales",
        "door to door",
        "direct sales",
        "retail sales",
    )

    def __init__(
        self,
        *,
        max_age_hours: int = 48,
        now: datetime | None = None,
    ) -> None:
        if max_age_hours <= 0:
            raise ValueError("max_age_hours must be greater than zero.")

        self.max_age = timedelta(hours=max_age_hours)
        self.now = self._normalize_now(now)

    @staticmethod
    def _normalize_now(value: datetime | None) -> datetime:
        """Return an aware UTC timestamp for deterministic processing."""
        current = value or datetime.now(UTC)

        if current.tzinfo is None:
            return current.replace(tzinfo=UTC)

        return current.astimezone(UTC)

    @staticmethod
    def _contains_signal(text: str, signals: tuple[str, ...]) -> bool:
        """Return True when text contains any configured signal."""
        normalized = text.casefold()

        return any(
            re.search(
                r"\b" + re.escape(signal) + r"\b",
                normalized,
            )
            for signal in signals
        )

    def _is_recent(self, post: LinkedInHiringPost) -> bool:
        """Return True when the post falls within the freshness window."""
        if post.posted_at is None:
            return False

        posted_at = post.posted_at

        if posted_at.tzinfo is None:
            posted_at = posted_at.replace(tzinfo=UTC)
        else:
            posted_at = posted_at.astimezone(UTC)

        age = self.now - posted_at

        return timedelta(0) <= age <= self.max_age

    def _has_hiring_intent(self, post: LinkedInHiringPost) -> bool:
        """Return True when the post contains clear hiring language."""
        return self._contains_signal(post.text, self._HIRING_SIGNALS)

    def _has_negative_title(self, post: LinkedInHiringPost) -> bool:
        """Return True when an explicit role/title is known to be noise."""
        role = (post.role or "").strip()

        if not role:
            return self._contains_signal(
                post.text,
                self._NEGATIVE_TITLES,
            )

        return self._contains_signal(role, self._NEGATIVE_TITLES)

    def _has_negative_keyword(self, post: LinkedInHiringPost) -> bool:
        """Return True when post text contains configured noise."""
        return self._contains_signal(
            post.text,
            self._NEGATIVE_KEYWORDS,
        )

    def _role_evidence(self, post: LinkedInHiringPost) -> str:
        """
        Return the advertised-role evidence used for CRM qualification.

        An explicit normalized role is authoritative. When role extraction
        has not happened yet, only inspect text immediately following a clear
        hiring phrase rather than treating arbitrary mentions elsewhere in
        the post as the advertised role.
        """
        explicit_role = (post.role or "").strip()
        if explicit_role:
            return explicit_role.casefold()

        text = post.text or ""

        role_patterns = (
            r"\b(?:we['’]?re|we are)\s+hiring\s+(?:an?\s+)?"
            r"([^.!?\n]{1,100})",
            r"\bhiring\s+(?:an?\s+)?"
            r"([^.!?\n]{1,100})",
            r"\b(?:looking for|seeking)\s+(?:an?\s+)?"
            r"([^.!?\n]{1,100})",
            r"\bopen role\s*[:\-]?\s*(?:an?\s+)?"
            r"([^.!?\n]{1,100})",
            r"\bjob opening\s*[:\-]?\s*(?:an?\s+)?"
            r"([^.!?\n]{1,100})",
            r"\bvacancy\s*[:\-]?\s*(?:an?\s+)?"
            r"([^.!?\n]{1,100})",
        )

        for pattern in role_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip().casefold()

        return ""

    def _crm_relevance(self, post: LinkedInHiringPost) -> bool:
        """Return True when the post contains substantive CRM evidence."""
        role = self._role_evidence(post)
        combined = f"{role} {post.text}".casefold()

        if self._contains_signal(
            role,
            self._STRONG_ROLE_SIGNALS,
        ):
            return True

        if self._contains_signal(
            role,
            self._TECHNICAL_ROLE_SIGNALS,
        ):
            return False

        tool_hits = [
            tool
            for tool in self._CRM_TOOLS
            if re.search(
                r"\b" + re.escape(tool) + r"\b",
                combined,
                re.IGNORECASE,
            )
        ]

        matched_groups: set[str] = set()

        for group, signals in self._CAPABILITY_GROUPS.items():
            if self._contains_signal(combined, signals):
                matched_groups.add(group)

        core_groups = matched_groups - {"crm_channels"}

        if tool_hits and core_groups:
            return True

        return len(core_groups) >= 2

    def _location_evidence(self, post: LinkedInHiringPost) -> bool:
        """Return True when post metadata/text contains a target location."""
        location = (post.location or "").strip()

        if location and self._contains_signal(
            location,
            self._TARGET_LOCATIONS,
        ):
            return True

        return self._contains_signal(
            post.text,
            self._TARGET_LOCATIONS,
        )

    def _score(self, post: LinkedInHiringPost) -> float:
        """Calculate a deterministic relevance score in the 0..1 range."""
        role = self._role_evidence(post)
        combined = f"{role} {post.text}".casefold()

        score = 0.0

        if self._contains_signal(
            role,
            self._STRONG_ROLE_SIGNALS,
        ):
            score += 0.60
        else:
            score += 0.40

        if self._contains_signal(
            combined,
            self._CRM_TOOLS,
        ):
            score += 0.15

        if self._location_evidence(post):
            score += 0.15

        if self._contains_signal(
            combined,
            self._CAPABILITY_GROUPS["lifecycle_retention"],
        ):
            score += 0.05

        if self._contains_signal(
            combined,
            self._CAPABILITY_GROUPS["campaign_automation"],
        ):
            score += 0.05

        return min(round(score, 4), 1.0)

    def process(
        self,
        post: LinkedInHiringPost,
    ) -> LinkedInHiringPost | None:
        """
        Qualify one normalized LinkedIn hiring post.

        Returns the same post object with a deterministic relevance score,
        or None when the post fails a qualification gate.
        """
        if not self._is_recent(post):
            return None

        if not self._has_hiring_intent(post):
            return None

        if self._has_negative_title(post):
            return None

        if self._has_negative_keyword(post):
            return None

        if not self._crm_relevance(post):
            return None

        return replace(
            post,
            relevance_score=self._score(post),
        )
