from __future__ import annotations

from unittest.mock import patch

from jobs.connectors.workday.connector import WorkdayConnector
from jobs.job import Job
from jobs.search import SearchRequest


def _job(job_id: str, location: str) -> Job:
    return Job(
        job_id=job_id,
        title=f"Job {job_id}",
        company="Test Company",
        location=location,
        description="Test description",
        job_url=f"https://example.com/{job_id}",
        portal="workday",
    )


def test_workday_deduplicates_external_path_across_keyword_requests(monkeypatch):
    connector = WorkdayConnector()

    detail_calls = []

    class FakeAPI:
        def search_jobs(self, search_text, offset, limit):
            return {
                "total": 1,
                "jobPostings": [
                    {
                        "externalPath": "/job/123",
                        "locationsText": "India",
                    }
                ],
            }

        def fetch_job_detail(self, external_path):
            detail_calls.append(external_path)
            return {
                "jobPostingInfo": {
                    "title": "CRM Manager",
                    "jobDescription": "CRM role",
                    "location": "India",
                    "jobReqId": "REQ-123",
                }
            }

    monkeypatch.setattr(
        "jobs.connectors.workday.connector.WorkdayAPI",
        lambda **kwargs: FakeAPI(),
    )
    monkeypatch.setattr(
        "jobs.connectors.workday.connector.WorkdayDiscovery.discover_live",
        lambda self: [("example.com", "tenant", "site")],
    )

    request_1 = SearchRequest(keyword="CRM Manager", location="India", max_jobs=10)
    request_2 = SearchRequest(keyword="Lifecycle Marketing", location="India", max_jobs=10)

    connector.fetch_jobs(request_1)
    connector.fetch_jobs(request_2)

    assert detail_calls == ["/job/123"]


def test_workday_max_jobs_applies_after_location_filter():
    connector = WorkdayConnector()

    raw_items = [
        {"externalPath": "/job-1"},
        {"externalPath": "/job-2"},
        {"externalPath": "/job-3"},
        {"externalPath": "/job-4"},
    ]

    mapped_jobs = {
        "/job-1": _job("1", "United States"),
        "/job-2": _job("2", "India-Gurugram"),
        "/job-3": _job("3", "United States"),
        "/job-4": _job("4", "India-Bangalore"),
    }

    request = SearchRequest(
        keyword="CRM",
        location="India",
        page_size=20,
        max_jobs=2,
    )

    with (
        patch(
            "jobs.connectors.workday.connector.WorkdayDiscovery.load",
            return_value=[
                (
                    "example.wd5.myworkdayjobs.com",
                    "example",
                    "Careers",
                )
            ],
        ),
        patch(
            "jobs.connectors.workday.connector.WorkdayDiscovery.discover_live",
            return_value=[],
        ),
        patch(
            "jobs.connectors.workday.connector.WorkdayAPI.search_jobs",
            return_value={
                "total": len(raw_items),
                "jobPostings": raw_items,
            },
        ),
        patch(
            "jobs.connectors.workday.connector.WorkdayAPI.fetch_job_detail",
            side_effect=lambda path: {"externalPath": path},
        ),
        patch(
            "jobs.connectors.workday.connector.map_job",
            side_effect=lambda item, detail, **kwargs: mapped_jobs[
                item["externalPath"]
            ],
        ),
    ):
        jobs = connector.fetch_jobs(request)

    assert len(jobs) == 2
    assert [job.job_id for job in jobs] == ["2", "4"]

def test_workday_search_uses_request_keyword():
    connector = WorkdayConnector()

    request = SearchRequest(
        keyword="CRM",
        location="India",
        page_size=20,
        max_jobs=1,
    )

    with (
        patch(
            "jobs.connectors.workday.connector.WorkdayDiscovery.load",
            return_value=[
                (
                    "example.wd5.myworkdayjobs.com",
                    "example",
                    "Careers",
                )
            ],
        ),
        patch(
            "jobs.connectors.workday.connector.WorkdayDiscovery.discover_live",
            return_value=[],
        ),
        patch(
            "jobs.connectors.workday.connector.WorkdayAPI.search_jobs",
            return_value={
                "total": 0,
                "jobPostings": [],
            },
        ) as mock_search,
    ):
        connector.fetch_jobs(request)

    mock_search.assert_called_once_with(
        search_text="CRM",
        offset=0,
        limit=20,
    )
