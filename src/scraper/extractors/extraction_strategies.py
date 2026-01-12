"""
Extraction Strategies - Strategy pattern for different chapter extraction methods.

Provides clean separation between scrolling-based and pagination-based
chapter URL extraction strategies.
"""

from abc import ABC, abstractmethod
from typing import List, Any, Optional, Callable
from pathlib import Path

from core.logger import get_logger

from .pagination_detector import PaginationInfo
from .link_processor import LinkProcessor

logger = get_logger("scraper.extractors.extraction_strategies")


class ExtractionContext:
    """Context information for extraction operations."""

    def __init__(
        self,
        toc_url: str,
        base_url: str,
        should_stop: Optional[Callable[[], bool]] = None,
        min_chapter_number: Optional[int] = None,
        max_chapter_number: Optional[int] = None
    ):
        self.toc_url = toc_url
        self.base_url = base_url
        self.should_stop = should_stop
        self.min_chapter_number = min_chapter_number
        self.max_chapter_number = max_chapter_number

    def with_pagination(self, pagination: PaginationInfo) -> 'ExtractionContextWithPagination':
        """Create a context with pagination information."""
        return ExtractionContextWithPagination(
            toc_url=self.toc_url,
            base_url=self.base_url,
            should_stop=self.should_stop,
            min_chapter_number=self.min_chapter_number,
            max_chapter_number=self.max_chapter_number,
            pagination=pagination
        )


class ExtractionContextWithPagination(ExtractionContext):
    """Extended context with pagination information."""

    def __init__(self, pagination: PaginationInfo, **kwargs):
        super().__init__(**kwargs)
        self.pagination = pagination


class ExtractionStrategy(ABC):
    """Base class for chapter URL extraction strategies."""

    def __init__(self, link_processor: LinkProcessor):
        self.link_processor = link_processor

    @abstractmethod
    def extract(self, page: Any, context: ExtractionContext) -> List[str]:
        """
        Extract chapter URLs using this strategy.

        Args:
            page: Playwright page object
            context: Extraction context with parameters

        Returns:
            List of chapter URLs
        """
        pass

    @abstractmethod
    def name(self) -> str:
        """Return the name of this extraction strategy."""
        pass


class ScrollingExtractionStrategy(ExtractionStrategy):
    """Extraction strategy using scrolling to load lazy content."""

    def name(self) -> str:
        return "scrolling"

    def extract(self, page: Any, context: ExtractionContext) -> List[str]:
        """
        Extract chapters using scrolling method.

        Args:
            page: Playwright page object
            context: Extraction context

        Returns:
            List of chapter URLs
        """
        logger.debug("Starting scrolling-based extraction")

        # Run the scroll script
        scroll_result = self._run_scroll_script(page)

        if scroll_result > 0:
            logger.info(f"Scrolling complete. Found {scroll_result} chapter links in DOM.")
        else:
            logger.warning("Scroll script found no chapter links")

        # Wait for network idle
        self._wait_for_content_load(page)

        # Extract chapter URLs
        chapter_urls = self.link_processor.process_page_links(page)

        logger.info(f"✓ Scrolling extraction found {len(chapter_urls)} unique chapter URLs")
        return chapter_urls

    def _run_scroll_script(self, page: Any) -> int:
        """Run the Playwright scroll script and return result."""
        try:
            scroll_script = self._load_scroll_script()
            scroll_result = page.evaluate(scroll_script)
            return int(scroll_result) if scroll_result else 0
        except Exception as e:
            logger.error(f"Error running scroll script: {e}")
            return 0

    def _load_scroll_script(self) -> str:
        """Load the scroll script from file."""
        # Import the existing script loader function
        from .url_extractor_playwright import _load_playwright_scroll_script
        return _load_playwright_scroll_script()

    def _wait_for_content_load(self, page: Any) -> None:
        """Wait for content to finish loading after scrolling."""
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
            logger.debug("Network idle - all content should be loaded")
        except Exception as e:
            try:
                page.wait_for_load_state("domcontentloaded", timeout=5000)
                logger.debug("Network idle timeout, but DOM is loaded")
            except Exception:
                pass


class PaginationExtractionStrategy(ExtractionStrategy):
    """Extraction strategy using pagination to visit multiple pages."""

    def __init__(self, link_processor: LinkProcessor, max_pages: int = 200):
        super().__init__(link_processor)
        self.max_pages = max_pages

    def name(self) -> str:
        return "pagination"

    def extract(self, page: Any, context: ExtractionContext) -> List[str]:
        """
        Extract chapters by visiting pagination pages.

        Args:
            page: Playwright page object
            context: Extraction context with pagination info

        Returns:
            List of chapter URLs
        """
        if not isinstance(context, ExtractionContextWithPagination):
            logger.error("Pagination strategy requires pagination context")
            return []

        pagination = context.pagination
        toc_url = context.toc_url
        should_stop = context.should_stop

        logger.info(f"Starting pagination extraction with {len(pagination.page_urls)} pages")

        all_chapter_urls: List[str] = []

        # Extract from page 1 (already loaded)
        logger.debug("Collecting chapters from page 1...")
        page_chapters = self.link_processor.process_page_links(page)
        all_chapter_urls.extend(page_chapters)

        # Visit additional pages
        max_pages_to_visit = min(len(pagination.page_urls), self.max_pages)

        if pagination.page_urls:
            logger.info(f"Visiting {max_pages_to_visit} additional pages to collect all chapters...")

            total_pages = len(pagination.page_urls[:max_pages_to_visit])

            for idx, page_url in enumerate(pagination.page_urls[:max_pages_to_visit], 1):
                if should_stop and should_stop():
                    break

                progress_pct = (idx / total_pages * 100) if total_pages > 0 else 0
                logger.info(f"Loading page {idx}/{total_pages} ({progress_pct:.1f}%): {page_url}")

                try:
                    # Load the page
                    self._load_page_safely(page, page_url, should_stop)

                    # Extract chapters from this page
                    page_chapters = self.link_processor.process_page_links(page)
                    all_chapter_urls.extend(page_chapters)

                    logger.info(f"Page {idx}/{total_pages}: Found {len(page_chapters)} chapters (total so far: {len(all_chapter_urls)})")

                except Exception as e:
                    logger.warning(f"Error loading page {idx} ({page_url}) after retries: {e}")
                    continue

        # Remove duplicates
        unique_urls = self.link_processor.deduplicate_urls(all_chapter_urls)

        logger.info(f"✓ Pagination extraction found {len(unique_urls)} unique chapter URLs from {len(pagination.page_urls[:max_pages_to_visit]) + 1} pages")
        return unique_urls

    def _load_page_safely(self, page: Any, url: str, should_stop: Optional[Callable[[], bool]] = None) -> None:
        """Load a page with proper error handling and retries."""
        from .url_extractor_playwright import retry_with_backoff

        def load_page():
            page.goto(url, wait_until="domcontentloaded", timeout=30000)

            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=5000)
                except Exception:
                    pass

            # Handle Cloudflare if it appears
            self._handle_cloudflare_if_present(page)

        retry_with_backoff(load_page, max_retries=3, base_delay=1.0, should_stop=should_stop)

    def _handle_cloudflare_if_present(self, page: Any) -> None:
        """Handle Cloudflare challenges that appear during pagination."""
        try:
            page_title = page.title()
            if "just a moment" in page_title.lower() or "checking your browser" in page_title.lower():
                logger.debug("Cloudflare challenge detected on pagination page - waiting...")
                max_wait = 10
                waited = 0
                while waited < max_wait:
                    import time
                    time.sleep(1)
                    waited += 1
                    try:
                        current_title = page.title()
                        if not ("just a moment" in current_title.lower() or "checking your browser" in current_title.lower()):
                            break
                    except Exception:
                        pass
        except Exception:
            pass  # Best effort


__all__ = [
    "ExtractionStrategy",
    "ScrollingExtractionStrategy",
    "PaginationExtractionStrategy",
    "ExtractionContext",
    "ExtractionContextWithPagination"
]