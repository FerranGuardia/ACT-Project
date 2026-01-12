"""
Browser Manager - Handles Playwright browser lifecycle and page management.

Provides centralized browser management with proper resource cleanup
and reusable browser instances.
"""

from typing import Optional, Any
from contextlib import contextmanager

try:
    from playwright.sync_api import sync_playwright, Browser, Page  # type: ignore[import-untyped]
    HAS_PLAYWRIGHT: bool = True
except ImportError:
    sync_playwright = None  # type: ignore[assignment, misc]
    Browser = None  # type: ignore[assignment, misc]
    Page = None  # type: ignore[assignment, misc]
    HAS_PLAYWRIGHT = False

from core.logger import get_logger

logger = get_logger("scraper.extractors.browser_manager")


class BrowserManager:
    """
    Manages Playwright browser lifecycle and provides reusable browser instances.

    This class handles the browser creation, configuration, and cleanup,
    allowing multiple extractors to share the same browser instance.
    """

    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize the browser manager.

        Args:
            headless: Whether to run browser in headless mode
            timeout: Default timeout for page operations in milliseconds
        """
        if not HAS_PLAYWRIGHT:
            raise ImportError("Playwright not available. Install with: pip install playwright")

        self.headless = headless
        self.timeout = timeout
        self._playwright = None
        self._browser: Optional[Browser] = None

    def __enter__(self):
        """Context manager entry - start the browser."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close the browser."""
        self.close()

    def start(self) -> None:
        """Start the browser if not already running."""
        if self._browser is not None:
            return  # Already started

        logger.debug(f"Starting Playwright browser (headless={self.headless})")
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
        )
        logger.debug("Browser started successfully")

    def close(self) -> None:
        """Close the browser and cleanup resources."""
        if self._browser:
            logger.debug("Closing browser")
            try:
                self._browser.close()
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
            self._browser = None

        if self._playwright:
            try:
                self._playwright.stop()
            except Exception as e:
                logger.warning(f"Error stopping playwright: {e}")
            self._playwright = None

    def new_page(self) -> Page:
        """
        Create a new page from the managed browser.

        Returns:
            A new Playwright page instance

        Raises:
            RuntimeError: If browser is not started
        """
        if self._browser is None:
            raise RuntimeError("Browser not started. Call start() first or use as context manager.")

        page = self._browser.new_page()
        page.set_default_timeout(self.timeout)
        return page

    def is_running(self) -> bool:
        """Check if the browser is currently running."""
        return self._browser is not None

    @contextmanager
    def page_context(self):
        """
        Context manager for page lifecycle.

        Usage:
            with browser_manager.page_context() as page:
                page.goto(url)
                # ... use page ...
            # Page is automatically closed
        """
        page = None
        try:
            page = self.new_page()
            yield page
        finally:
            if page:
                try:
                    page.close()
                except Exception as e:
                    logger.warning(f"Error closing page: {e}")


__all__ = ["BrowserManager"]