"""
Portal enums for AI Job Hunter.
"""

from __future__ import annotations

from enum import StrEnum


class Portal(StrEnum):
    """Supported job portals."""

    UNKNOWN = "unknown"
    NAUKRI = "naukri"
    IIMJOBS = "iimjobs"
    LINKEDIN = "linkedin"
    LINKEDIN_POST = "linkedin_post"
    INDEED = "indeed"
    FOUNDIT = "foundit"
    INSTAHYRE = "instahyre"
    CUTSHORT = "cutshort"
    WELLFOUND = "wellfound"
    GREENHOUSE = "greenhouse"
    WORKDAY = "workday"
    LEVER = "lever"
    ASHBY = "ashby"
    COMPANY = "company"  # Direct company career page


# =============================================================================
# END OF FILE
# =============================================================================