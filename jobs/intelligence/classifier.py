"""
Job classification engine.

Classifies jobs into business categories before scoring.

No scoring logic.
No profile-specific weights.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class JobClassification:
    """
    Classification result for a job.
    """

    category: str
    confidence: float
    signals: list[str] = field(default_factory=list)


class JobClassifier:
    """
    Rule-based job classifier.

    Purpose:
        Separate relevant roles from noisy roles.

    Categories:
        CRM_STRATEGIC
        SALES_CRM
        CUSTOMER_SUPPORT
        UNKNOWN
    """

    STRATEGIC_SIGNALS = [
        "lifecycle",
        "retention",
        "marketing automation",
        "customer engagement",
        "segmentation",
        "personalization",
        "journey",
        "clevertap",
        "moengage",
        "webengage",
        "braze",
        "campaign",
        "loyalty",
        "customer analytics",
        "ltv",
    ]

    SALES_SIGNALS = [
        "sales target",
        "lead generation",
        "cold calling",
        "telecalling",
        "loan sales",
        "insurance sales",
        "field sales",
        "business development",
    ]

    SUPPORT_SIGNALS = [
        "customer support",
        "customer care",
        "voice process",
        "call center",
        "helpdesk",
        "technical support",
    ]

    def classify(self, job) -> JobClassification:
        """
        Classify a job.

        Args:
            job: Job object.

        Returns:
            JobClassification
        """

        text = " ".join(
            [
                job.title or "",
                job.description or "",
                " ".join(job.skills or []),
            ]
        ).lower()

        strategic = self._match(
            text,
            self.STRATEGIC_SIGNALS,
        )

        sales = self._match(
            text,
            self.SALES_SIGNALS,
        )

        support = self._match(
            text,
            self.SUPPORT_SIGNALS,
        )

        if strategic:
            return JobClassification(
                category="CRM_STRATEGIC",
                confidence=min(100, len(strategic) * 15),
                signals=strategic,
            )

        if sales:
            return JobClassification(
                category="SALES_CRM",
                confidence=min(100, len(sales) * 15),
                signals=sales,
            )

        if support:
            return JobClassification(
                category="CUSTOMER_SUPPORT",
                confidence=min(100, len(support) * 15),
                signals=support,
            )

        return JobClassification(
            category="UNKNOWN",
            confidence=0,
            signals=[],
        )

    def _match(
        self,
        text: str,
        signals: list[str],
    ) -> list[str]:
        """
        Return matched signals.
        """

        return [
            signal
            for signal in signals
            if signal in text
        ]