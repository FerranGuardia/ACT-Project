"""
Pagination Detector - Detects and analyzes pagination patterns on web pages.

Provides clean pagination detection logic with structured results
and fallback pattern recognition.
"""

import re
from typing import Any, List, Optional, Set, Dict
from dataclasses import dataclass

from core.logger import get_logger

from ..chapter_parser import normalize_url
from .url_extractor_validators import is_chapter_url

logger = get_logger("scraper.extractors.pagination_detector")


@dataclass
class PaginationInfo:
    """Structured information about detected pagination."""
    page_urls: List[str]
    pattern: str
    max_pages: int
    confidence: float  # 0.0 to 1.0

    def __bool__(self) -> bool:
        """Allow truthiness check."""
        return len(self.page_urls) > 0


class PaginationDetector:
    """
    Detects and analyzes pagination patterns on web pages.

    Provides structured pagination detection with multiple strategies
    and confidence scoring.
    """

    def __init__(self, max_pages: int = 200):
        """
        Initialize the pagination detector.

        Args:
            max_pages: Maximum number of pages to consider
        """
        self.max_pages = max_pages

    def detect(self, page: Any, toc_url: str) -> Optional[PaginationInfo]:
        """
        Detect pagination on the given page.

        Args:
            page: Playwright page object
            toc_url: Table of contents URL

        Returns:
            PaginationInfo if pagination detected, None otherwise
        """
        logger.debug("Detecting pagination patterns...")

        # Strategy 1: Direct pagination link detection
        pagination_links = self._find_pagination_links(page, toc_url)
        if pagination_links:
            page_urls = self._extract_page_urls_from_links(pagination_links, toc_url)
            if page_urls:
                return PaginationInfo(
                    page_urls=page_urls,
                    pattern="direct_links",
                    max_pages=self.max_pages,
                    confidence=0.9
                )

        # Strategy 2: URL pattern construction from numbers
        pattern_urls = self._detect_pagination_by_number_patterns(page, toc_url)
        if pattern_urls:
            return PaginationInfo(
                page_urls=pattern_urls,
                pattern="number_patterns",
                max_pages=self.max_pages,
                confidence=0.7
            )

        # Strategy 3: Fallback URL construction
        fallback_urls = self._construct_fallback_pagination(page, toc_url)
        if fallback_urls:
            return PaginationInfo(
                page_urls=fallback_urls,
                pattern="fallback_construction",
                max_pages=self.max_pages,
                confidence=0.5
            )

        logger.debug("No pagination detected")
        return None

    def _find_pagination_links(self, page: Any, toc_url: str) -> List[Any]:
        """
        Find pagination-related links on the page.

        Args:
            page: Playwright page object
            toc_url: Base TOC URL

        Returns:
            List of pagination link elements
        """
        pagination_selectors = [
            'a[href*="page"]', 'a[href*="?p="]', 'a[href*="&p="]',
            'a[href*="?page="]', 'a[href*="&page="]',
            '.pagination a', '.page-numbers a', '.pager a',
            '.pagination-wrapper a', '[class*="pagination"] a',
            '[class*="pager"] a', '[class*="page"] a',
            'a[href*="/page/"]', 'a[href*="/p/"]',
            'button[data-page]', 'a[data-page]', '[data-page]',
            'a:has-text("2")', 'a:has-text("3")',
        ]

        pagination_links: List[Any] = []

        for selector in pagination_selectors:
            try:
                found = page.query_selector_all(selector)
                if found:
                    pagination_links.extend(found)
                    logger.debug(f"Found {len(found)} pagination links using: {selector}")
            except Exception:
                continue

        return pagination_links

    def _extract_page_urls_from_links(self, pagination_links: List[Any], toc_url: str) -> List[str]:
        """
        Extract page URLs from pagination link elements.

        Args:
            pagination_links: List of pagination link elements
            toc_url: Base TOC URL

        Returns:
            List of unique page URLs to visit
        """
        seen_page_urls: Set[str] = set()
        base_toc = toc_url.split('?')[0].split('#')[0]

        for link in pagination_links:
            href = self._extract_link_href(link)
            if not href:
                continue

            full_page_url = normalize_url(href, toc_url)

            # Skip if it's a chapter URL or already seen
            if is_chapter_url(full_page_url, "") or full_page_url in seen_page_urls:
                continue

            url_lower = full_page_url.lower()
            is_pagination_url = (
                '?page=' in url_lower or '&page=' in url_lower or
                '/page/' in url_lower or '/p/' in url_lower or
                bool(re.search(r'[?&]p=\d+', url_lower)) or
                (bool(re.search(r'/\d+$', url_lower)) and not is_chapter_url(full_page_url, ""))
            )

            if is_pagination_url and full_page_url != toc_url:
                seen_page_urls.add(full_page_url)

        # Sort by page number
        page_urls = list(seen_page_urls)
        page_urls.sort(key=self._extract_page_number)

        return page_urls

    def _detect_pagination_by_number_patterns(self, page: Any, toc_url: str) -> List[str]:
        """
        Detect pagination by looking for links with numbers.

        Args:
            page: Playwright page object
            toc_url: Base TOC URL

        Returns:
            List of constructed page URLs
        """
        try:
            all_links = page.query_selector_all('a[href]')
            base_path = toc_url.rstrip('/')
            if re.search(r'/\d+$', base_path):
                base_path = re.sub(r'/\d+$', '', base_path)

            extracted_page_nums: Set[int] = set()

            for link in all_links:
                href = self._extract_link_href(link)
                text = self._extract_link_text(link)

                if not href:
                    continue

                normalized_href = normalize_url(href, toc_url)

                # Check if link text is a number
                if text and text.isdigit() and 1 <= int(text) <= 999:
                    if self._is_pagination_like_url(normalized_href, base_path):
                        extracted_page_nums.add(int(text))

                # Check URL patterns
                if re.search(r'/\d+$', normalized_href):
                    href_base = re.sub(r'/\d+$', '', normalized_href.rstrip('/'))
                    if href_base.lower() == base_path.lower():
                        page_match = re.search(r'/(\d+)$', normalized_href)
                        if page_match:
                            page_num = int(page_match.group(1))
                            if 1 <= page_num <= 999:
                                extracted_page_nums.add(page_num)

            if extracted_page_nums:
                return self._construct_urls_from_page_numbers(extracted_page_nums, base_path, toc_url)

        except Exception as e:
            logger.debug(f"Error in number pattern detection: {e}")

        return []

    def _construct_fallback_pagination(self, page: Any, toc_url: str) -> List[str]:
        """
        Construct pagination URLs using common patterns.

        Args:
            page: Playwright page object
            toc_url: Base TOC URL

        Returns:
            List of constructed page URLs
        """
        try:
            # Check if we have reasonable chapter count for pagination
            chapter_count = self._count_chapters_on_page(page)
            if not (30 <= chapter_count <= 60):
                return []

            logger.info(f"Found {chapter_count} chapters, checking for pagination patterns...")

            base_path = toc_url.rstrip('/')
            if base_path.endswith('/1') or base_path.endswith('/0'):
                base_path = base_path[:-2]

            pagination_patterns = [
                f"{base_path}/{{}}", f"{toc_url}/{{}}", f"{toc_url}?page={{}}",
                f"{toc_url}?p={{}}", f"{toc_url}/page/{{}}", f"{toc_url}/p/{{}}",
                f"{toc_url}?page={{}}&", f"{toc_url}&page={{}}",
            ]

            # Try patterns to see if they work
            for pattern in pagination_patterns:
                try:
                    test_url = pattern.format(2)  # Keep .format() for dynamic pattern strings
                    if self._test_pagination_pattern(page, test_url, toc_url):
                        # Pattern works, construct URLs
                        estimated_pages = min(max(10, 50), self.max_pages)  # Estimate based on chapters
                        return [pattern.format(page_num) for page_num in range(2, estimated_pages + 1)]
                except Exception:
                    continue

        except Exception as e:
            logger.debug(f"Error in fallback pagination construction: {e}")

        return []

    def _count_chapters_on_page(self, page: Any) -> int:
        """Count chapter links on the current page."""
        try:
            links = page.query_selector_all('a[href]')
            chapter_count = 0

            for link in links:
                href = self._extract_link_href(link)
                text = self._extract_link_text(link)

                if href and is_chapter_url(normalize_url(href, ""), text):
                    chapter_count += 1

            return chapter_count
        except Exception:
            return 0

    def _test_pagination_pattern(self, page: Any, test_url: str, original_url: str) -> bool:
        """Test if a pagination pattern works by trying to load page 2."""
        try:
            response = page.goto(test_url, wait_until="domcontentloaded", timeout=10000)
            if response and response.status == 200:
                # Check if this page has different chapters than the original
                original_chapters = set()
                current_chapters = set()

                # Get chapters from current page (page 2)
                links = page.query_selector_all('a[href]')
                for link in links:
                    href = self._extract_link_href(link)
                    text = self._extract_link_text(link)
                    if href and is_chapter_url(normalize_url(href, ""), text):
                        current_chapters.add(href)

                # Go back to original page
                page.goto(original_url, wait_until="domcontentloaded", timeout=10000)

                # Get chapters from original page
                links = page.query_selector_all('a[href]')
                for link in links:
                    href = self._extract_link_href(link)
                    text = self._extract_link_text(link)
                    if href and is_chapter_url(normalize_url(href, ""), text):
                        original_chapters.add(href)

                # Pattern works if we have different chapters
                return len(current_chapters) > 0 and current_chapters != original_chapters

        except Exception as e:
            logger.debug(f"Pattern test failed for {test_url}: {e}")
            return False

    def _construct_urls_from_page_numbers(self, page_nums: Set[int], base_path: str, toc_url: str) -> List[str]:
        """Construct URLs from extracted page numbers."""
        sorted_pages = sorted(page_nums)
        constructed_urls: List[str] = []

        # Try different patterns
        patterns = [
            f"{base_path}/{{}}",
            f"{toc_url}?page={{}}",
            f"{toc_url}?p={{}}",
            f"{toc_url}/page/{{}}",
        ]

        for pattern in patterns:
            test_urls = [pattern.format(page_num) for page_num in sorted_pages[:3]]
            if all(url != toc_url for url in test_urls):
                constructed_urls.extend([pattern.format(page_num) for page_num in sorted_pages])
                break

        return constructed_urls

    def _extract_link_href(self, link: Any) -> Optional[str]:
        """Extract href attribute from a link element."""
        try:
            href_raw = link.get_attribute("href")
            return str(href_raw) if href_raw else None
        except Exception:
            return None

    def _extract_link_text(self, link: Any) -> Optional[str]:
        """Extract text content from a link element."""
        try:
            text_raw = link.inner_text()
            return str(text_raw).strip() if text_raw else None
        except Exception:
            return None

    def _is_pagination_like_url(self, url: str, base_path: str) -> bool:
        """Check if URL looks like a pagination URL."""
        url_lower = url.lower()
        return ('page' in url_lower or 'p=' in url_lower or
                bool(re.search(r'/\d+$', url_lower)))

    def _extract_page_number(self, url: str) -> int:
        """Extract page number from URL for sorting."""
        match = re.search(r'/(\d+)$|[/?&]page[=_](\d+)|/page[/-](\d+)|/p[/-](\d+)|page(\d+)', url.lower())
        if match:
            return int(match.group(1) or match.group(2) or match.group(3) or match.group(4) or match.group(5))
        return 0


__all__ = ["PaginationDetector", "PaginationInfo"]