"""
Canonical job-location policy.

Only these eight cities are supported by the product job feed.
"""

from __future__ import annotations

import re


ALLOWED_LOCATIONS = (
    "Delhi",
    "Noida",
    "Gurgaon",
    "Bengaluru",
    "Mumbai",
    "Hyderabad",
    "Kolkata",
    "Pune",
)

_LOCATION_ALIASES = {
    "DELHI": "Delhi",
    "DELHI NCR": "Delhi",
    "DELHI / NCR": "Delhi",
    "DELHI/NCR": "Delhi",
    "NEW DELHI": "Delhi",
    "NEWDELHI": "Delhi",
    "NOIDA": "Noida",
    "GURGAON": "Gurgaon",
    "GURUGRAM": "Gurgaon",
    "BENGALURU": "Bengaluru",
    "BANGALORE": "Bengaluru",
    "MUMBAI": "Mumbai",
    "HYDERABAD": "Hyderabad",
    "KOLKATA": "Kolkata",
    "PUNE": "Pune",
}


def normalize_location(value: str | None) -> str | None:
    """Normalize a raw location to an allowed city, if applicable."""
    if not value:
        return None

    text = str(value).strip().upper()

    text = re.sub(r"\bHYBRID\s*-\s*", "", text)
    text = re.sub(r"\s*\([^)]*\)", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    if text in _LOCATION_ALIASES:
        return _LOCATION_ALIASES[text]

    for token in re.split(r"[,/]", text):
        city = re.sub(r"\s+", " ", token).strip()

        if city in _LOCATION_ALIASES:
            return _LOCATION_ALIASES[city]

        if (
            city.startswith("BENGALURU")
            or city.startswith("BANGALORE")
            or "BENGALURU" in city
            or "BANGALORE" in city
        ):
            return "Bengaluru"

    return None


def location_sql(column: str = "l.canonical_name") -> str:
    """Return SQL restricting a location column to allowed cities."""
    return f"""
        (
            LOWER(COALESCE({column}, '')) LIKE '%delhi%'
            OR LOWER(COALESCE({column}, '')) LIKE '%noida%'
            OR LOWER(COALESCE({column}, '')) LIKE '%gurgaon%'
            OR LOWER(COALESCE({column}, '')) LIKE '%gurugram%'
            OR LOWER(COALESCE({column}, '')) LIKE '%bengaluru%'
            OR LOWER(COALESCE({column}, '')) LIKE '%bangalore%'
            OR LOWER(COALESCE({column}, '')) LIKE '%mumbai%'
            OR LOWER(COALESCE({column}, '')) LIKE '%hyderabad%'
            OR LOWER(COALESCE({column}, '')) LIKE '%kolkata%'
            OR LOWER(COALESCE({column}, '')) LIKE '%pune%'
        )
    """
