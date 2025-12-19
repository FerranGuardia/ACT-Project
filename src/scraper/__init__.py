"""
Scraper module - Content extraction from web sources.
"""

from .novel_scraper import NovelScraper
from .base import BaseScraper

# Backwards compatibility aliases
GenericScraper = NovelScraper  # Deprecated: use NovelScraper
ChapterUrlFetcher = None  # Moved to extractors.url_extractor.UrlExtractor
ContentScraper = None  # Moved to extractors.chapter_extractor.ChapterExtractor

__all__ = [
    "NovelScraper",
    "BaseScraper",
    # Backwards compatibility
    "GenericScraper",
]


