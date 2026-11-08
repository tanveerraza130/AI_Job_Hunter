from __future__ import annotations

from datetime import date


from jobs.connectors.linkedin.connector import LinkedInConnector
from jobs.search import SearchRequest


def test_linkedin_deduplicates_candidate_across_search_requests(
    monkeypatch,
):
    """The same LinkedIn job must have its detail page fetched only once."""

    connector = LinkedInConnector()

    detail_calls: list[str] = []

    class FakeAPI:
        def search_job_cards(
            self,
            *,
            keyword: str,
            location: str,
        ):
            return [
                {
                    "job_id": "123",
                    "job_url": (
                        "https://www.linkedin.com/jobs/view/123"
                    ),
                    "posted_date": date.today().isoformat(),
                }
            ]

        def fetch_job_page(self, url: str):
            detail_calls.append(url)

            return {
                "title": "CRM Manager",
                "description": "CRM role",
                "company": {
                    "name": "Test Company",
                },
                "jobLocation": {
                    "address": {
                        "addressLocality": "Delhi",
                    }
                },
            }

    fake_api = FakeAPI()

    monkeypatch.setattr(
        connector,
        "_api",
        fake_api,
    )

    request_1 = SearchRequest(
        keyword="CRM Manager",
        location="Delhi",
        max_jobs=10,
    )

    request_2 = SearchRequest(
        keyword="CRM Lead",
        location="Delhi",
        max_jobs=10,
    )

    connector.fetch_jobs(request_1)
    connector.fetch_jobs(request_2)

    assert detail_calls == [
        "https://www.linkedin.com/jobs/view/123"
    ]


def test_linkedin_detail_request_retries_transient_request_exception(
    monkeypatch,
):
    """Transient detail HTTP failures are retried and can recover."""

    from requests import ReadTimeout

    from jobs.connectors.linkedin.api import LinkedInAPI

    api = LinkedInAPI(
        max_retries=2,
        detail_min_delay=0,
    )

    calls = {"count": 0}

    class FakeResponse:
        status_code = 200
        text = """
        <script type="application/ld+json">
        {
            "@type": "JobPosting",
            "title": "CRM Manager"
        }
        </script>
        """

        headers = {}

    def fake_get(*args, **kwargs):
        calls["count"] += 1

        if calls["count"] == 1:
            raise ReadTimeout("simulated timeout")

        return FakeResponse()

    monkeypatch.setattr(
        api.session,
        "get",
        fake_get,
    )

    payload = api.fetch_job_page(
        "https://www.linkedin.com/jobs/view/123"
    )

    assert payload is not None
    assert payload["title"] == "CRM Manager"
    assert calls["count"] == 2


def test_linkedin_detail_request_returns_none_after_retries(
    monkeypatch,
):
    """Persistent detail HTTP failures do not crash the connector."""

    from requests import ConnectionError

    from jobs.connectors.linkedin.api import LinkedInAPI

    api = LinkedInAPI(
        max_retries=2,
        detail_min_delay=0,
    )

    calls = {"count": 0}

    def fake_get(*args, **kwargs):
        calls["count"] += 1
        raise ConnectionError("simulated connection failure")

    monkeypatch.setattr(
        api.session,
        "get",
        fake_get,
    )

    payload = api.fetch_job_page(
        "https://www.linkedin.com/jobs/view/123"
    )

    assert payload is None
    assert calls["count"] == 3
