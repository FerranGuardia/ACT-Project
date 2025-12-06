"""
Generic scraper with failsafe methods for webnovel content extraction.

Combines URL fetching and content scraping modules to provide
a unified interface for webnovel scraping.
Works for most webnovel sites without site-specific code.
"""

from typing import Optional, Tuple, List, Callable

from .base_scraper import BaseScraper
from .url_fetcher import ChapterUrlFetcher
from .content_scraper import ContentScraper
from .config import REQUEST_TIMEOUT, REQUEST_DELAY
from core.logger import get_logger

logger = get_logger("scraper.generic_scraper")


class GenericScraper(BaseScraper):
    """
    Generic scraper with failsafe methods for webnovel sites.
    
    Combines URL fetching and content scraping modules to provide
    a unified interface. Uses failsafe methods that try multiple
    approaches in order of speed.
    """

    def __init__(self, base_url: str, **kwargs):
        """
        Initialize generic scraper.
        
        Args:
            base_url: Base URL of the webnovel site
            **kwargs: Additional arguments passed to BaseScraper
        """
        super().__init__(base_url, **kwargs)
        
        # Initialize URL fetcher and content scraper
        self.url_fetcher = ChapterUrlFetcher(
            base_url=base_url,
            timeout=self.timeout,
            delay=self.delay
        )
        self.content_scraper = ContentScraper(
            base_url=base_url,
            timeout=self.timeout,
            delay=self.delay
        )

    def get_chapter_urls(self, toc_url: str, min_chapter_number: Optional[int] = None, max_chapter_number: Optional[int] = None) -> List[str]:
        """
        Get list of chapter URLs using failsafe methods.
        
        Delegates to ChapterUrlFetcher which tries methods in order of speed:
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
        """
        urls, _ = self.url_fetcher.fetch(
            toc_url, 
            should_stop=self.check_should_stop,
            min_chapter_number=min_chapter_number,
            max_chapter_number=max_chapter_number
        )
        return urls


    def scrape_chapter(self, chapter_url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Scrape a single chapter using failsafe methods.
        
        Delegates to ContentScraper which uses multiple selector patterns
        to extract content and titles.
        
        Args:
            chapter_url: URL of the chapter to scrape
            
        Returns:
            Tuple of (content, title, error_message)
            - content: Scraped and cleaned text content
            - title: Chapter title
            - error_message: Error message if scraping failed, None otherwise
        """
        return self.content_scraper.scrape(chapter_url, should_stop=self.check_should_stop)

