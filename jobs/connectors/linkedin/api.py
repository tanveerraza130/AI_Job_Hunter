
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
import threading
import time
from typing import Any
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter


class LinkedInAPI:
    """Client for publicly accessible LinkedIn Jobs pages."""

    BASE_URL = "https://www.linkedin.com"

    LOCATION_GEO_IDS = {
        "Delhi": "106187582",
        "Gurugram": "106442238",
        "Noida": "104869687",
        "Bangalore": "105214831",
        "Bengaluru": "105214831",
        "Mumbai": "90009639",
        "Hyderabad": "105556991",
        "Pune": "112419263",
        "Kolkata": "104878698",
    }

    def __init__(
        self,
        *,
        session: requests.Session | None = None,
        timeout: int = 4,   # reduced from 12 — login wall fails fast
        min_delay: float = 0.0,
        max_delay: float = 0.0,
        max_retries: int = 1,
        detail_min_delay: float = 0.10,
    ) -> None:
        self.session = session or requests.Session()

        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=0,
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.timeout = timeout
        self.min_delay = min(max(min_delay, 0.0), 2.0)
        self.max_delay = min(max(max_delay, 0.0), 2.0)
        self.max_retries = min(max_retries, 2)
        self.detail_min_delay = min(max(detail_min_delay, 0.0), 2.0)

        self._last_request_at = 0.0
        self._last_detail_request_at = 0.0
        self._detail_lock = threading.Lock()

        self.session.headers.update({
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
        })

    def _pace(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        delay = random.uniform(self.min_delay, min(self.max_delay, 2.0))
        if elapsed < delay:
            time.sleep(delay - elapsed)

    def _detail_pace(self) -> None:
        elapsed = time.monotonic() - self._last_detail_request_at
        if elapsed < self.detail_min_delay:
            time.sleep(self.detail_min_delay - elapsed)
        with self._detail_lock:
            self._last_detail_request_at = time.monotonic()

    def _get(self, url: str) -> requests.Response | None:
        for attempt in range(self.max_retries + 1):
            self._pace()
            try:
                response = self.session.get(
                    url, timeout=self.timeout, allow_redirects=True
                )
                self._last_request_at = time.monotonic()
            except requests.RequestException:
                self._last_request_at = time.monotonic()
                if attempt >= self.max_retries:
                    return None
                time.sleep(min(2 ** attempt, 2.0))
                continue

            if response.status_code == 429:
                if attempt >= self.max_retries:
                    return response
                retry_after = response.headers.get("Retry-After")
                try:
                    wait = min(float(retry_after), 5.0)
                except (TypeError, ValueError):
                    wait = 2.0
                time.sleep(wait)
                continue

            return response

        return None

    def search_job_cards(self, *, keyword: str, location: str) -> list[dict]:
        geo_id = self.LOCATION_GEO_IDS.get(location.strip())
        params = f"keywords={quote(keyword)}"
        if geo_id:
            params += f"&geoId={quote(geo_id)}"
        else:
            params += f"&location={quote(location)}"
        params += "&f_TPR=r1296000"

        url = f"{self.BASE_URL}/jobs/search/?{params}"
        response = self._get(url)
        if response is None or response.status_code != 200:
            return []

        page = html.unescape(response.text)

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
                card, re.IGNORECASE,
            )
            link = re.search(
                r'href=["\'](https?://[^"\']*/jobs/view/[^"\']+)["\']',
                card, re.IGNORECASE,
            )
            posted = re.search(
                r'<time[^>]+class=["\'][^"\']*'
                r'job-search-card__listdate[^"\']*["\'][^>]+'
                r'datetime=["\'](\d{4}-\d{2}-\d{2})["\']',
                card, re.IGNORECASE | re.DOTALL,
            )
            title_match = re.search(
                r'<h3[^>]+class=["\'][^"\']*'
                r'base-search-card__title[^"\']*["\'][^>]*>'
                r'(.*?)'
                r'</h3>',
                card, re.IGNORECASE | re.DOTALL,
            )
            location_match = re.search(
                r'<span[^>]+class=["\'][^"\']*'
                r'job-search-card__location[^"\']*["\'][^>]*>'
                r'(.*?)'
                r'</span>',
                card, re.IGNORECASE | re.DOTALL,
            )

            title = None
            if title_match:
                title = re.sub(
                    r"\s+", " ",
                    html.unescape(title_match.group(1)),
                ).strip()

            loc = None
            if location_match:
                loc = re.sub(
                    r"\s+", " ",
                    html.unescape(location_match.group(1)),
                ).strip()

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
                "title": title,
                "location": loc,
            })
            seen_ids.add(job_id)

        return cards

    def search_jobs(self, *, keyword: str, location: str) -> list[str]:
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
            page, flags=re.IGNORECASE,
        )

        urls: list[str] = []
        for match in matches:
            clean = html.unescape(match).split("?")[0].rstrip("),.;")
            if "/jobs/view/" not in clean.lower():
                continue
            if clean not in urls:
                urls.append(clean)
        return urls

    def fetch_job_page(self, url: str) -> dict[str, Any] | None:
        self._detail_pace()

        response = None
        for attempt in range(2):
            try:
                response = self.session.get(
                    url, timeout=self.timeout, allow_redirects=True
                )
            except requests.RequestException:
                if attempt == 1:
                    return None
                time.sleep(0.2)
                continue

            if response.status_code != 429:
                break

            retry_after = response.headers.get("Retry-After")
            try:
                wait = min(float(retry_after), 1.5)
            except (TypeError, ValueError):
                wait = 1.5

            if wait >= 1.5:
                return None

            if attempt == 1:
                return None

            time.sleep(wait)

        if response is None or response.status_code != 200:
            return None

        page = html.unescape(response.text)
        blocks = re.findall(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>'
            r'(.*?)'
            r'</script>',
            page, flags=re.IGNORECASE | re.DOTALL,
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
                if candidate.get("@type") == "JobPosting":
                    return candidate

        return None
