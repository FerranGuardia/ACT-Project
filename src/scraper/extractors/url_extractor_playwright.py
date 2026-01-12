"""
Playwright-based chapter URL extraction.

Handles the most reliable but slowest method for extracting chapter URLs
using Playwright with scrolling and pagination support.
"""

import re
import time
from pathlib import Path
from typing import Any, Callable, List, Optional

try:
    from playwright.sync_api import \
        sync_playwright  # type: ignore[import-untyped]
    HAS_PLAYWRIGHT: bool = True
except ImportError:
    sync_playwright = None  # type: ignore[assignment, misc]
    HAS_PLAYWRIGHT: bool = False  # type: ignore[constant-redefinition]

from core.logger import get_logger

from ..chapter_parser import extract_chapter_number, normalize_url
# Import new component architecture
from .browser_manager import BrowserManager
from .cloudflare_handler import CloudflareHandler
from .extraction_strategies import (ExtractionContext,
                                    PaginationExtractionStrategy,
                                    ScrollingExtractionStrategy)
from .link_processor import LinkProcessor
from .pagination_detector import PaginationDetector
from .url_extractor_validators import is_chapter_url

logger = get_logger("scraper.extractors.url_extractor_playwright")


def retry_with_backoff(func: Callable[..., Any], max_retries: int = 3, base_delay: float = 1.0, should_stop: Optional[Callable[[], bool]] = None):
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry (should be a callable that takes no arguments)
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (will be multiplied by 2^attempt)
        should_stop: Optional callable to check if we should stop retrying
    
    Returns:
        Result of the function call
    
    Raises:
        Exception: The last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries):
        if should_stop and should_stop():
            raise Exception("Operation cancelled by user")
        
        try:
            return func()
        except Exception as e:
            last_exception = e
            
            if attempt < max_retries - 1:
                wait_time = base_delay * (2 ** attempt)  # Exponential backoff
                logger.debug(f"Retry {attempt + 1}/{max_retries} after {wait_time:.1f}s: {str(e)[:100]}")
                time.sleep(wait_time)
                continue
            else:
                raise
    
    if last_exception:
        raise last_exception


def _load_playwright_scroll_script() -> str:
    """
    Load and bundle all Playwright scroll script modules.
    
    Modules are loaded in dependency order:
    1. chapter_detector.js - Chapter link detection
    2. link_counter.js - Link counting utilities
    3. load_more_handler.js - Load More button handling
    4. container_finder.js - Container finding utilities
    5. scroll_operations.js - Scroll operation helpers
    6. scroll_loop.js - Main scroll loop logic
    7. main.js - Entry point
    
    Returns:
        JavaScript code as string, wrapped in async function call
    """
    script_dir = Path(__file__).parent.parent / "playwright_scripts"
    
    # Define modules in dependency order
    modules = [
        ("chapter_detector", "chapter_detector.js"),
        ("link_counter", "link_counter.js"),
        ("load_more_handler", "load_more_handler.js"),
        ("container_finder", "container_finder.js"),
        ("scroll_operations", "scroll_operations.js"),
        ("scroll_loop", "scroll_loop.js"),
        ("main", "main.js"),
    ]
    
    bundled_parts = []
    for module_name, filename in modules:
        module_path = script_dir / filename
        try:
            with open(module_path, "r", encoding="utf-8") as f:
                module_content = f.read()
            bundled_parts.append(f"// === {module_name} ===\n{module_content}")
        except FileNotFoundError:
            logger.error(f"Playwright module '{module_name}' not found at {module_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading Playwright module '{module_name}': {e}")
            raise
    
    # Combine all modules
    bundled_script = "\n\n".join(bundled_parts)
    
    # Wrap in async function call for page.evaluate()
    return f"async () => {{ {bundled_script} return await scrollAndCountChapters(); }}"


class PlaywrightExtractor:
    """
    Clean orchestrator for Playwright-based chapter URL extraction.

    Uses composition with specialized components for browser management,
    Cloudflare handling, pagination detection, and extraction strategies.
    """

    def __init__(
        self,
        base_url: str,
        session_manager: Any,  # SessionManager from url_extractor_session
        timeout: int = 30000,
        delay: float = 1.0,
    ):
        """
        Initialize the Playwright extractor with component dependencies.

        Args:
            base_url: Base URL for link normalization
            session_manager: Session manager for rate limiting
            timeout: Default timeout for operations
            delay: Delay between operations
        """
        self.base_url = base_url
        self.session_manager = session_manager
        self.timeout = timeout
        self.delay = delay

        # Initialize components
        self.browser_manager = BrowserManager(headless=True, timeout=timeout)
        self.cloudflare_handler = CloudflareHandler(max_wait_seconds=15)
        self.pagination_detector = PaginationDetector(max_pages=200)
        self.link_processor = LinkProcessor(base_url)

        # Initialize extraction strategies
        self.extraction_strategies = {
            "scrolling": ScrollingExtractionStrategy(self.link_processor),
            "pagination": PaginationExtractionStrategy(self.link_processor, max_pages=200)
        }
    
    def extract(
        self,
        toc_url: str,
        should_stop: Optional[Callable[[], bool]] = None,
        min_chapter_number: Optional[int] = None,
        max_chapter_number: Optional[int] = None
    ) -> List[str]:
        """
        Extract chapter URLs using Playwright with clean component architecture.

        This method orchestrates the extraction process using specialized components
        for browser management, Cloudflare handling, pagination detection, and
        extraction strategies.

        Args:
            toc_url: Table of contents URL to extract from
            should_stop: Optional callback to check if extraction should stop
            min_chapter_number: Minimum chapter number to consider
            max_chapter_number: Maximum chapter number to consider

        Returns:
            List of chapter URLs found
        """
        if not HAS_PLAYWRIGHT or sync_playwright is None:
            logger.warning("Playwright not available - install with: pip install playwright && playwright install chromium")
            return []

        try:
            logger.info("Starting Playwright extraction with component architecture...")

            # Create extraction context
            context = ExtractionContext(
                toc_url=toc_url,
                base_url=self.base_url,
                should_stop=should_stop,
                min_chapter_number=min_chapter_number,
                max_chapter_number=max_chapter_number
            )

            # Use browser manager for clean resource handling
            with self.browser_manager.page_context() as page:
                logger.debug(f"Navigating to {toc_url}...")
                page.goto(toc_url, wait_until="networkidle", timeout=60000)

                # Handle Cloudflare challenge
                if not self.cloudflare_handler.wait_for_completion(page):
                    logger.warning("Failed to resolve Cloudflare challenge")
                    return []

                # Check for CAPTCHA (legacy method - could be improved)
                self._check_captcha(page)

                # Detect pagination
                pagination = self.pagination_detector.detect(page, toc_url)

                # Choose extraction strategy
                if pagination:
                    logger.info(f"Using pagination strategy ({len(pagination.page_urls)} pages)")
                    strategy = self.extraction_strategies["pagination"]
                    context_with_pagination = context.with_pagination(pagination)
                    return strategy.extract(page, context_with_pagination)
                else:
                    logger.info("Using scrolling strategy")
                    strategy = self.extraction_strategies["scrolling"]
                    return strategy.extract(page, context)

        except Exception as e:
            error_msg = str(e).lower()
            if "execution context was destroyed" in error_msg or "navigation" in error_msg:
                logger.error(f"Playwright failed due to page navigation (likely Cloudflare protection): {e}")
                logger.warning("⚠ This site may have strong anti-bot protection that prevents automated scraping")
                logger.warning("💡 Consider using manual methods or alternative scraping approaches for this site")
            else:
                logger.error(f"Playwright extraction failed: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return []
    
    def _check_captcha(self, page: Any) -> None:
        """Check for CAPTCHA (separate from Cloudflare)."""
        try:
            captcha_iframes = page.query_selector_all('iframe[src*="captcha"], iframe[src*="recaptcha"]')  # type: ignore[attr-defined]
            if captcha_iframes:
                logger.warning("⚠ CAPTCHA detected (separate from Cloudflare) - this may block scraping")
                time.sleep(3)  # Brief wait in case it auto-resolves
        except Exception as e:
            pass

