"""
Cloudflare Handler - Detects and waits for Cloudflare challenge completion.

Provides clean, testable Cloudflare challenge detection and waiting logic
with configurable timeouts and proper error handling.
"""

from typing import Any, Optional
import time

from core.logger import get_logger

logger = get_logger("scraper.extractors.cloudflare_handler")


class CloudflareChallenge:
    """Represents the state of a Cloudflare challenge."""

    def __init__(self, detected: bool, title: str = ""):
        self.detected = detected
        self.title = title

    def is_resolved(self) -> bool:
        """Check if the challenge appears to be resolved."""
        if not self.detected:
            return True

        lower_title = self.title.lower()
        return ("just a moment" not in lower_title and
                "checking your browser" not in lower_title)


class CloudflareHandler:
    """
    Handles Cloudflare challenge detection and waiting.

    Provides clean, testable logic for detecting Cloudflare challenges
    and waiting for their completion with proper timeouts and error handling.
    """

    def __init__(self, max_wait_seconds: int = 15, check_interval: float = 1.0):
        """
        Initialize the Cloudflare handler.

        Args:
            max_wait_seconds: Maximum time to wait for challenge completion
            check_interval: How often to check challenge status (seconds)
        """
        self.max_wait_seconds = max_wait_seconds
        self.check_interval = check_interval

    def wait_for_completion(self, page: Any) -> bool:
        """
        Wait for Cloudflare challenge to complete if one is detected.

        Args:
            page: Playwright page object

        Returns:
            True if challenge completed or no challenge detected, False if timeout
        """
        challenge = self._detect_challenge(page)

        if not challenge.detected:
            logger.debug("No Cloudflare challenge detected")
            return True

        logger.warning(f"⚠ Cloudflare challenge detected (title: '{challenge.title}') - waiting...")
        return self._wait_for_resolution(page, challenge)

    def _detect_challenge(self, page: Any) -> CloudflareChallenge:
        """
        Detect if a Cloudflare challenge is present.

        Args:
            page: Playwright page object

        Returns:
            CloudflareChallenge object with detection results
        """
        try:
            title = page.title()
            lower_title = title.lower()

            is_cloudflare = ("just a moment" in lower_title or
                           "checking your browser" in lower_title)

            return CloudflareChallenge(is_cloudflare, title)

        except Exception as e:
            # If we can't get the title, assume no challenge (page might be navigating)
            logger.debug(f"Could not detect Cloudflare challenge (title check failed): {e}")
            return CloudflareChallenge(False)

    def _wait_for_resolution(self, page: Any, initial_challenge: CloudflareChallenge) -> bool:
        """
        Wait for the Cloudflare challenge to resolve.

        Args:
            page: Playwright page object
            initial_challenge: The initially detected challenge

        Returns:
            True if resolved, False if timeout
        """
        waited = 0

        while waited < self.max_wait_seconds:
            try:
                # Wait for DOM content to be loaded
                page.wait_for_load_state("domcontentloaded", timeout=5000)
                time.sleep(self.check_interval)
                waited += self.check_interval

                # Check current challenge status
                current_challenge = self._detect_challenge(page)

                if current_challenge.is_resolved():
                    logger.debug(f"Cloudflare challenge resolved after {waited:.1f} seconds")
                    return True

                # Log progress every 4 seconds
                if int(waited) % 4 == 0:
                    logger.debug(f"Still waiting for Cloudflare... ({waited:.1f}s)")

            except Exception as e:
                logger.debug(f"Error during Cloudflare wait (may be navigation): {e}")
                time.sleep(self.check_interval)
                waited += self.check_interval

                # Try to recover by waiting for load state
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=5000)
                except Exception:
                    pass  # Continue waiting

        logger.warning(f"⚠ Cloudflare wait timed out after {self.max_wait_seconds} seconds")
        return False

    def handle_post_challenge_wait(self, page: Any) -> None:
        """
        Perform any necessary waiting after challenge resolution.

        Args:
            page: Playwright page object
        """
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            try:
                page.wait_for_load_state("domcontentloaded", timeout=5000)
            except Exception:
                pass  # Best effort


__all__ = ["CloudflareHandler", "CloudflareChallenge"]