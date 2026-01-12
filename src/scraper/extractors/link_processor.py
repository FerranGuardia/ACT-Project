"""
Link Processor - Handles link collection, validation, and deduplication.

Provides clean link processing functionality for chapter URL extraction,
with proper validation and normalization.
"""

from typing import List, Tuple, Set, Any

from core.logger import get_logger

from ..chapter_parser import normalize_url
from .url_extractor_validators import is_chapter_url

logger = get_logger("scraper.extractors.link_processor")


class LinkProcessor:
    """
    Processes and validates links from web pages.

    Handles link collection, normalization, validation, and deduplication
    for chapter URL extraction.
    """

    def __init__(self, base_url: str):
        """
        Initialize the link processor.

        Args:
            base_url: Base URL for link normalization
        """
        self.base_url = base_url

    def collect_links(self, page: Any) -> List[Tuple[str, str]]:
        """
        Collect all links from the current page.

        Args:
            page: Playwright page object

        Returns:
            List of (href, text) tuples
        """
        links: List[Tuple[str, str]] = []

        try:
            dom_links = page.query_selector_all("a[href]")
        except Exception as e:
            logger.debug(f"Error querying links: {e}")
            return links

        for link in dom_links:
            try:
                href_raw = link.get_attribute("href")
                href = str(href_raw) if href_raw else ""

                if not href:
                    continue

                text_raw = link.inner_text()
                text = (str(text_raw) if text_raw else "").strip()

                links.append((href, text))

            except Exception as e:
                # Skip individual link errors
                continue

        logger.debug(f"Collected {len(links)} links from page")
        return links

    def extract_chapter_urls(self, links: List[Tuple[str, str]]) -> List[str]:
        """
        Extract and validate chapter URLs from a list of links.

        Args:
            links: List of (href, text) tuples
            base_url: Base URL for normalization

        Returns:
            List of validated chapter URLs
        """
        chapter_urls: List[str] = []

        for href, text in links:
            try:
                full_url = normalize_url(href, self.base_url)

                if is_chapter_url(full_url, text):
                    chapter_urls.append(full_url)

            except Exception as e:
                logger.debug(f"Error processing link {href}: {e}")
                continue

        logger.debug(f"Extracted {len(chapter_urls)} chapter URLs from {len(links)} links")
        return chapter_urls

    def deduplicate_urls(self, urls: List[str]) -> List[str]:
        """
        Remove duplicate URLs while preserving order.

        Args:
            urls: List of URLs (may contain duplicates)

        Returns:
            List of unique URLs in original order
        """
        seen: Set[str] = set()
        unique_urls: List[str] = []

        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        if len(unique_urls) < len(urls):
            logger.debug(f"Removed {len(urls) - len(unique_urls)} duplicate URLs")

        return unique_urls

    def process_page_links(self, page: Any) -> List[str]:
        """
        Complete link processing pipeline for a page.

        Args:
            page: Playwright page object

        Returns:
            List of unique chapter URLs
        """
        # Collect all links
        links = self.collect_links(page)

        # Extract chapter URLs
        chapter_urls = self.extract_chapter_urls(links)

        # Remove duplicates
        unique_urls = self.deduplicate_urls(chapter_urls)

        logger.info(f"Processed page: {len(links)} total links -> {len(unique_urls)} chapter URLs")
        return unique_urls

    def validate_url_list(self, urls: List[str]) -> List[str]:
        """
        Validate a list of URLs, removing invalid ones.

        Args:
            urls: List of URLs to validate

        Returns:
            List of valid URLs
        """
        valid_urls: List[str] = []

        for url in urls:
            try:
                # Basic URL validation - should start with http/https
                if url.startswith(('http://', 'https://')):
                    valid_urls.append(url)
                else:
                    logger.debug(f"Skipping invalid URL: {url}")
            except Exception as e:
                logger.debug(f"Error validating URL {url}: {e}")
                continue

        if len(valid_urls) < len(urls):
            logger.debug(f"Filtered out {len(urls) - len(valid_urls)} invalid URLs")

        return valid_urls


__all__ = ["LinkProcessor"]