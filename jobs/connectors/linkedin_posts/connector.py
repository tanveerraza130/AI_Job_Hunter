"""
LinkedIn public hiring-post connector.

Production adapter:

    discovery -> public LinkedIn post URL
              -> LinkedInHiringPostParser
              -> LinkedInHiringPostProcessor
              -> canonical Job

Discovery is deliberately injected. This connector does not authenticate
to LinkedIn, bypass access controls, use proxies, solve CAPTCHAs, or access
member-only content.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from jobs.base import BaseConnector
from jobs.enums import ConnectorType, Portal
from jobs.job import Job
from jobs.linkedin_posts.models import LinkedInHiringPost
from jobs.linkedin_posts.parser import LinkedInHiringPostParser
from jobs.linkedin_posts.processor import LinkedInHiringPostProcessor
from jobs.search import SearchRequest


PostURLDiscovery = Callable[[SearchRequest], Iterable[str]]


class LinkedInPostsConnector(BaseConnector):
    """Adapter that brings public LinkedIn hiring posts into Job pipeline."""

    PORTAL = Portal.LINKEDIN_POST
    CONNECTOR_TYPE = ConnectorType.API
    VERSION = "1.0.0"

    def __init__(
        self,
        context: Any = None,
        *,
        discovery: PostURLDiscovery | None = None,
        parser: LinkedInHiringPostParser | None = None,
        processor: LinkedInHiringPostProcessor | None = None,
    ) -> None:
        self.context = context
        self.discovery = discovery
        self.parser = parser or LinkedInHiringPostParser()
        self.processor = processor or LinkedInHiringPostProcessor()

    @property
    def name(self) -> str:
        return "LinkedIn Hiring Posts"

    def fetch_jobs(self, request: SearchRequest) -> list[Job]:
        """
        Discover public post URLs and return qualified canonical Jobs.

        Returns an empty list when no discovery provider is configured.
        """
        if self.discovery is None:
            return []

        jobs: list[Job] = []
        seen_post_ids: set[str] = set()
        seen_urls: set[str] = set()

        for post_url in self.discovery(request):
            if not isinstance(post_url, str):
                continue

            post_url = post_url.strip()

            if not post_url or post_url in seen_urls:
                continue

            seen_urls.add(post_url)

            post = self.parser.parse(
                post_url,
                discovery_query=request.keyword,
            )

            if post is None:
                continue

            if post.post_id in seen_post_ids:
                continue

            seen_post_ids.add(post.post_id)

            qualified = self.processor.process(post)

            if qualified is None:
                continue

            jobs.append(self._post_to_job(qualified))

        return jobs

    @staticmethod
    def _post_to_job(post: LinkedInHiringPost) -> Job:
        """Convert a qualified LinkedIn hiring post to canonical Job."""
        return Job(
            job_id=post.post_id,
            title=post.role or "LinkedIn Hiring Post",
            company=post.company or post.author_name or "Unknown",
            location=post.location or "",
            description=post.text,
            job_url=post.post_url,
            portal=Portal.LINKEDIN_POST.value,
            discovery_keyword=post.discovery_query or "",
            posted_date=(
                post.posted_at.date()
                if post.posted_at is not None
                else None
            ),
            raw={
                "linkedin_post": post.raw,
                "author_name": post.author_name,
                "author_url": post.author_url,
                "author_headline": post.author_headline,
                "company_url": post.company_url,
                "application_url": post.application_url,
                "contact_email": post.contact_email,
                "relevance_score": post.relevance_score,
            },
        )
