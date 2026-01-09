"""
Base scraper class for webnovel content extraction.

Provides abstract interface and common functionality for all scrapers.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, List, Callable
from pathlib import Path

from core.logger import get_logger
from core.config_manager import get_config
from .text_cleaner import clean_text
from .chapter_parser import extract_chapter_number as _extract_chapter_number, sort_chapters_by_number
from .config import REQUEST_TIMEOUT, REQUEST_DELAY, MAX_RETRIES

__all__ = ['BaseScraper']

logger = get_logger("scraper.base")


class BaseScraper(ABC):
    """
    Base class for all webnovel scrapers.

    Provides common functionality and defines the interface that
    all specific scrapers must implement.
    """

    def __init__(
        self,
        base_url: str,
        should_stop: Optional[Callable[[], bool]] = None,
    ):
        """
        Initialize the base scraper.

        Args:
            base_url: Base URL of the webnovel site
            should_stop: Optional callback function that returns True if scraping should stop
        """
        self.base_url = base_url
        self.should_stop = should_stop or (lambda: False)
        self.config = get_config()
        self.logger = logger

        # Get settings from config with fallback to defaults
        self.timeout = self.config.get("scraper.timeout", REQUEST_TIMEOUT)
        self.delay = self.config.get("scraper.delay", REQUEST_DELAY)
        self.max_retries = self.config.get("scraper.max_retries", MAX_RETRIES)

    @abstractmethod
    def scrape_chapter(self, chapter_url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Scrape a single chapter.

        Args:
            chapter_url: URL of the chapter to scrape

        Returns:
            Tuple of (content, title, error_message)
            - content: Scraped and cleaned text content
            - title: Chapter title
            - error_message: Error message if scraping failed, None otherwise
        """
        pass

    @abstractmethod
    def get_chapter_urls(self, toc_url: str) -> List[str]:
        """
        Get list of chapter URLs from table of contents.

        Args:
            toc_url: URL of the table of contents page

        Returns:
            List of chapter URLs
        """
        pass

    def clean_content(self, content: str) -> str:
        """
        Clean scraped content using text cleaner.

        Args:
            content: Raw scraped content

        Returns:
            Cleaned content ready for TTS
        """
        return clean_text(content)

    def extract_chapter_number(self, url: str) -> Optional[int]:
        """
        Extract chapter number from URL.

        Args:
            url: Chapter URL

        Returns:
            Chapter number, or None if not found
        """
        return _extract_chapter_number(url)

    def sort_chapters(self, chapter_urls: List[str]) -> List[str]:
        """
        Sort chapter URLs by chapter number.

        Args:
            chapter_urls: List of chapter URLs

        Returns:
            Sorted list of chapter URLs
        """
        return sort_chapters_by_number(chapter_urls)

    def save_chapter(
        self,
        content: str,
        title: str,
        chapter_num: Optional[int],
        output_dir: Path,
    ) -> Path:
        """
        Save scraped chapter to file.

        Args:
            content: Chapter content
            title: Chapter title
            chapter_num: Chapter number (optional)
            output_dir: Directory to save the file

        Returns:
            Path to saved file
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        if chapter_num is not None:
            filename = f"Chapter_{chapter_num:04d}_{title}.txt"
        else:
            filename = f"{title}.txt"

        # Sanitize filename
        filename = "".join(c for c in filename if c.isalnum() or c in (" ", "-", "_", ".")).strip()
        filename = filename.replace(" ", "_")

        filepath = output_dir / filename

        # Write content
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"{title}\n\n")
            f.write(content)

        self.logger.info(f"Saved chapter to {filepath}")
        return filepath

    def check_should_stop(self) -> bool:
        """
        Check if scraping should stop.

        Returns:
            True if scraping should stop, False otherwise
        """
        return self.should_stop()

    def log(self, message: str, level: str = "info") -> None:
        """
        Log a message using the logger.

        Args:
            message: Message to log
            level: Log level ('debug', 'info', 'warning', 'error')
        """
        log_func = getattr(self.logger, level.lower(), self.logger.info)
        log_func(message)

