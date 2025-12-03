"""
Scraper module - Content extraction from web sources.
"""

from .generic_scraper import GenericScraper
from .base_scraper import BaseScraper
from .url_fetcher import ChapterUrlFetcher
from .content_scraper import ContentScraper

__all__ = [
    "GenericScraper",
    "BaseScraper",
    "ChapterUrlFetcher",
    "ContentScraper",
]


