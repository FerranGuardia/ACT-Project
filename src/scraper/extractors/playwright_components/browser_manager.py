"""
Browser Manager - Handles Playwright browser lifecycle and page management.

Provides a clean interface for browser creation, page management, and resource cleanup.
Supports browser reuse across multiple extraction operations.
"""

from typing import Optional, TYPE_CHECKING

try:
    from playwright.sync_api import sync_playwright, Browser, Page  # type: ignore[import-untyped]
    HAS_PLAYWRIGHT: bool = True
except ImportError:
    sync_playwright = None  # type: ignore[assignment, misc]
    Browser = None  # type: ignore[assignment, misc, used-before-def]
    Page = None  # type: ignore[assignment, misc, used-before-def]
    HAS_PLAYWRIGHT: bool = False

from core.logger import get_logger

logger = get_logger("scraper.extractors.browser_manager")


class BrowserManager:
    """
    Manages Playwright browser lifecycle and provides page instances.

    This class handles browser creation, page management, and cleanup,
    allowing browser reuse across multiple extraction operations.
    """

    def __init__(self, headless: bool = True, browser_args: Optional[list] = None):
        """
        Initialize the browser manager.

        Args:
            headless: Whether to run browser in headless mode
            browser_args: Additional arguments to pass to browser launch
        """
        self.headless = headless
        self.browser_args = browser_args or []
        self._playwright = None
        self._browser: Optional[Browser] = None

        if not HAS_PLAYWRIGHT:
            logger.warning("Playwright not available - browser manager will not function")

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def start(self) -> None:
        """Start the browser instance."""
        if not HAS_PLAYWRIGHT or sync_playwright is None:
            raise RuntimeError("Playwright not available")

        if self._playwright is None:
            logger.debug("Starting Playwright...")
            self._playwright = sync_playwright().start()

        if self._browser is None:
            logger.debug(f"Launching Chromium browser (headless={self.headless})...")
            self._browser = self._playwright.chromium.launch(
                headless=self.headless,
                args=self.browser_args
            )
            logger.debug("Browser launched successfully")

    def new_page(self) -> Page:
        """
        Create a new page instance.

        Returns:
            A new Playwright Page instance

        Raises:
            RuntimeError: If browser is not started
        """
        if self._browser is None:
            raise RuntimeError("Browser not started. Call start() first.")

        page = self._browser.new_page()

        # Set reasonable defaults for scraping
        page.set_default_timeout(30000)  # 30 seconds
        page.set_default_navigation_timeout(60000)  # 60 seconds

        logger.debug("Created new page")
        return page

    def close(self) -> None:
        """Close the browser and cleanup resources."""
        if self._browser:
            logger.debug("Closing browser...")
            try:
                self._browser.close()
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
            self._browser = None

        if self._playwright:
            logger.debug("Stopping Playwright...")
            try:
                self._playwright.stop()
            except Exception as e:
                logger.warning(f"Error stopping Playwright: {e}")
            self._playwright = None

    @property
    def is_running(self) -> bool:
        """Check if the browser is currently running."""
        return self._browser is not None

    def __del__(self):
        """Ensure cleanup on destruction."""
        try:
            self.close()
        except:
            pass  # Ignore errors during cleanup


__all__ = ["BrowserManager"]