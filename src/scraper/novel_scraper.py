"""
Novel scraper with failsafe methods for webnovel content extraction.

Combines URL extraction and content extraction modules to provide
a unified interface for webnovel scraping.
Works for most webnovel sites without site-specific code.
"""

from typing import Optional, Tuple, List, Any

from .base import BaseScraper
from .extractors.url_extractor import UrlExtractor
from .extractors.chapter_extractor import ChapterExtractor
from core.logger import get_logger
from utils.validation import validate_url

logger = get_logger("scraper.novel_scraper")


__all__ = ["NovelScraper"]


class NovelScraper(BaseScraper):
    """
    Novel scraper with failsafe methods for webnovel sites.
    
    Combines URL extraction and content extraction modules to provide
    a unified interface. Uses failsafe methods that try multiple
    approaches in order of speed.
    """

    def __init__(self, base_url: str, **kwargs: Any):
        """
        Initialize novel scraper.
        
        Args:
            base_url: Base URL of the webnovel site
            **kwargs: Additional arguments passed to BaseScraper
        """
        super().__init__(base_url, **kwargs)
        
        # Initialize URL extractor and chapter extractor
        self.url_extractor = UrlExtractor(
            base_url=base_url,
            timeout=self.timeout,
            delay=self.delay
        )
        self.chapter_extractor = ChapterExtractor(
            base_url=base_url,
            timeout=self.timeout,
            delay=self.delay
        )

    def get_chapter_urls(self, toc_url: str, min_chapter_number: Optional[int] = None, max_chapter_number: Optional[int] = None) -> List[str]:
        """
        Get list of chapter URLs using failsafe methods.

        Delegates to UrlExtractor which tries methods in order of speed:
        1. JavaScript variable extraction
        2. AJAX endpoint discovery
        3. HTML parsing
        4. Playwright with scrolling
        5. Follow "next" links

        Args:
            toc_url: URL of the table of contents page
            min_chapter_number: Optional minimum chapter number needed (for pagination detection)
            max_chapter_number: Optional maximum chapter number needed (for range validation)

        Returns:
            List of chapter URLs, sorted by chapter number

        Raises:
            ValueError: If URL validation fails
        """
        # Validate input URL
        is_valid, validation_result = validate_url(toc_url)
        if not is_valid:
            raise ValueError(f"Invalid table of contents URL: {validation_result}")

        toc_url = validation_result  # Use sanitized URL

        result = self.url_extractor.fetch(
            toc_url,
            should_stop=self.check_should_stop,  # type: ignore[arg-type]
            min_chapter_number=min_chapter_number,
            max_chapter_number=max_chapter_number
        )
        urls: List[str] = result[0]
        _: Any = result[1]  # Metadata dict, unused
        return urls


    def scrape_chapter(self, chapter_url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Scrape a single chapter using failsafe methods.

        Delegates to ChapterExtractor which uses multiple selector patterns
        to extract content and titles.

        Args:
            chapter_url: URL of the chapter to scrape

        Returns:
            Tuple of (content, title, error_message)
            - content: Scraped and cleaned text content
            - title: Chapter title
            - error_message: Error message if scraping failed, None otherwise

        Raises:
            ValueError: If URL validation fails
        """
        # Validate input URL
        is_valid, validation_result = validate_url(chapter_url)
        if not is_valid:
            raise ValueError(f"Invalid chapter URL: {validation_result}")

        chapter_url = validation_result  # Use sanitized URL

        return self.chapter_extractor.scrape(chapter_url, should_stop=self.check_should_stop)  # type: ignore[arg-type]

