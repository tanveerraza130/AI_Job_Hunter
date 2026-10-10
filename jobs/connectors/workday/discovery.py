from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import unquote

import requests


class WorkdayDiscovery:
    """Discover public Workday career boards dynamically."""

    CDX_URL = "https://web.archive.org/cdx/search/cdx"
    REGISTRY_URL = (
        "https://raw.githubusercontent.com/"
        "Feashliaa/job-board-aggregator/main/data/workday_companies.json"
    )
    ENVIRONMENTS = ("wd1", "wd3", "wd5", "wd12")
    MAX_WORKERS = 10

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

    def discover_registry(
        self,
    ) -> list[tuple[str, str, str]]:
        """Load Workday boards from the public registry."""

        try:
            response = self.session.get(
                self.REGISTRY_URL,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except (
            requests.RequestException,
            ValueError,
        ):
            return []

        candidates: set[tuple[str, str, str]] = set()

        if not isinstance(data, list):
            return []

        for item in data:
            parts = str(item).strip().split("|")

            if len(parts) != 3:
                continue

            tenant, instance, site = (
                part.strip()
                for part in parts
            )

            if not all((tenant, instance, site)):
                continue

            host = f"{tenant}.{instance}.myworkdayjobs.com"

            candidates.add(
                (
                    host.lower(),
                    tenant,
                    site,
                )
            )

        return sorted(candidates)

    def discover_cdx(
        self,
    ) -> list[tuple[str, str, str]]:
        """Discover Workday boards through Internet Archive CDX."""

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

    def discover(self) -> list[tuple[str, str, str]]:
        """Discover boards from the registry, with CDX fallback."""

        registry_boards = self.discover_registry()

        if registry_boards:
            return registry_boards

        return self.discover_cdx()

    def _validate_board(
        self,
        board: tuple[str, str, str],
    ) -> tuple[str, str, str] | None:
        """Validate one Workday board."""

        from .api import WorkdayAPI, WorkdayAPIError

        host, tenant, site = board

        try:
            api = WorkdayAPI(
                host=host,
                tenant=tenant,
                site=site,
                timeout=self.timeout,
            )

            payload = api.search_jobs(
                search_text="",
                offset=0,
                limit=1,
            )

            if not isinstance(
                payload.get("jobPostings"),
                list,
            ):
                return None

            return board

        except (WorkdayAPIError, ValueError):
            return None

    def validate(
        self,
        boards: list[tuple[str, str, str]],
    ) -> list[tuple[str, str, str]]:
        """Validate Workday boards with bounded concurrency."""

        if not boards:
            return []

        live: list[tuple[str, str, str]] = []

        workers = min(
            self.MAX_WORKERS,
            len(boards),
        )

        with ThreadPoolExecutor(
            max_workers=workers,
        ) as executor:
            futures = {
                executor.submit(
                    self._validate_board,
                    board,
                ): board
                for board in boards
            }

            for future in as_completed(futures):
                board = future.result()

                if board is not None:
                    live.append(board)

        return sorted(set(live))

    def discover_live(
        self,
    ) -> list[tuple[str, str, str]]:
        """Discover and validate live Workday boards."""

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
