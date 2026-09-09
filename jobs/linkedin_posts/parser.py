"""
Parser for publicly accessible LinkedIn member hiring posts.

This module is intentionally isolated from the existing LinkedIn Jobs
connector and production Job pipeline.

It only parses a known public LinkedIn post URL. It does not authenticate,
bypass access controls, use proxies, or solve CAPTCHAs.
"""

from __future__ import annotations

import html
import json
import re
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import requests

from jobs.linkedin_posts.models import LinkedInHiringPost


class LinkedInHiringPostParser:
    """Fetch and normalize a publicly accessible LinkedIn member post."""

    def __init__(
        self,
        *,
        session: requests.Session | None = None,
        timeout: int = 20,
    ) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout

        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/139.0 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

    @staticmethod
    def _is_linkedin_post_url(url: str) -> bool:
        """Return True when URL points to a LinkedIn member post."""
        try:
            parsed = urlparse(url)
        except ValueError:
            return False

        host = parsed.netloc.lower().split(":", 1)[0]

        if host not in {"linkedin.com", "www.linkedin.com"}:
            return False

        return "/posts/" in parsed.path.lower()

    @staticmethod
    def _extract_post_id(candidate: dict[str, Any], url: str) -> str | None:
        """Extract the stable activity identifier from JSON-LD or URL."""
        for value in (
            candidate.get("@id"),
            candidate.get("identifier"),
        ):
            if isinstance(value, str):
                match = re.search(r"activity-(\d+)", value)
                if match:
                    return f"activity:{match.group(1)}"

        match = re.search(r"activity-(\d+)", url)
        if match:
            return f"activity:{match.group(1)}"

        return None

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        """Parse an ISO-8601 publication timestamp."""
        if not isinstance(value, str) or not value.strip():
            return None

        normalized = value.strip()

        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"

        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            return None

    @staticmethod
    def _extract_author(
        candidate: dict[str, Any],
    ) -> tuple[str | None, str | None, str | None]:
        """Extract normalized author fields from JSON-LD."""
        author = candidate.get("author")

        if not isinstance(author, dict):
            return None, None, None

        name = author.get("name")
        profile_url = author.get("url")

        return (
            name if isinstance(name, str) else None,
            profile_url if isinstance(profile_url, str) else None,
            None,
        )

    @staticmethod
    def _extract_json_ld(page: str) -> dict[str, Any] | None:
        """Return the first SocialMediaPosting JSON-LD object."""
        blocks = re.findall(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>'
            r'(.*?)'
            r'</script>',
            page,
            flags=re.IGNORECASE | re.DOTALL,
        )

        for block in blocks:
            try:
                payload = json.loads(block.strip())
            except json.JSONDecodeError:
                continue

            candidates = payload if isinstance(payload, list) else [payload]

            for candidate in candidates:
                if not isinstance(candidate, dict):
                    continue

                if candidate.get("@type") == "SocialMediaPosting":
                    return candidate

        return None

    def parse(
        self,
        url: str,
        *,
        discovery_query: str | None = None,
        discovered_at: datetime | None = None,
    ) -> LinkedInHiringPost | None:
        """
        Fetch and normalize one public LinkedIn member post.

        Returns None when the URL is not a LinkedIn post, the request fails,
        the page is not HTTP 200, or no SocialMediaPosting JSON-LD is present.
        """
        if not self._is_linkedin_post_url(url):
            return None

        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
                allow_redirects=True,
            )
        except requests.RequestException:
            return None

        if response.status_code != 200:
            return None

        page = html.unescape(response.text)
        candidate = self._extract_json_ld(page)

        if candidate is None:
            return None

        post_id = self._extract_post_id(candidate, url)

        if not post_id:
            return None

        author_name, author_url, author_headline = self._extract_author(
            candidate
        )

        text = candidate.get("articleBody")

        if not isinstance(text, str) or not text.strip():
            text = candidate.get("headline") or ""

        if not isinstance(text, str):
            text = ""

        posted_at = self._parse_datetime(candidate.get("datePublished"))

        normalized_text = text.strip()

        role = None
        company = None
        location = None
        contact_email = None
        application_url = None

        role_match = re.search(
            r"(?im)^\s*(?:🚀\s*)?(?:we['’]re|we are)\s+hiring\s*[:\-–—]?\s*(.+?)\s*$",
            normalized_text,
        )
        if role_match:
            role = role_match.group(1).strip()

        company_match = re.search(
            r"(?im)^\s*(.+?)\s+is looking for\s+",
            normalized_text,
        )
        if company_match:
            company = company_match.group(1).strip()

        location_match = re.search(
            r"(?im)^\s*(?:📍\s*)?location\s*:\s*(.+?)\s*$",
            normalized_text,
        )
        if location_match:
            location = location_match.group(1).strip()

        email_match = re.search(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            normalized_text,
        )
        if not email_match:
            email_match = re.search(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
                page,
            )
        if email_match:
            contact_email = email_match.group(0)

        url_matches = re.findall(
            r"https?://[^\s<>]+",
            normalized_text,
        )
        for value in url_matches:
            cleaned = value.rstrip(".,);]}")
            if "linkedin.com" not in cleaned.lower():
                application_url = cleaned
                break

        return LinkedInHiringPost(
            post_id=post_id,
            post_url=url,
            author_name=author_name,
            author_url=author_url,
            author_headline=author_headline,
            text=normalized_text,
            posted_at=posted_at,
            company=company,
            location=location,
            role=role,
            application_url=application_url,
            contact_email=contact_email,
            discovery_query=discovery_query,
            discovered_at=discovered_at,
            raw=candidate,
        )
