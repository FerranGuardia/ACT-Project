"""
Browser Automation Strategy.

Uses Playwright to handle complex rendering, lazy-loading, and dynamic content.
This is the most comprehensive but slowest method.
"""

import asyncio
import time
from typing import List, Optional, Callable, Any, Tuple

from core.logger import get_logger
from ..universal_url_detector import BaseDetectionStrategy, DetectionResult

logger = get_logger("scraper.strategies.browser")


class BrowserAutomationStrategy(BaseDetectionStrategy):
    """Strategy that uses browser automation for comprehensive URL detection."""

    def __init__(self, base_url: str, session_manager):
        super().__init__("browser_automation", base_url, session_manager)
        self._playwright_available = self._check_playwright_available()

    async def detect(
        self,
        toc_url: str,
        should_stop: Optional[Callable[[], bool]] = None,
        min_chapter: Optional[int] = None,
        max_chapter: Optional[int] = None
    ) -> DetectionResult:
        """Detect chapter URLs using browser automation."""
        start_time = time.time()

        if not self._playwright_available:
            return self._create_result(
                [],
                confidence=0.0,
                error="Playwright not available",
                response_time=time.time() - start_time
            )

        try:
            urls = await self._run_browser_automation(toc_url, should_stop, min_chapter, max_chapter)

            if not urls:
                return self._create_result(
                    [],
                    confidence=0.0,
                    error="No URLs found via browser automation",
                    response_time=time.time() - start_time
                )

            # Validate and normalize
            urls, validation_score = self._validate_urls(urls)

            # Analyze coverage
            coverage_range = self._analyze_coverage(urls)

            confidence = min(0.8 + (validation_score * 0.2), 1.0)  # High base confidence for browser method

            return self._create_result(
                urls=urls,
                confidence=confidence,
                coverage_range=coverage_range,
                validation_score=validation_score,
                response_time=time.time() - start_time,
                metadata={
                    "extraction_method": "browser_automation",
                    "playwright_used": True
                }
            )

        except Exception as e:
            logger.debug(f"Browser automation strategy failed: {e}")
            return self._create_result(
                [],
                confidence=0.0,
                error=str(e),
                response_time=time.time() - start_time
            )

    def _check_playwright_available(self) -> bool:
        """Check if Playwright is available."""
        try:
            import playwright
            return True
        except ImportError:
            return False

    async def _run_browser_automation(
        self,
        toc_url: str,
        should_stop: Optional[Callable[[], bool]],
        min_chapter: Optional[int],
        max_chapter: Optional[int]
    ) -> List[str]:
        """Run browser automation to extract chapter URLs."""
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = await context.new_page()

                try:
                    # Navigate to the page
                    await page.goto(toc_url, wait_until="networkidle", timeout=30000)

                    # Try to trigger lazy loading by scrolling
                    await self._scroll_to_load_content(page)

                    # Extract URLs from the main content
                    urls = await self._extract_from_page_content(page)

                    # Handle pagination if present
                    paginated_urls = await self._handle_pagination(page, should_stop)
                    urls.extend(paginated_urls)

                    return urls

                finally:
                    await browser.close()

        except Exception as e:
            logger.debug(f"Browser automation failed: {e}")
            return []

    async def _scroll_to_load_content(self, page) -> None:
        """Scroll to trigger lazy loading."""
        try:
            # Scroll down in increments to trigger lazy loading
            for _ in range(5):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(0.5)
        except Exception:
            pass  # Ignore scrolling errors

    async def _extract_from_page_content(self, page) -> List[str]:
        """Extract chapter URLs from the current page content."""
        urls = []

        # For NovelFull, we need to be more selective to avoid duplicates
        if "novelfull.net" in self.base_url:
            urls = await self._extract_novelfull_chapters(page)
        else:
            # Original logic for other sites
            selectors = [
                'ul.list-chapter li a[href*="chapter-"]',
                '.chapter-list a[href*="chapter-"]',
                '.chapters a[href*="chapter-"]',
                'a[href*="chapter-"]',
            ]

            for selector in selectors:
                try:
                    links = await page.query_selector_all(selector)
                    for link in links:
                        href = await link.get_attribute('href')
                        if href and self._is_chapter_url(href):
                            if not href.startswith('http'):
                                href = f"https://{self.domain}{href}"
                            urls.append(href)
                except Exception:
                    continue

        return urls

    async def _extract_novelfull_chapters(self, page) -> List[str]:
        """Extract chapters from NovelFull pages."""
        urls = []

        try:
            # Use the standard ul.list-chapter selector for NovelFull
            chapter_links = await page.query_selector_all('ul.list-chapter li a[href*="chapter-"]')

            for link in chapter_links:
                href = await link.get_attribute('href')
                if href and self._is_chapter_url(href):
                    if not href.startswith('http'):
                        href = f"https://novelfull.net{href}"
                    urls.append(href)

        except Exception as e:
            # Fallback to basic extraction
            try:
                basic_links = await page.query_selector_all('a[href*="chapter-"]')
                for link in basic_links:
                    href = await link.get_attribute('href')
                    if href and self._is_chapter_url(href):
                        if not href.startswith('http'):
                            href = f"https://novelfull.net{href}"
                        urls.append(href)
            except Exception:
                pass

        return urls

    def _is_chapter_url(self, url: str) -> bool:
        """Check if URL looks like a chapter URL."""
        return 'chapter-' in url and url.endswith('.html')

    def _analyze_coverage(self, urls: List[str]) -> Optional[Tuple[int, int]]:
        """Analyze chapter number coverage."""
        from ..chapter_parser import extract_chapter_number

        chapter_nums = []
        for url in urls:
            num = extract_chapter_number(url)
            if num:
                chapter_nums.append(num)

        if not chapter_nums:
            return None

        return (min(chapter_nums), max(chapter_nums))

    def _validate_urls(self, urls: List[str]) -> Tuple[List[str], float]:
        """Validate URLs and return filtered list with average confidence."""
        if not urls:
            return [], 0.0

        valid_urls = []
        total_confidence = 0.0

        for url in urls:
            if self._is_chapter_url(url):
                valid_urls.append(url)
                total_confidence += 0.9  # High confidence for browser-extracted URLs

        avg_confidence = total_confidence / len(valid_urls) if valid_urls else 0.0
        return valid_urls, avg_confidence

    async def _handle_pagination(self, page, should_stop: Optional[Callable[[], bool]]) -> List[str]:
        """Handle traditional pagination by following page links."""
        try:
            urls = []

            # Extract from current page first
            current_urls = await self._extract_from_page_content(page)
            urls.extend(current_urls)

            # For NovelFull and similar sites, implement systematic pagination
            if "novelfull.net" in self.base_url:
                novel_urls = await self._handle_novelfull_pagination(page, should_stop)
                urls.extend(novel_urls)
            else:
                # Original pagination logic for other sites
                legacy_urls = await self._handle_legacy_pagination(page, should_stop)
                urls.extend(legacy_urls)

            return urls

        except Exception as e:
            logger.debug(f"Pagination handling failed: {e}")
            return urls

    async def _handle_novelfull_pagination(self, page, should_stop: Optional[Callable[[], bool]]) -> List[str]:
        """Handle NovelFull-style pagination systematically."""
        urls = []
        seen_urls = set()  # Track URLs we've already seen to avoid duplicates

        base_url = page.url
        # Remove query parameters to get base URL
        base_url = base_url.split('?')[0]

        page_num = 2  # Start from page 2 since we already did page 1

        while True:
            if should_stop and should_stop():
                break

            try:
                # Construct next page URL
                next_page_url = f"{base_url}?page={page_num}"

                # Navigate to next page
                await page.goto(next_page_url, wait_until="networkidle", timeout=10000)

                # Check if page loaded and has content
                content_check = await page.query_selector('ul.list-chapter')
                if not content_check:
                    break

                # Extract URLs from this page
                page_urls = await self._extract_from_page_content(page)

                if not page_urls:
                    break

                # Add new URLs (avoid duplicates)
                new_urls = 0
                for url in page_urls:
                    if url not in seen_urls:
                        seen_urls.add(url)
                        urls.append(url)
                        new_urls += 1

                # If we didn't get any new URLs from this page, we've likely reached the end
                if new_urls == 0:
                    break

                page_num += 1

                # Safety check: don't go beyond reasonable page count
                if page_num > 50:  # Reasonable maximum
                    break

            except Exception as e:
                break

        return urls

    async def _handle_legacy_pagination(self, page, should_stop: Optional[Callable[[], bool]]) -> List[str]:
        """Handle traditional pagination by following page links."""
        urls = []

        # Check for pagination links
        pagination_selectors = [
            'a[href*="page="]',  # Common pagination pattern
            '.pagination a',     # Bootstrap-style pagination
            'ul.pagination a',   # Bootstrap pagination
            'nav.pagination a',  # Modern pagination
            '.pager a',          # Alternative pagination
            '.page-links a',     # WordPress pagination
            'a.next',            # Next button
            'a[rel="next"]',     # Next link
        ]

        page_links = []
        for selector in pagination_selectors:
            try:
                links = await page.query_selector_all(selector)
                for link in links:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()
                    if href and text.strip():
                        page_links.append((href, text.strip()))
            except Exception:
                continue

        # Remove duplicates
        seen_hrefs = set()
        unique_page_links = []
        for href, text in page_links:
            if href not in seen_hrefs:
                seen_hrefs.add(href)
                unique_page_links.append((href, text))

        # Visit each pagination page
        for href, text in unique_page_links:
            if should_stop and should_stop():
                break

            try:
                # Navigate to the page
                await page.goto(href, wait_until="networkidle", timeout=10000)

                # Extract URLs from this page
                page_urls = await self._extract_from_page_content(page)
                urls.extend(page_urls)

            except Exception as e:
                continue

        return urls