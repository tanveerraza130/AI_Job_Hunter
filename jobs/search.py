"""
Search request models for AI Job Hunter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class SearchRequest:
    """
    Search request for job listings.

    Attributes:
        keyword: Search keyword (e.g., "CRM Manager").
        location: Search location (e.g., "Bangalore").
        page_size: Number of results per page (default: 20).
        max_jobs: Maximum jobs to fetch (default: None = unlimited).
    """
    keyword: str
    location: str
    page_size: int = 20
    max_jobs: Optional[int] = None