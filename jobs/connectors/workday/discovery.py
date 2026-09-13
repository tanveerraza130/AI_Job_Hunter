from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

import requests


class WorkdayDiscovery:
    """Discover public Workday career boards dynamically."""

    CDX_URL = "https://web.archive.org/cdx/search/cdx"
    ENVIRONMENTS = ("wd1", "wd3", "wd5", "wd12")
    BOARD_PATTERN = re.compile(
        r"^https://(?P<host>[^/]+\.myworkdayjobs\.com)"
        r"/wday/cxs/(?P<tenant>[^/]+)/(?P<site>[^/]+)"
        r"/jobs(?:[/?#].*)?$",
        re.IGNORECASE,
    )

    def __init__(
        self,
        *,
        timeout: int = 20,
        session: requests.Session | None = None,
    ) -> None:
        self.timeout = timeout
        self.session = session or requests.Session()

    def discover(self) -> list[tuple[str, str, str]]:
        candidates: set[tuple[str, str, str]] = set()

        for environment in self.ENVIRONMENTS:
            url_pattern = f"*.{environment}.myworkdayjobs.com/*"

            try:
                response = self.session.get(
                    self.CDX_URL,
                    params={
                        "url": url_pattern,
                        "output": "original",
                        "filter": "statuscode:200",
                        "collapse": "urlkey",
                        "fl": "original",
                        "limit": 5000,
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
            except requests.RequestException:
                continue

            for line in response.text.splitlines():
                original = unquote(line.strip())
                match = self.BOARD_PATTERN.match(original)

                if not match:
                    continue

                candidates.add(
                    (
                        match.group("host").lower(),
                        match.group("tenant"),
                        match.group("site"),
                    )
                )

        return sorted(candidates)

    def validate(
        self,
        boards: list[tuple[str, str, str]],
    ) -> list[tuple[str, str, str]]:
        from .api import WorkdayAPI, WorkdayAPIError

        live: list[tuple[str, str, str]] = []

        for host, tenant, site in boards:
            try:
                api = WorkdayAPI(
                    host=host,
                    tenant=tenant,
                    site=site,
                    session=self.session,
                    timeout=self.timeout,
                )
                payload = api.search_jobs(
                    search_text="",
                    offset=0,
                    limit=20,
                )

                if isinstance(payload.get("jobPostings"), list):
                    live.append((host, tenant, site))

            except (WorkdayAPIError, ValueError):
                continue

        return live

    def discover_live(self) -> list[tuple[str, str, str]]:
        return self.validate(self.discover())

    @staticmethod
    def save(
        boards: list[tuple[str, str, str]],
        path: Path,
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            f"{host}|{tenant}|{site}"
            for host, tenant, site in boards
        ]

        path.write_text(
            "\n".join(lines) + ("\n" if lines else ""),
        )

    @staticmethod
    def load(
        path: Path,
    ) -> list[tuple[str, str, str]]:
        if not path.exists():
            return []

        boards: list[tuple[str, str, str]] = []

        for line in path.read_text().splitlines():
            parts = line.strip().split("|")

            if len(parts) != 3:
                continue

            host, tenant, site = (
                part.strip()
                for part in parts
            )

            if host and tenant and site:
                boards.append((host, tenant, site))

        return boards
