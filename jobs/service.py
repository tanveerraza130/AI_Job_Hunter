"""
Job scanning service.
"""

from core.logger import get_logger
from jobs.base import BaseConnector
from jobs.job import Job
from jobs.search import SearchRequest

logger = get_logger(__name__)


class ScanService:
    def __init__(self, connectors: list[BaseConnector]):
        self.connectors = connectors

    def run(self, search_request: SearchRequest) -> list[Job]:
        """
        Run all connectors with a search request.

        Args:
            search_request: SearchRequest object containing keyword, location, max_jobs.

        Returns:
            list[Job]: List of jobs collected from all connectors.
        """
        jobs: list[Job] = []

        for connector in self.connectors:
            connector_name = connector.__class__.__name__

            logger.info("Running %s with keyword: %s", connector_name, search_request.keyword)

            try:
                connector_jobs = connector.fetch_jobs(search_request)

                logger.info(
                    "%s returned %d jobs",
                    connector_name,
                    len(connector_jobs),
                )

                jobs.extend(connector_jobs)

            except Exception:
                logger.exception(
                    "%s failed",
                    connector_name,
                )

        logger.info(
            "Collected %d jobs",
            len(jobs),
        )

        return jobs