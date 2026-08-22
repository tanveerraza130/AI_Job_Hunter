"""
Browser context manager.

Responsible for creating and managing persistent Playwright browser contexts.

Responsibilities:
- Persistent browser profiles
- Cookies
- Local storage
- Downloads
- Viewport
- Locale
- Timezone
- User agent

No portal-specific logic belongs here.
"""

from pathlib import Path

from playwright.sync_api import (
    BrowserContext,
    Playwright,
)

from core.logger import get_logger

logger = get_logger(__name__)


class BrowserContextManager:
    """
    Creates a persistent Playwright browser context.
    """

    def __init__(
        self,
        playwright: Playwright,
        profile_directory: Path,
        *,
        headless: bool,
        viewport_width: int,
        viewport_height: int,
        user_agent: str,
        locale: str,
        timezone: str,
        downloads_path: Path,
    ) -> None:

        self.playwright = playwright

        self.profile_directory = Path(profile_directory)

        self.headless = headless

        self.viewport_width = viewport_width

        self.viewport_height = viewport_height

        self.user_agent = user_agent

        self.locale = locale

        self.timezone = timezone

        self.downloads_path = Path(downloads_path)

        self.context: BrowserContext | None = None

    def start(self) -> BrowserContext:
        """
        Launch a persistent Chromium context.
        """

        self.profile_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.downloads_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        logger.info(
            "Launching persistent browser profile: %s",
            self.profile_directory,
        )

        self.context = (
            self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_directory),
                headless=self.headless,
                viewport={
                    "width": self.viewport_width,
                    "height": self.viewport_height,
                },
                locale=self.locale,
                timezone_id=self.timezone,
                user_agent=self.user_agent,
                accept_downloads=True,
                downloads_path=str(self.downloads_path),
            )
        )

        return self.context

    def stop(self) -> None:
        """
        Close the browser context.
        """

        if self.context is not None:
            logger.info("Closing browser context...")
            self.context.close()
            self.context = None