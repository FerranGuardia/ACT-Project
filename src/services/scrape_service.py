"""
Standalone scraping service that exposes a simple, consistent API.
"""

from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from core.logger import get_logger
from scraper import NovelScraper
from utils.validation import validate_url

logger = get_logger("services.scrape_service")


class ScrapeService:
    """Standalone scraping service for chapter discovery and content extraction."""

    def __init__(self):
        self._scraper_cache: Dict[str, NovelScraper] = {}

    def get_chapter_urls(self, toc_url: str) -> List[str]:
        """Get all chapter URLs for a table of contents URL."""
        clean_url = self._validate_url(toc_url)
        scraper = self._get_scraper_for_url(clean_url)
        return scraper.get_chapter_urls(clean_url)

    def get_chapter_urls_with_metadata(self, toc_url: str) -> Tuple[List[str], Dict[str, Any]]:
        """
        Get chapter URLs plus extraction metadata (confidence, pagination, completeness).

        This is intended for diagnostics and UIs that want a failsafe signal to decide
        whether the returned list is likely complete.
        """
        clean_url = self._validate_url(toc_url)
        scraper = self._get_scraper_for_url(clean_url)
        return scraper.get_chapter_urls_with_metadata(clean_url)

    def scrape_chapter(self, chapter_url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Scrape a single chapter URL."""
        clean_url = self._validate_url(chapter_url)
        scraper = self._get_scraper_for_url(clean_url)
        return scraper.scrape_chapter(clean_url)

    def filter_chapter_urls(self, chapter_urls: List[str], selection: Dict) -> List[str]:
        """Filter chapter URLs based on selection criteria."""
        selection_type = selection.get("type")

        if selection_type == "all":
            return chapter_urls
        if selection_type == "range":
            start_raw = selection.get("from", selection.get("start", 1))
            end_raw = selection.get("to", selection.get("end", len(chapter_urls)))
            start = int(start_raw) - 1 if start_raw else 0
            end = int(end_raw) if end_raw else len(chapter_urls)
            return chapter_urls[start:end]
        if selection_type in ("specific", "list"):
            indices = selection.get("chapters", selection.get("indices", []))
            return [chapter_urls[i - 1] for i in indices if 1 <= i <= len(chapter_urls)]

        return chapter_urls

    def _get_scraper_for_url(self, url: str) -> NovelScraper:
        """Get or create a cached scraper for the URL's base domain."""
        base_url = self._extract_base_url(url)
        scraper = self._scraper_cache.get(base_url)
        if not scraper:
            scraper = NovelScraper(base_url=base_url)
            self._scraper_cache[base_url] = scraper
            logger.info(f"Initialized scraper for base URL: {base_url}")
        return scraper

    @staticmethod
    def _extract_base_url(url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    @staticmethod
    def _validate_url(url: str) -> str:
        is_valid, clean_or_err = validate_url(url)
        if not is_valid:
            raise ValueError(f"Invalid URL: {clean_or_err}")
        return clean_or_err


__all__ = ["ScrapeService"]
