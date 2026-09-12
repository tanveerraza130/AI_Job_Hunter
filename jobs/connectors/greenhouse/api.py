"""
Greenhouse public Job Board API client.

This client uses Greenhouse's publicly accessible Job Board API.
It does not authenticate, bypass access controls, or use browser
automation.
"""

from __future__ import annotations

from typing import Any

import requests


class GreenhouseAPIError(RuntimeError):
    """Raised when the Greenhouse public API cannot be accessed."""


class GreenhouseAPI:
    """Client for one public Greenhouse job board."""

    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

    def __init__(
        self,
        board_token: str,
        *,
        session: requests.Session | None = None,
        timeout: int = 20,
    ) -> None:
        board_token = board_token.strip()

        if not board_token:
            raise ValueError("board_token cannot be empty")

        self.board_token = board_token
        self.session = session or requests.Session()
        self.timeout = timeout

    @property
    def jobs_url(self) -> str:
        """Return the public jobs endpoint for this board."""
        return (
            f"{self.BASE_URL}/"
            f"{self.board_token}/jobs"
        )

    def fetch_jobs(
        self,
        *,
        content: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Fetch published jobs from the Greenhouse board.

        Greenhouse exposes the board inventory through a public GET
        endpoint. Full job content is requested by default because
        downstream keyword matching may use the job description.
        """
        try:
            response = self.session.get(
                self.jobs_url,
                params={"content": "true" if content else "false"},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise GreenhouseAPIError(
                f"Unable to fetch Greenhouse board "
                f"'{self.board_token}'."
            ) from exc

        if response.status_code != 200:
            raise GreenhouseAPIError(
                "Greenhouse returned HTTP "
                f"{response.status_code} for board "
                f"'{self.board_token}'."
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise GreenhouseAPIError(
                f"Greenhouse returned invalid JSON for "
                f"board '{self.board_token}'."
            ) from exc

        jobs = payload.get("jobs", [])

        if not isinstance(jobs, list):
            raise GreenhouseAPIError(
                "Greenhouse response contained an invalid "
                "'jobs' collection."
            )

        return [
            job
            for job in jobs
            if isinstance(job, dict)
        ]
