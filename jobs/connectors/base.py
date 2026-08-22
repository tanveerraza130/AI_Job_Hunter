"""
Base connector interface.
"""

from abc import ABC, abstractmethod

from jobs.models import Job


class BaseConnector(ABC):
    @abstractmethod
    def fetch_jobs(self) -> list[Job]:
        raise NotImplementedError