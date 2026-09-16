"""
Base connector interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from jobs.enums import ConnectorType, Portal
from jobs.job import Job
from jobs.search import SearchRequest


class BaseConnector(ABC):
    """
    Abstract base class for all job portal connectors.

    Attributes:
        PORTAL: The portal this connector works with.
        CONNECTOR_TYPE: The type of connector implementation.
        VERSION: The version of this connector.
    """

    PORTAL: Portal = Portal.UNKNOWN
    CONNECTOR_TYPE: ConnectorType = ConnectorType.UNKNOWN
    VERSION: str = "0.0.0"

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the connector."""
        pass

    @abstractmethod
    def fetch_jobs(self, request: SearchRequest) -> list[Job]:
        """
        Fetch jobs from the portal based on the search request.

        Args:
            request: SearchRequest containing keyword, location, and filters.

        Returns:
            list[Job]: List of normalized Job objects.
        """
        pass

    def set_repositories(self, raw_repo: Any, session_id: UUID) -> None:
        """
        Set repository context on the connector.

        Override this method if the connector needs to store raw data.

        Args:
            raw_repo: RawRepository instance for storing API responses.
            session_id: The current search session ID.
        """
        pass

    def set_registry(self, registry: Any) -> None:
        """
        Set the central job registry on connectors that support early lookup.

        Connectors that do not implement an early registry gate may ignore this
        hook.

        Args:
            registry: JobRegistry instance.
        """
        pass

    def set_candidate_gate(self, gate) -> None:
        """Set an optional early candidate-filter callback."""
        pass


# =============================================================================
# END OF FILE
# =============================================================================