"""
Profile Scoring Engine for AI Job Hunter.

Deterministic, profile-driven scoring engine.

Architecture:

    Profile
        ↓
    Profile-owned scoring/*.yaml
        ↓
    JobIntelligence
        ↓
    Configured scoring components
        ↓
    ScoreResult

Active scoring components are defined exclusively by the active profile.

Current supported components:
    - tool_match
    - skill_match
    - jd_match
    - title_match
    - negative_penalty

Salary, experience, and work mode are NOT scoring components.
They remain available as job/profile metadata for the Web App layer.

No profile-specific scoring defaults exist in this module.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Callable

from jobs.intelligence.models import JobIntelligence, WeightedItem
from jobs.profiles.loader import ConfigLoader
from jobs.scoring.models import ScoreResult, MatchBreakdown
from jobs.version import AI_PIPELINE_VERSION

logger = logging.getLogger(__name__)


class ProfileScoringEngine:
    """
    Generic profile-driven scoring engine.

    The active profile owns:
        - scoring weights
        - skill weights
        - tool scoring policy
        - JD scoring configuration
        - title rules
        - negative signals
        - matching rules
        - bonus configuration

    This class contains only generic scoring mechanics.
    """

    VERSION = AI_PIPELINE_VERSION

    _SUPPORTED_CALCULATORS = frozenset(
        {
            "tool_match",
            "skill_match",
            "jd_match",
            "title_match",
            "negative_penalty",
        }
    )

    def __init__(
        self,
        profile_type: str,
        profile_path: Optional[Path] = None,
    ) -> None:
        if not profile_type or not profile_type.strip():
            raise ValueError(
                "profile_type is required for ProfileScoringEngine."
            )

        self.profile_type = profile_type.strip()

        if profile_path is None:
            profile_path = Path(__file__).parent.parent / "profiles"

        self.profile_path = (
            profile_path / self.profile_type
        )

        if not self.profile_path.exists():
            raise ValueError(
                f"Profile directory does not exist: "
                f"{self.profile_path}"
            )

        self._calculator_registry: Dict[
            str,
            Callable,
        ] = {}

        self._register_calculators()

        self.profile = ConfigLoader.load_profile(
            self.profile_type
        )

        self.category_mappings = (
            ConfigLoader.load_categories(
                self.profile_type
            )
        )

        self.weights = (
            ConfigLoader.load_scoring_weights(
                self.profile_type
            )
        )

        self.matching_rules = (
            ConfigLoader.load_matching_rules(
                self.profile_type
            )
        )

        self.bonus_rules = (
            ConfigLoader.load_bonus_rules(
                self.profile_type
            )
        )

        self.llm_config = (
            ConfigLoader.load_llm_config(
                self.profile_type
            )
        )

        # Profile skill aliases/canonical mapping.
        # This resolves profile-owned terminology.
        self.skill_mapping = self.matching_rules.get(
            "skill_mapping",
            {},
        )

        # Job evidence → profile skill mapping.
        # This is the SINGLE configuration-driven bridge between
        # extracted JD evidence and profile skills.
        self.job_skill_mapping = self.matching_rules.get(
            "job_skill_mapping",
            {},
        )

        if not isinstance(self.skill_mapping, dict):
            raise ValueError(
                f"Profile '{self.profile_type}' has invalid "
                "skill_mapping configuration."
            )

        if not isinstance(self.job_skill_mapping, dict):
            raise ValueError(
                f"Profile '{self.profile_type}' has invalid "
                "job_skill_mapping configuration."
            )

        self._validate_weights()

        self.title_rules = self._load_title_rules()
        self.negative_signals = (
            self._load_negative_signals()
        )

    def _register_calculators(self) -> None:
        """Register generic scoring calculators."""
        self._calculator_registry = {
            "tool_match": self._calculate_tool_match,
            "skill_match": self._calculate_skill_match,
            "jd_match": self._calculate_jd_match,
            "title_match": self._calculate_title_match,
            "negative_penalty": (
                self._calculate_negative_penalty
            ),
        }

    def _validate_weights(self) -> None:
        """Validate the complete profile-owned scoring configuration."""
        weights_data = self.weights.get("weights")

        if not isinstance(weights_data, dict) or not weights_data:
            raise ValueError(
                f"Profile '{self.profile_type}' must define "
                f"scoring weights in "
                f"{self.profile_path / 'scoring' / 'weights.yaml'}"
            )

        unsupported = [
            component
            for component in weights_data
            if component not in self._SUPPORTED_CALCULATORS
        ]

        if unsupported:
            raise ValueError(
                f"Profile '{self.profile_type}' defines unsupported "
                f"scoring components: {unsupported}. "
                f"Supported components: "
                f"{sorted(self._SUPPORTED_CALCULATORS)}"
            )

        positive_weight_sum = sum(
            float(weight)
            for component, weight in weights_data.items()
            if component != "negative_penalty"
        )

        if positive_weight_sum <= 0:
            raise ValueError(
                f"Profile '{self.profile_type}' has no positive "
                f"scoring weight configured."
            )

        if abs(positive_weight_sum - 100.0) > 0.01:
            raise ValueError(
                f"Profile '{self.profile_type}' positive scoring "
                f"weights must total 100.0. "
                f"Current total: {positive_weight_sum}"
            )

        if "negative_penalty" not in weights_data:
            raise ValueError(
                f"Profile '{self.profile_type}' must define "
                f"'negative_penalty' in weights.yaml."
            )

        if (
            "skill_match" in weights_data
            and float(weights_data["skill_match"]) > 0
        ):
            skill_config = self.weights.get(
                "skill_weights"
            )

            if not isinstance(skill_config, dict):
                raise ValueError(
                    f"Profile '{self.profile_type}' requires "
                    f"skill_weights configuration."
                )

            required = {
                "core",
                "default",
                "core_skills",
            }

            missing = required - set(skill_config)

            if missing:
                raise ValueError(
                    f"Profile '{self.profile_type}' is missing "
                    f"skill_weights: {sorted(missing)}"
                )

        if (
            "jd_match" in weights_data
            and float(weights_data["jd_match"]) > 0
        ):
            jd_config = self.weights.get("jd_config")

            if not isinstance(jd_config, dict):
                raise ValueError(
                    f"Profile '{self.profile_type}' requires "
                    f"jd_config configuration."
                )

            required = {
                "score_per_concept",
                "max_score",
            }

            missing = required - set(jd_config)

            if missing:
                raise ValueError(
                    f"Profile '{self.profile_type}' is missing "
                    f"jd_config: {sorted(missing)}"
                )

        if (
            "tool_match" in weights_data
            and float(weights_data["tool_match"]) > 0
        ):
            tool_config = self.weights.get(
                "tool_scoring"
            )

            if not isinstance(tool_config, dict):
                raise ValueError(
                    f"Profile '{self.profile_type}' requires "
                    f"tool_scoring configuration."
                )

            required = {
                "mode",
                "full_match_score",
            }

            missing = required - set(tool_config)

            if missing:
                raise ValueError(
                    f"Profile '{self.profile_type}' is missing "
                    f"tool_scoring: {sorted(missing)}"
                )

            supported_modes = {
                "any_profile_tool",
            }

            if tool_config["mode"] not in supported_modes:
                raise ValueError(
                    f"Profile '{self.profile_type}' defines unsupported "
                    f"tool scoring mode: {tool_config['mode']}"
                )

        bonus_config = self.weights.get(
            "bonus_config"
        )

        if not isinstance(bonus_config, dict):
            raise ValueError(
                f"Profile '{self.profile_type}' requires "
                f"bonus_config.max_bonus in weights.yaml."
            )

        if "max_bonus" not in bonus_config:
            raise ValueError(
                f"Profile '{self.profile_type}' requires "
                f"bonus_config.max_bonus in weights.yaml."
            )

    def _load_title_rules(self) -> dict:
        """Load and validate profile-owned title rules."""
        title_rules = ConfigLoader.load(
            self.profile_type,
            section="scoring",
            file="titles.yaml",
        )

        strong = title_rules.get("strong")
        weak = title_rules.get("weak")
        patterns = title_rules.get("patterns")

        if not isinstance(strong, dict):
            raise ValueError(
                f"Profile '{self.profile_type}' titles.yaml must "
                f"define strong.titles and strong.score."
            )

        if not isinstance(weak, dict):
            raise ValueError(
                f"Profile '{self.profile_type}' titles.yaml must "
                f"define weak.titles and weak.score."
            )

        if not isinstance(
            strong.get("titles"),
            list,
        ):
            raise ValueError(
                f"Profile '{self.profile_type}' strong.titles "
                f"must be a list."
            )

        if "score" not in strong:
            raise ValueError(
                f"Profile '{self.profile_type}' strong.score "
                f"is required."
            )

        if not isinstance(
            weak.get("titles"),
            list,
        ):
            raise ValueError(
                f"Profile '{self.profile_type}' weak.titles "
                f"must be a list."
            )

        if "score" not in weak:
            raise ValueError(
                f"Profile '{self.profile_type}' weak.score "
                f"is required."
            )

        if not isinstance(patterns, list):
            raise ValueError(
                f"Profile '{self.profile_type}' titles.yaml "
                f"patterns must be a list."
            )

        for index, rule in enumerate(patterns):
            if (
                not isinstance(rule, dict)
                or "pattern" not in rule
                or "score" not in rule
            ):
                raise ValueError(
                    f"Profile '{self.profile_type}' title pattern "
                    f"#{index} must define pattern and score."
                )

        self._title_scores = {
            "strong": float(strong["score"]),
            "weak": float(weak["score"]),
        }

        return {
            "strong": list(strong["titles"]),
            "weak": list(weak["titles"]),
            "patterns": patterns,
        }

    def _load_negative_signals(self) -> dict:
        """Load and validate profile-owned negative signals."""
        negative_signals = ConfigLoader.load(
            self.profile_type,
            section="scoring",
            file="negative_signals.yaml",
        )

        required = {
            "signals",
            "penalty_per_signal",
            "max_penalty",
        }

        missing = required - set(
            negative_signals
        )

        if missing:
            raise ValueError(
                f"Profile '{self.profile_type}' negative_signals.yaml "
                f"is missing: {sorted(missing)}"
            )

        return negative_signals

    def _get_weight(
        self,
        category: str,
    ) -> float:
        """Return a required profile-owned component weight."""
        weights = self.weights.get("weights", {})

        if category not in weights:
            raise ValueError(
                f"Profile '{self.profile_type}' is missing required "
                f"weight '{category}'."
            )

        return float(weights[category])

    def _get_mandatory_skills(self) -> List[str]:
        return self.matching_rules.get(
            "mandatory_skills",
            [],
        )

    def _get_preferred_skills(self) -> List[str]:
        return self.matching_rules.get(
            "preferred_skills",
            [],
        )

    def _get_skill_bonuses(self) -> List[dict]:
        return self.bonus_rules.get(
            "skill_bonuses",
            [],
        )

    def _get_tool_bonuses(self) -> List[dict]:
        return self.bonus_rules.get(
            "tool_bonuses",
            [],
        )

    def _get_category_mapping(
        self,
        scoring_category: str,
    ) -> str:
        """Resolve a scoring category through profile configuration."""
        if scoring_category not in self.category_mappings:
            raise ValueError(
                f"Profile '{self.profile_type}' is missing "
                f"category mapping for '{scoring_category}'."
            )

        return self.category_mappings[
            scoring_category
        ]

    def _calculate_skill_match(
        self,
        profile_skills: List[str],
        job_skills: List[WeightedItem],
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calculate binary CRM skill/capability relevance.

        A strong CRM capability found in the JD qualifies the skill
        component at 100%. Otherwise the component is 0%.

        Major CRM capabilities come from the profile-owned
        skill_weights.core_skills configuration. Job evidence is
        resolved through the existing profile job_skill_mapping and
        skill_mapping rules.

        This intentionally does not calculate proportional coverage.
        """

        if not profile_skills:
            return 100.0, [], []

        if not job_skills:
            return 0.0, list(profile_skills), []

        skill_config = self.weights.get("skill_weights", {})
        core_skills = {
            str(skill).strip().lower()
            for skill in skill_config.get("core_skills", [])
            if str(skill).strip()
        }

        if not core_skills:
            return 0.0, [], []

        job_skill_names: set[str] = set()

        for item in job_skills:
            if not item.name:
                continue

            normalized = item.name.strip().lower()

            if normalized:
                job_skill_names.add(normalized)

        # Binary CRM qualification must use explicit extracted evidence.
    #
    # Do NOT use job_skill_mapping here.
    # Taxonomy mappings are useful for normalization elsewhere,
    # but they must not promote generic terms such as:
    #   Retention -> Retention Marketing
    # into high-confidence CRM evidence.
    #
    # A job qualifies for binary Skill Match only when the
    # extracted job evidence itself matches an explicit core skill.
        canonical_core_skills = set(core_skills)


        matched_core = sorted(
            skill
            for skill in canonical_core_skills
            if skill in job_skill_names
        )

        if matched_core:
            # A core capability is not sufficient by itself for a
            # CRM profile. Generic capabilities such as Customer
            # Lifecycle, Customer Lifetime Value, Data Unification,
            # and Onboarding Journeys occur in unrelated roles.
            #
            # Role relevance is established by the profile filter /
            # CRM role gate before scoring. Keep this component
            # binary, but do not allow generic capability evidence
            # to manufacture CRM relevance downstream.
            return 100.0, [], matched_core[:5]

        return 0.0, list(profile_skills), []
    def _calculate_tool_match(
        self,
        profile_tools: List[str],
        job_tools: List[WeightedItem],
    ) -> Tuple[float, List[str], List[str]]:
        """Calculate profile-owned tool match."""
        if not profile_tools:
            return 100.0, [], []

        if not job_tools:
            return 0.0, profile_tools, []

        tool_config = self.weights[
            "tool_scoring"
        ]

        mode = tool_config["mode"]
        full_match_score = float(
            tool_config["full_match_score"]
        )

        profile_tool_names = {
            tool.strip().lower()
            for tool in profile_tools
            if tool and tool.strip()
        }

        job_tool_names = {
            item.name.strip().lower()
            for item in job_tools
            if item.name and item.name.strip()
        }

        if mode == "any_profile_tool":
            found = bool(
                profile_tool_names
                & job_tool_names
            )
        else:
            raise ValueError(
                f"Unsupported tool scoring mode: {mode}"
            )

        missing = (
            []
            if found
            else list(profile_tools)
        )

        strengths = [
            item.name
            for item in job_tools
            if (
                item.name
                and item.name.strip().lower()
                not in profile_tool_names
            )
        ]

        score = (
            full_match_score
            if found
            else 0.0
        )

        return (
            score,
            missing,
            strengths[:5],
        )

    def _calculate_jd_match(
        self,
        job_concepts: List[WeightedItem],
        job_skills: List[WeightedItem],
        job_tools: List[WeightedItem],
    ) -> float:
        """
        Calculate contextual CRM JD relevance.

        Dedicated MarTech platforms remain strong CRM evidence.

        Generic / dual-purpose CRM platforms such as HubSpot must
        be evaluated in the context of the surrounding JD. A role
        dominated by RevOps, GTM/Data Operations, enrichment,
        outbound infrastructure, or engineering signals should not
        receive a full JD relevance score merely because a CRM
        platform is present.
        """

        if not job_tools:
            return 0.0

        tool_names = {
            item.name.strip().lower()
            for item in job_tools
            if item.name and item.name.strip()
        }

        # Dedicated CRM/MarTech platforms are strong direct evidence.
        dedicated_martech_tools = {
            "clevertap",
            "moengage",
            "webengage",
            "netcore cloud",
            "braze",
            "iterable",
            "insider",
            "customer.io",
            "mailmodo",
            "leanplum",
            "onesignal",
            "upshot.ai",
            "salesforce marketing cloud",
            "adobe experience cloud",
            "adobe campaign",
            "marketo",
            "klaviyo",
            "activecampaign",
            "blueshift",
            "omnisend",
            "drip",
            "airship",
        }

        crm_context_signals = {
            "crm strategy",
            "crm analytics",
            "customer lifecycle",
            "lifecycle marketing",
            "retention marketing",
            "customer engagement",
            "customer journey",
            "customer journey mapping",
            "segmentation",
            "personalization",
            "loyalty programs",
            "journey builder",
            "journey design",
            "journey orchestration",
            "triggered campaigns",
            "retention journeys",
            "win back campaigns",
            "churn reduction",
            "campaign management",
            "campaign automation",
            "marketing automation",
            "customer analytics",
            "cohort analysis",
            "rfm analysis",
            "customer lifetime value",
            "ltv analysis",
            "customer data platform",
            "cdp strategy",
            "push notification strategy",
            "sms marketing strategy",
            "whatsapp marketing strategy",
            "omnichannel communication strategy",
        }

        evidence_names = {
            item.name.strip().lower()
            for item in [
                *job_concepts,
                *job_skills,
            ]
            if item.name and item.name.strip()
        }

        crm_context_evidence = (
            evidence_names & crm_context_signals
        )

        if tool_names & dedicated_martech_tools:
            return (
                100.0
                if crm_context_evidence
                else 0.0
            )

        # Generic / dual-purpose CRM platforms need contextual evidence.
        contextual_tools = {
            "hubspot",
            "salesforce",
            "salesforce crm",
            "zoho crm",
            "freshsales",
            "freshworks crm",
            "leadsquared",
        }

        if not (tool_names & contextual_tools):
            return 0.0


        # These signals indicate CRM platform operations rather than
        # CRM/MarTech lifecycle ownership.
        operational_conflicts = {
            "revenue operations",
            "revops",
            "sales operations",
            "sales ops",
            "sales operations management",
            "gtm operations",
            "gtm ops",
            "data operations",
            "data ops",
            "data enrichment",
            "outbound infrastructure",
            "outbound sales",
            "salesforce administration",
            "crm administration",
            "backend engineering",
            "software engineering",
        }

        conflict_count = len(
            evidence_names & operational_conflicts
        )

        # Two or more independent operational signals mean the CRM
        # platform is being used primarily as an operational/data system.
        if conflict_count >= 2:
            return 0.0

        # One operational signal means contextual CRM relevance,
        # but not a full JD match.
        if conflict_count == 1:
            return 40.0

        # Generic CRM platforms are useful evidence only when the JD
        # contains explicit CRM/lifecycle/marketing context.
        if crm_context_evidence:
            return 70.0

        return 0.0


    def _calculate_title_match(
        self,
        job_title: str,
    ) -> float:
        """Calculate profile-owned title match."""
        if not job_title:
            return 0.0

        title_lower = job_title.lower()

        for title in self.title_rules["strong"]:
            if title.lower() in title_lower:
                return self._title_scores["strong"]

        for title in self.title_rules["weak"]:
            if title.lower() in title_lower:
                return self._title_scores["weak"]

        for rule in self.title_rules["patterns"]:
            pattern = str(
                rule["pattern"]
            ).strip()

            if not pattern:
                continue

            if re.search(
                r"\b"
                + re.escape(pattern)
                + r"\b",
                title_lower,
            ):
                return float(rule["score"])

        return 0.0

    def _calculate_negative_penalty(
        self,
        job_title: str,
        job_description: str,
    ) -> float:
        """Calculate profile-owned negative penalty."""
        if not job_title and not job_description:
            return 0.0

        combined_text = (
            f"{job_title or ''} "
            f"{job_description or ''}"
        )

        signals = self.negative_signals[
            "signals"
        ]

        penalty_per_signal = float(
            self.negative_signals[
                "penalty_per_signal"
            ]
        )

        max_penalty = float(
            self.negative_signals[
                "max_penalty"
            ]
        )

        penalty = 0.0

        for pattern in signals:
            if re.search(
                pattern,
                combined_text,
                re.IGNORECASE,
            ):
                penalty += penalty_per_signal

        return min(
            penalty,
            max_penalty,
        )

    def _calculate_technical_negative_penalty(
        self,
        job_title: str,
        job_description: str,
    ) -> float:
        """
        Calculate one technical-role penalty.

        Technical CRM signals represent role classification, not
        independent negative signals. Therefore overlapping patterns
        can never stack.

        Explicit technical titles are excluded directly.

        Ambiguous CRM titles such as:
            - Microsoft Dynamics CRM
            - Functional Consultant Dynamics CRM

        are evaluated using technical evidence in the JD.
        """
        if not job_title and not job_description:
            return 0.0

        title_text = str(job_title or "").strip()
        description_text = str(job_description or "")

        combined_text = (
            f"{title_text} {description_text}"
        )

        signals = self.negative_signals.get(
            "technical_signals",
            [],
        )

        penalty_per_signal = float(
            self.negative_signals.get(
                "penalty_per_signal",
                20.0,
            )
        )

        max_penalty = float(
            self.negative_signals.get(
                "max_penalty",
                100.0,
            )
        )

        # --------------------------------------------------------
        # Explicit technical title signals
        # --------------------------------------------------------

        title_signal_match = False

        for pattern in signals:
            try:
                if re.search(
                    str(pattern),
                    title_text,
                    flags=re.IGNORECASE,
                ):
                    title_signal_match = True
                    break
            except re.error:
                continue

        # --------------------------------------------------------
        # Engineering/data-engineering title families
        #
        # These are intentionally profile-level role signals.
        # They do not affect normal MarTech tools.
        # --------------------------------------------------------

        engineering_title_patterns = [
            r"\bCRM\s+(?:Data\s+)?Engineer(?:ing)?\b",
            r"\b(?:Data|Software|Backend|Solutions?)\s+Engineer\b.*\bCRM\b",
            r"\bCRM\b.*\b(?:Data|Software|Backend|Solutions?)\s+Engineer\b",
            r"\bCRM\b.*\bDeveloper\b",
            r"\bDeveloper\b.*\bCRM\b",
        ]

        engineering_title_match = any(
            re.search(
                pattern,
                title_text,
                flags=re.IGNORECASE,
            )
            for pattern in engineering_title_patterns
        )

        # --------------------------------------------------------
        # Technical JD evidence
        #
        # Used only when the title itself is ambiguous.
        #
        # Evidence is grouped by technical capability so that
        # repeated wording does not artificially inflate the count.
        # --------------------------------------------------------

        technical_evidence_groups = {
            "development": [
                r"\bsoftware\s+development\b",
                r"\bsolution\s+development\b",
                r"\bdevelop(?:ing|ment|ed)?\s+(?:custom\s+)?solutions?\b",
                r"\bcustom(?:ize|ized|ization|isation|ised)\b",
                r"\bdevelopers?\b",
                r"\bdevelopment\b",
            ],
            "programming": [
                r"\bjavascript\b",
                r"\bc#\b",
                r"\b\.net\b",
                r"\bpython\b",
            ],
            "platform_automation": [
                r"\bpower\s*apps?\b",
                r"\bpower\s+automate\b",
                r"\bpower\s+platform\b",
            ],
            "integration": [
                r"\bweb\s+services?\b",
                r"\bapis?\b",
                r"\bintegration(?:s)?\b",
                r"\bthird[-\s]?party\s+systems?\b",
            ],
            "cloud": [
                r"\bazure\b",
                r"\bcloud\s+architecture\b",
            ],
            "technical_implementation": [
                r"\btechnical\s+implementation\b",
                r"\btechnical\s+architecture\b",
                r"\btechnical\s+solution\b",
                r"\bconfiguration\b",
                r"\bcustom(?:ization|isation)\b",
            ],
            "engineering_team": [
                r"\bdevelopment\s+team\b",
                r"\bteam\s+of\s+developers?\b",
                r"\bdevelopers?\s+and\s+engineers?\b",
            ],
        }

        technical_evidence_groups_matched = 0
        matched_technical_groups: set[str] = set()

        for group_name, patterns in technical_evidence_groups.items():
            if any(
                re.search(
                    pattern,
                    description_text,
                    flags=re.IGNORECASE,
                )
                for pattern in patterns
            ):
                matched_technical_groups.add(group_name)

        technical_evidence_groups_matched = len(
            matched_technical_groups
        )

        # --------------------------------------------------------
        # CRM context is required for JD-based technical exclusion.
        # --------------------------------------------------------

        crm_context = bool(
            re.search(
                r"\b(?:crm|dynamics\s+365|dynamics\s+crm|"
                r"salesforce|sap\s+crm)\b",
                combined_text,
                flags=re.IGNORECASE,
            )
        )

        # --------------------------------------------------------
        # Functional Consultant
        #
        # Functional Consultant is NOT automatically technical.
        # It becomes technical when the JD contains strong
        # implementation/development evidence.
        # --------------------------------------------------------

        functional_consultant = bool(
            re.search(
                r"\bfunctional\s+consultant\b",
                title_text,
                flags=re.IGNORECASE,
            )
        )

        functional_technical = (
            functional_consultant
            and crm_context
            and technical_evidence_groups_matched >= 3
        )

        # --------------------------------------------------------
        # Ambiguous CRM platform titles
        #
        # Example:
        #   "Microsoft Dynamics CRM"
        #
        # The title alone is NOT enough.
        # Multiple independent technical capability groups
        # in the JD are required.
        # --------------------------------------------------------

        # Ambiguous CRM titles need meaningful technical evidence,
        # but requiring three unrelated capability groups is too strict.
        #
        # A combination such as:
        #   CRM + development/customization
        #   CRM + Power Platform
        # is sufficient to classify an engineering/implementation role.
        #
        # This prevents technical CRM roles from escaping because their
        # JD is short, while normal CRM/MarTech roles remain unaffected.
        development_group = (
            "development" in matched_technical_groups
        )
        programming_group = (
            "programming" in matched_technical_groups
        )
        platform_group = (
            "platform_automation" in matched_technical_groups
        )
        integration_group = (
            "integration" in matched_technical_groups
        )
        cloud_group = (
            "cloud" in matched_technical_groups
        )

        technical_implementation_group = (
            "technical_implementation"
            in matched_technical_groups
        )

        ambiguous_crm_technical = (
            crm_context
            and (
                (
                    development_group
                    and platform_group
                    and technical_implementation_group
                )
                or (
                    programming_group
                    and integration_group
                    and technical_implementation_group
                )
                or (
                    integration_group
                    and cloud_group
                    and technical_implementation_group
                )
            )
        )

        technical_role = (
            title_signal_match
            or engineering_title_match
            or functional_technical
            or ambiguous_crm_technical
        )

        if technical_role:
            return min(
                penalty_per_signal,
                max_penalty,
            )

        return 0.0

    def _calculate_bonuses(
        self,
        job_skills: List[WeightedItem],
        job_tools: List[WeightedItem],
    ) -> float:
        """
        Calculate configured bonuses.

        Bonuses are retained as metadata and are not currently included
        in the locked positive scoring formula.
        """
        bonus = 0.0

        for rule in self._get_skill_bonuses():
            skill_name = rule.get(
                "skill",
                "",
            )

            bonus_value = float(
                rule.get("bonus", 0.0)
            )

            min_count = int(
                rule.get("min_count", 1)
            )

            for item in job_skills:
                if (
                    item.name == skill_name
                    and item.count >= min_count
                ):
                    bonus += bonus_value
                    break

        for rule in self._get_tool_bonuses():
            tool_name = rule.get(
                "tool",
                "",
            )

            bonus_value = float(
                rule.get("bonus", 0.0)
            )

            min_count = int(
                rule.get("min_count", 1)
            )

            for item in job_tools:
                if (
                    item.name == tool_name
                    and item.count >= min_count
                ):
                    bonus += bonus_value
                    break

        max_bonus = float(
            self.weights[
                "bonus_config"
            ]["max_bonus"]
        )

        return min(
            bonus,
            max_bonus,
        )

    def score_job(
        self,
        intelligence: JobIntelligence,
        job_title: str = "",
        job_description: str = "",
    ) -> ScoreResult:
        """
        Score one job using only profile-configured components.
        """
        profile_skills = self.profile.skills
        profile_tools = self.profile.tools

        skills_category = (
            self._get_category_mapping(
                "skills"
            )
        )

        tools_category = (
            self._get_category_mapping(
                "tools"
            )
        )

        concepts_category = (
            self._get_category_mapping(
                "concepts"
            )
        )

        job_skills = intelligence.get_category(
            skills_category
        )

        job_tools = intelligence.get_category(
            tools_category
        )

        job_concepts = intelligence.get_category(
            concepts_category
        )

        # Skills, concepts, and communication channels can provide
        # evidence for profile skill matching.
        channels_category = self._get_category_mapping(
            "channels"
        )

        job_channels = intelligence.get_category(
            channels_category
        )

        skill_evidence: list[WeightedItem] = []
        seen: set[str] = set()

        for item in [
            *job_skills,
            *job_concepts,
            *job_channels,
        ]:
            normalized = (
                item.name.strip().lower()
            )

            if normalized and normalized not in seen:
                skill_evidence.append(item)
                seen.add(normalized)

        # Contextual protection against false-positive CRM skill matches.
        #
        # "Customer Lifecycle" is a legitimate CRM capability, but it can
        # also appear in operational CRM/data contexts such as:
        #   - Revenue Operations
        #   - Data Enrichment
        #   - Bounce Rate / data quality
        #
        # In those contexts, the phrase alone must not qualify the job as
        # strong CRM lifecycle-marketing evidence.
        operational_context = {
            item.name.strip().lower()
            for item in [
                *job_concepts,
                *job_skills,
            ]
            if item.name and item.name.strip()
        }

        operational_signals = {
            "revenue operations",
            "data enrichment",
            "bounce rate",
        }

        if (
            "customer lifecycle" in operational_context
            and operational_context & operational_signals
        ):
            skill_evidence = [
                item
                for item in skill_evidence
                if item.name.strip().lower()
                != "customer lifecycle"
            ]

        # ----------------------------------------------------------
        # CRM role-context gate
        # ----------------------------------------------------------
        # Generic CRM capabilities frequently occur in unrelated jobs:
        #   Customer Lifecycle
        #   Onboarding Journeys
        #   Journey Design
        #   Data Unification
        #   Customer Lifetime Value
        #
        # These signals must NOT independently qualify a job as CRM.
        # Explicit CRM/lifecycle/MarTech titles are allowed to use
        # the capability evidence normally.
        #
        # This is intentionally CRM-profile logic for the current
        # experiment. No Naukri/database behaviour is changed.
        # ----------------------------------------------------------

        crm_title_score = self._calculate_title_match(
            job_title
        )

        generic_capabilities = {
            "customer lifecycle",
            "onboarding journeys",
            "journey design",
            "data unification",
            "customer lifetime value",
            "ltv analysis",
        }

        if crm_title_score <= 0.0:
            skill_evidence = [
                item
                for item in skill_evidence
                if item.name.strip().lower()
                not in generic_capabilities
            ]

        weights_data = self.weights[
            "weights"
        ]

        positive_score = 0.0

        component_scores: Dict[
            str,
            float,
        ] = {}

        missing_skills: List[str] = []
        missing_tools: List[str] = []
        matched_skills: List[str] = []
        matched_tools: List[str] = []

        for component, weight in weights_data.items():
            if component == "negative_penalty":
                continue

            calculator = self._calculator_registry.get(
                component
            )

            if calculator is None:
                raise ValueError(
                    f"No calculator registered for "
                    f"component '{component}'."
                )

            if component == "tool_match":
                score, missing, _ = calculator(
                    profile_tools,
                    job_tools,
                )
                missing_tools = missing

                profile_tool_names = {
                    tool.strip().lower()
                    for tool in profile_tools
                    if tool and tool.strip()
                }

                matched_tools = [
                    item.name
                    for item in job_tools
                    if (
                        item.name
                        and item.name.strip().lower()
                        in profile_tool_names
                    )
                ][:5]

            elif component == "skill_match":
                score, missing, matched = calculator(
                    profile_skills,
                    skill_evidence,
                )
                missing_skills = missing
                matched_skills = matched

            elif component == "jd_match":
                score = calculator(
                    job_concepts,
                    job_skills,
                    job_tools,
                )

            elif component == "title_match":
                score = calculator(
                    job_title
                )

            else:
                raise ValueError(
                    f"Unsupported positive scoring component: "
                    f"{component}"
                )

            component_scores[
                component
            ] = float(score)

            positive_score += (
                float(score)
                * (
                    float(weight)
                    / 100.0
                )
            )

        # Generic negative signals can be overridden by strong
        # CRM/MarTech evidence.
        #
        # Technical CRM role signals are different: a named CRM
        # platform inside a developer/architect/data-engineering role
        # does not make that role a CRM/MarTech marketing role.
        generic_negative_penalty = (
            self._calculate_negative_penalty(
                job_title,
                job_description,
            )
        )

        technical_negative_penalty = (
            self._calculate_technical_negative_penalty(
                job_title,
                job_description,
            )
        )

        strong_crm_evidence = (
            component_scores.get("skill_match", 0.0) >= 100.0
            or component_scores.get("tool_match", 0.0) >= 100.0
        )

        # Technical role classification takes precedence over
        # generic negative signals.
        #
        # Example:
        #   "Microsoft Dynamics 365 CE / CRM Technical"
        #
        # must produce exactly ONE technical penalty, not:
        #   generic 20 + technical 20 = 40.
        if technical_negative_penalty > 0.0:
            generic_negative_penalty = 0.0

        elif strong_crm_evidence:
            generic_negative_penalty = 0.0

        negative_penalty = min(
            generic_negative_penalty
            + technical_negative_penalty,
            float(
                self.negative_signals[
                    "max_penalty"
                ]
            ),
        )

        penalty_weight = self._get_weight(
            "negative_penalty"
        )

        penalty = (
            negative_penalty
            * (
                penalty_weight
                / 100.0
            )
        )

        # ----------------------------------------------------------
        # Technical CRM role hard exclusion
        # ----------------------------------------------------------
        #
        # Explicit technical CRM roles must not be rescued by strong
        # CRM tools/skills/JD evidence. A weighted negative penalty is
        # insufficient because the negative component itself is only
        # weighted at 20%.
        #
        # This applies only to explicit technical role signals loaded
        # from the profile negative_signals.yaml configuration.
        technical_exclusion = (
            technical_negative_penalty > 0.0
        )

        if technical_exclusion:
            overall_score = 0.0
        else:
            overall_score = max(
                0.0,
                positive_score - penalty,
            )

        overall_score = min(
            overall_score,
            100.0,
        )

        # Metadata only. These values are intentionally
        # not scoring components.
        experience_match = 0.0
        salary_match = 0.0
        work_mode_match = 0.0

        strengths: list[str] = []

        breakdown = MatchBreakdown(
            overall_score=overall_score,
            skill_match=component_scores.get(
                "skill_match",
                0.0,
            ),
            tool_match=component_scores.get(
                "tool_match",
                0.0,
            ),
            experience_match=experience_match,
            salary_match=salary_match,
            work_mode_match=work_mode_match,
            jd_match=component_scores.get(
                "jd_match",
                0.0,
            ),
            title_match=component_scores.get(
                "title_match",
                0.0,
            ),
            negative_penalty=negative_penalty,
            matched_skills=matched_skills,
            matched_tools=matched_tools,
            missing_skills=missing_skills,
            missing_tools=missing_tools,
            strengths=strengths[:5],
        )

        return ScoreResult(
            job_id="",
            title=job_title,
            company="",
            score=overall_score,
            breakdown=breakdown,
            intelligence=intelligence,
        )

    def score_jobs(
        self,
        jobs: List[
            tuple[
                str,
                str,
                str,
                JobIntelligence,
            ]
        ],
        job_descriptions: Optional[
            List[str]
        ] = None,
    ) -> List[ScoreResult]:
        """Score multiple jobs and sort descending by score."""
        if job_descriptions is None:
            job_descriptions = [
                ""
                for _ in jobs
            ]

        results: list[ScoreResult] = []

        for index, (
            job_id,
            title,
            company,
            intelligence,
        ) in enumerate(jobs):
            description = (
                job_descriptions[index]
                if index < len(job_descriptions)
                else ""
            )

            result = self.score_job(
                intelligence,
                job_title=title,
                job_description=description,
            )

            result.job_id = job_id
            result.title = title
            result.company = company

            results.append(result)

        results.sort(
            key=lambda result: result.score,
            reverse=True,
        )

        return results


# =============================================================================
# END OF FILE
# =============================================================================
