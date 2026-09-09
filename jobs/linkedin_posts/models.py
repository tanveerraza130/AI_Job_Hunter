"""
Data models for LinkedIn member hiring posts.

This module is intentionally isolated from the existing Job model and
job-search pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class LinkedInHiringPost:
    """
    Normalized LinkedIn member post discovered as a potential hiring lead.

    The post_id is the stable LinkedIn post/activity identifier and is the
    primary identity used for persistent deduplication.
    """

    post_id: str
    post_url: str
    portal: str = "linkedin_post"

    author_name: str | None = None
    author_url: str | None = None
    author_headline: str | None = None

    text: str = ""
    posted_at: datetime | None = None

    company: str | None = None
    company_url: str | None = None
    location: str | None = None
    role: str | None = None

    application_url: str | None = None
    contact_email: str | None = None

    discovery_query: str | None = None
    discovered_at: datetime | None = None

    relevance_score: float = 0.0

    raw: dict[str, Any] = field(default_factory=dict)
