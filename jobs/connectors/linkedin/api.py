"""
LinkedIn public Jobs HTTP client.

This module only accesses publicly served LinkedIn Jobs pages.
It does not authenticate, bypass access controls, or use proxies.
"""

from __future__ import annotations

import html
import json
import random
import re
import time
from typing import Any
from urllib.parse import quote, urljoin

import requests


class LinkedInAPI:
    """Client for publicly accessible LinkedIn Jobs pages."""

    BASE_URL = "https://www.linkedin.com"

    def __init__(
        self,
        *,
        session: requests.Session | None = None,
        timeout: int = 20,
        min_delay: float = 0.0,
        max_delay: float = 0.0,
        max_retries: int = 2,
    ) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self._last_request_at = 0.0

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

    def _pace(self) -> None:
        elapsed = time.monotonic() - self._last_request_at

        delay = random.uniform(
            self.min_delay,
            self.max_delay,
        )

        if elapsed < delay:
            time.sleep(delay - elapsed)

    def _get(self, url: str) -> requests.Response | None:
        for attempt in range(self.max_retries + 1):
            self._pace()

            try:
                response = self.session.get(
                    url,
                    timeout=self.timeout,
                    allow_redirects=True,
                )
                self._last_request_at = time.monotonic()

            except requests.RequestException:
                self._last_request_at = time.monotonic()

                if attempt >= self.max_retries:
                    return None

                time.sleep(2 ** attempt)
                continue

            if response.status_code == 429:
                # Respect the server rate limit.
                if attempt >= self.max_retries:
                    return response

                retry_after = response.headers.get("Retry-After")

                try:
                    wait_seconds = min(float(retry_after), 30.0)
                except (TypeError, ValueError):
                    wait_seconds = min(5.0 * (attempt + 1), 30.0)

                time.sleep(wait_seconds)
                continue

            return response

        return None

    def search_job_cards(
        self,
        *,
        keyword: str,
        location: str,
    ) -> list[dict]:
        """Discover LinkedIn search cards with posting dates."""

        params = (
            f"keywords={quote(keyword)}"
            f"&location={quote(location)}"
        )

        url = f"{self.BASE_URL}/jobs/search/?{params}"

        response = self._get(url)

        if response is None or response.status_code != 200:
            return []

        page = html.unescape(response.text)

        # Each LinkedIn result is contained in one job-search-card.
        # The card contains its job ID, URL and posting date.
        pattern = re.compile(
            r'<div[^>]+class=["\'][^"\']*job-search-card[^"\']*["\'][^>]*>'
            r'(.*?)'
            r'(?=<div[^>]+class=["\'][^"\']*job-search-card[^"\']*["\']|'
            r'</li>)',
            re.IGNORECASE | re.DOTALL,
        )

        cards = []
        seen_ids = set()

        for match in pattern.finditer(page):
            card = match.group(0)

            urn = re.search(
                r'data-entity-urn=["\']urn:li:jobPosting:(\d+)["\']',
                card,
                re.IGNORECASE,
            )

            link = re.search(
                r'href=["\'](https?://[^"\']*/jobs/view/[^"\']+)["\']',
                card,
                re.IGNORECASE,
            )

            posted = re.search(
                r'<time[^>]+class=["\'][^"\']*'
                r'job-search-card__listdate[^"\']*["\'][^>]+'
                r'datetime=["\'](\d{4}-\d{2}-\d{2})["\']',
                card,
                re.IGNORECASE | re.DOTALL,
            )

            if not urn or not link:
                continue

            job_id = urn.group(1)

            if job_id in seen_ids:
                continue

            job_url = html.unescape(link.group(1))
            job_url = job_url.split("?")[0].rstrip("),.;")

            cards.append({
                "job_id": job_id,
                "job_url": job_url,
                "posted_date": posted.group(1) if posted else None,
            })

            seen_ids.add(job_id)

        return cards
    def search_jobs(
        self,
        *,
        keyword: str,
        location: str,
    ) -> list[str]:
        """Return public LinkedIn job URLs discovered on the search page."""

        params = (
            f"keywords={quote(keyword)}"
            f"&location={quote(location)}"
        )

        url = f"{self.BASE_URL}/jobs/search/?{params}"

        response = self._get(url)

        if response is None or response.status_code != 200:
            return []

        page = html.unescape(response.text)

        matches = re.findall(
            r'https?://[^"\'<>\s]*linkedin\.com/jobs/view/[^"\'<>\s]*',
            page,
            flags=re.IGNORECASE,
        )

        urls: list[str] = []

        for match in matches:
            clean = html.unescape(match)
            clean = clean.split("?")[0].rstrip("),.;")

            if "/jobs/view/" not in clean.lower():
                continue

            if clean not in urls:
                urls.append(clean)

        return urls

    def fetch_job_page(self, url: str) -> dict[str, Any] | None:
        """Fetch and parse a public LinkedIn JobPosting JSON-LD block."""

        response = self._get(url)

        if response is None or response.status_code != 200:
            return None

        page = html.unescape(response.text)

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

            candidates = (
                payload if isinstance(payload, list) else [payload]
            )

            for candidate in candidates:
                if not isinstance(candidate, dict):
                    continue

                job_type = candidate.get("@type")

                if job_type == "JobPosting":
                    return candidate

        return None
