"""
File:
    urls.py

Version:
    1.0.0

Phase:
    8

Status:
    FROZEN

Purpose:
    Build Naukri search URLs from SearchRequest.

Responsibilities:
    - Accept SearchRequest
    - Generate Naukri search URL from keyword and location
    - No filter parameters (not yet verified)

Dependencies:
    - jobs.search: SearchRequest
    - jobs.connectors.naukri.constants: BASE_URL
    - urllib.parse: quote

This module does NOT:
    - Perform any filtering logic
    - Validate search parameters
    - Interact with connectors
    - Scrape data

PEP8:     Yes
SOLID:    Yes (Single Responsibility)
DRY:      Yes
KISS:     Yes
"""

from __future__ import annotations

from urllib.parse import quote

from jobs.connectors.naukri.constants import BASE_URL
from jobs.search import SearchRequest


def build_search_url(request: SearchRequest) -> str:
    """
    Build Naukri search URL from keyword and location.

    Only keyword and location are used. Filter fields in SearchRequest
    are intentionally ignored until verified from live Naukri URLs.

    Args:
        request: SearchRequest with keyword and location.

    Returns:
        str: Full Naukri search URL.

    Examples:
        >>> build_search_url(SearchRequest(
        ...     keyword="python developer",
        ...     location="bangalore",
        ... ))
        'https://www.naukri.com/python-developer-jobs-in-bangalore'
    """
    # Build base URL
    keyword_slug = quote(request.keyword.lower().replace(" ", "-"))
    url_path = f"/{keyword_slug}-jobs"

    if request.location:
        location_slug = quote(request.location.lower().replace(" ", "-"))
        url_path += f"-in-{location_slug}"

    return f"{BASE_URL}{url_path}"


# =============================================================================
# END OF FILE
# =============================================================================