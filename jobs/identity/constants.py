"""
File:
    constants.py

Version:
    1.0.0

Phase:
    3

Status:
    FROZEN

Purpose:
    Constants for identity normalization module.

Responsibilities:
    - Company suffixes to remove
    - Location mapping
    - Work mode mapping
    - Employment type mapping

PEP8:     Yes
SOLID:    Yes
DRY:      Yes
KISS:     Yes
"""

from __future__ import annotations

# ------------------------------------------------------------------
# Company Suffixes
# ------------------------------------------------------------------

COMPANY_SUFFIXES: list[str] = [
    "pvt",
    "private",
    "ltd",
    "limited",
    "llp",
    "llc",
    "corp",
    "corporation",
    "inc",
    "incorporated",
    "co.",
    "company",
    "technologies",
    "technology",
    "solutions",
    "solution",
    "services",
    "service",
]

# ------------------------------------------------------------------
# Location Mapping
# ------------------------------------------------------------------

LOCATION_MAP: dict[str, str] = {
    "bangalore": "bangalore",
    "bengaluru": "bangalore",
    "bengalooru": "bangalore",
    "new delhi": "delhi",
    "delhi": "delhi",
    "gurugram": "gurgaon",
    "gurgaon": "gurgaon",
    "mumbai": "mumbai",
    "bombay": "mumbai",
    "pune": "pune",
    "poonaw": "pune",
    "hyderabad": "hyderabad",
    "secunderabad": "hyderabad",
    "chennai": "chennai",
    "madras": "chennai",
    "noida": "noida",
    "remote": "remote",
    "work from home": "remote",
    "wfh": "remote",
}

# ------------------------------------------------------------------
# Work Mode Mapping
# ------------------------------------------------------------------

WORK_MODE_MAP: dict[str, str] = {
    "remote": "remote",
    "work from home": "remote",
    "wfh": "remote",
    "hybrid": "hybrid",
    "onsite": "onsite",
    "on-site": "onsite",
    "office": "onsite",
}

# ------------------------------------------------------------------
# Employment Type Mapping
# ------------------------------------------------------------------

EMPLOYMENT_TYPE_MAP: dict[str, str] = {
    "full time": "full_time",
    "fulltime": "full_time",
    "permanent": "full_time",
    "contract": "contract",
    "contractual": "contract",
    "internship": "internship",
    "intern": "internship",
    "part time": "part_time",
    "parttime": "part_time",
    "freelance": "freelance",
}


# =============================================================================
# END OF FILE
# =============================================================================