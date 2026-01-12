"""
Cloudflare Handler - Detects and waits for Cloudflare challenge completion.

Provides clean, testable logic for handling Cloudflare protection challenges.
"""

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page  # type: ignore[import-untyped]

from core.logger import get_logger

logger = get_logger("scraper.extractors.cloudflare_handler")


class CloudflareHandler:
    """
    Handles Cloudflare challenge detection and waiting.

    Provides clean, configurable logic for detecting and waiting for
    Cloudflare challenges to complete.
    """

    def __init__(
        self,
        max_wait_seconds: int = 15,
        check_interval_seconds: float = 1.0,
        initial_delay_seconds: float = 3.0
    ):
        """
        Initialize the Cloudflare handler.

        Args:
            max_wait_seconds: Maximum time to wait for challenge completion
            check_interval_seconds: How often to check challenge status
            initial_delay_seconds: Initial delay before first check
        """
        self.max_wait_seconds = max_wait_seconds
        self.check_interval_seconds = check_interval_seconds
        self.initial_delay_seconds = initial_delay_seconds

    def wait_for_completion(self, page: "Page") -> bool:
        """
        Wait for Cloudflare challenge to complete.

        Args:
            page: Playwright page instance

        Returns:
            True if challenge completed or no challenge detected,
            False if timeout exceeded
        """
        if not self._is_cloudflare_challenge(page):
            logger.debug("No Cloudflare challenge detected")
            return True

        logger.warning("⚠ Cloudflare challenge detected - waiting for completion...")

        # Initial delay before checking
        time.sleep(self.initial_delay_seconds)

        return self._wait_for_challenge_resolution(page)

    def _is_cloudflare_challenge(self, page: "Page") -> bool:
        """
        Check if the current page has a Cloudflare challenge.

        Args:
            page: Playwright page instance

        Returns:
            True if Cloudflare challenge is detected
        """
        try:
            title = page.title.lower()
            return ("just a moment" in title or
                   "checking your browser" in title or
                   "please wait" in title)
        except Exception as e:
            logger.debug(f"Error checking page title for Cloudflare: {e}")
            return False

    def _wait_for_challenge_resolution(self, page: "Page") -> bool:
        """
        Wait for the Cloudflare challenge to resolve.

        Args:
            page: Playwright page instance

        Returns:
            True if challenge resolved, False if timeout
        """
        waited = 0

        while waited < self.max_wait_seconds:
            try:
                # Wait for DOM content to load
                page.wait_for_load_state("domcontentloaded", timeout=5000)

                # Check if challenge is still active
                if not self._is_cloudflare_challenge(page):
                    logger.debug(f"Cloudflare challenge completed after {waited + self.initial_delay_seconds:.1f}s")
                    return True

                # Wait before next check
                time.sleep(self.check_interval_seconds)
                waited += self.check_interval_seconds

                # Log progress at intervals
                if waited % 4 < self.check_interval_seconds:  # Log roughly every 4 seconds
                    logger.debug(f"Still waiting for Cloudflare... ({waited:.1f}s)")

            except Exception as e:
                logger.debug(f"Error during Cloudflare wait (may be navigation): {e}")
                time.sleep(self.check_interval_seconds)
                waited += self.check_interval_seconds

        logger.warning(f"⚠ Cloudflare wait timed out after {self.max_wait_seconds}s")
        return False


class CaptchaHandler:
    """
    Handles CAPTCHA detection and basic waiting.

    Separate from CloudflareHandler for better separation of concerns.
    """

    def __init__(self, wait_seconds: float = 3.0):
        """
        Initialize the CAPTCHA handler.

        Args:
            wait_seconds: Time to wait after CAPTCHA detection
        """
        self.wait_seconds = wait_seconds

    def check_and_wait(self, page: "Page") -> None:
        """
        Check for CAPTCHA and wait if detected.

        Args:
            page: Playwright page instance
        """
        if self._has_captcha(page):
            logger.warning("⚠ CAPTCHA detected - waiting briefly...")
            time.sleep(self.wait_seconds)

    def _has_captcha(self, page: "Page") -> bool:
        """
        Check if page contains CAPTCHA elements.

        Args:
            page: Playwright page instance

        Returns:
            True if CAPTCHA detected
        """
        try:
            # Check for common CAPTCHA selectors
            captcha_selectors = [
                'iframe[src*="captcha"]',
                'iframe[src*="recaptcha"]',
                '[class*="captcha"]',
                '[id*="captcha"]',
                '.recaptcha',
                '#recaptcha'
            ]

            for selector in captcha_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        return True
                except:
                    continue

            return False

        except Exception as e:
            logger.debug(f"Error checking for CAPTCHA: {e}")
            return False


__all__ = ["CloudflareHandler", "CaptchaHandler"]