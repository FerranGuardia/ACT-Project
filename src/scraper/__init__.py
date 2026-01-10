"""
Scraper module - Content extraction from web sources.
"""

from .novel_scraper import NovelScraper
from .base import BaseScraper

# Backwards compatibility aliases
GenericScraper = NovelScraper  # Deprecated: use NovelScraper

__all__ = [
    "NovelScraper",
    "BaseScraper",
    # Backwards compatibility
    "GenericScraper",
]
