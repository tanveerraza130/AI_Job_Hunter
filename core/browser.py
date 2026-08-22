"""
Browser manager.

Responsible for:
- Starting/stopping Playwright
- Creating persistent browser contexts

No portal-specific logic belongs here.
"""

from pathlib import Path

from playwright.sync_api import (
    BrowserContext,
    Playwright,
    sync_playwright,
)

from core.browser_context import BrowserContextManager
from core.logger import get_logger

logger = get_logger(__name__)


class BrowserManager:
    """
    High-level wrapper around Playwright.
    """

    def __init__(
        self,
        *,
        profile_directory: Path,
        downloads_directory: Path,
        headless: bool,
        viewport_width: int,
        viewport_height: int,
        user_agent: str,
        locale: str,
        timezone: str,
    ) -> None:

        self.profile_directory = Path(profile_directory)
        self.downloads_directory = Path(downloads_directory)

        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

        self.user_agent = user_agent
        self.locale = locale
        self.timezone = timezone

        self.playwright: Playwright | None = None
        self.context: BrowserContext | None = None
        self.context_manager: BrowserContextManager | None = None

    def start(self) -> None:
        """
        Start Playwright and create a persistent browser context.
        """

        logger.info("Starting Playwright...")

        self.playwright = sync_playwright().start()

        self.context_manager = BrowserContextManager(
            playwright=self.playwright,
            profile_directory=self.profile_directory,
            headless=self.headless,
            viewport_width=self.viewport_width,
            viewport_height=self.viewport_height,
            user_agent=self.user_agent,
            locale=self.locale,
            timezone=self.timezone,
            downloads_path=self.downloads_directory,
        )

        self.context = self.context_manager.start()

        logger.info("Browser ready.")

    def new_page(self):
        """
        Create a new page in the persistent browser context.
        """

        if self.context is None:
            raise RuntimeError("Browser has not been started.")

        return self.context.new_page()

    def stop(self) -> None:
        """
        Close browser context and Playwright.
        """

        logger.info("Stopping browser...")

        if self.context_manager is not None:
            self.context_manager.stop()

        if self.playwright is not None:
            self.playwright.stop()

        self.context = None
        self.context_manager = None
        self.playwright = None

        logger.info("Browser stopped.")