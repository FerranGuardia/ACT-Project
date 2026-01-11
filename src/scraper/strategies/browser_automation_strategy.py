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
                    viewport={'width': 1280, 'height': 720},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                )

                page = await context.new_page()

                try:
                    # Set up request interception for API monitoring
                    api_urls = []
                    def handle_request(request):
                        if any(keyword in request.url.lower() for keyword in ['chapter', 'api', 'ajax']):
                            api_urls.append(request.url)

                    page.on('request', handle_request)

                    # Navigate to the page
                    await page.goto(toc_url, wait_until='networkidle')

                    # Wait for dynamic content to load
                    await page.wait_for_timeout(2000)

                    # Try to trigger lazy loading by scrolling
                    await self._scroll_and_wait(page, should_stop)

                    # Extract URLs using multiple methods
                    urls = []

                    # Method 1: Extract from page content
                    content_urls = await self._extract_from_page_content(page)
                    urls.extend(content_urls)

                    # Method 2: Try common selectors for chapter lists
                    selector_urls = await self._extract_with_selectors(page)
                    urls.extend(selector_urls)

                    # Method 3: Monitor and try API endpoints found
                    api_extracted_urls = await self._try_api_endpoints(page, api_urls)
                    urls.extend(api_extracted_urls)

                    # Method 4: JavaScript execution to extract from variables
                    js_urls = await self._extract_via_javascript(page)
                    urls.extend(js_urls)

                    # Remove duplicates
                    urls = self._deduplicate_urls(urls)

                    # Filter by chapter range if specified
                    if min_chapter or max_chapter:
                        urls = self._filter_by_chapter_range(urls, min_chapter, max_chapter)

                    return urls

                finally:
                    await page.close()
                    await context.close()
                    await browser.close()

        except Exception as e:
            logger.debug(f"Browser automation failed: {e}")
            return []

    async def _scroll_and_wait(self, page, should_stop: Optional[Callable[[], bool]]):
        """Scroll the page to trigger lazy loading."""
        try:
            # Scroll down in increments to trigger lazy loading
            scroll_increment = 500
            max_scrolls = 20  # Limit to prevent infinite scrolling

            for i in range(max_scrolls):
                if should_stop and should_stop():
                    break

                # Scroll down
                await page.evaluate(f"window.scrollBy(0, {scroll_increment})")

                # Wait for content to load
                await page.wait_for_timeout(500)

                # Check if we reached the bottom
                at_bottom = await page.evaluate("""
                    window.innerHeight + window.scrollY >= document.body.offsetHeight - 100
                """)

                if at_bottom:
                    break

            # Scroll back to top for extraction
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(500)

        except Exception as e:
            logger.debug(f"Scrolling failed: {e}")

    async def _extract_from_page_content(self, page) -> List[str]:
        """Extract chapter URLs from the rendered page content."""
        try:
            # Get all links that might be chapters
            links = await page.query_selector_all('a')

            urls = []
            for link in links:
                try:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()

                    if href and self._is_chapter_link(href, text.strip()):
                        full_url = self._normalize_url(href)
                        urls.append(full_url)

                except Exception:
                    continue

            return urls

        except Exception as e:
            logger.debug(f"Content extraction failed: {e}")
            return []

    async def _extract_with_selectors(self, page) -> List[str]:
        """Extract URLs using common CSS selectors."""
        selectors = [
            'a[href*="chapter"]',
            'a[href*="chap"]',
            'a[href*="ch-"]',
            '.chapter-list a',
            '.chapter-item a',
            '.toc a',
            '#toc a',
            'li a[href*="chapter"]',
            'td a[href*="chapter"]',
            '.chapter-link',
            '.chapter-title a',
        ]

        urls = []

        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)

                for element in elements:
                    try:
                        href = await element.get_attribute('href')
                        if href:
                            full_url = self._normalize_url(href)
                            urls.append(full_url)
                    except Exception:
                        continue

            except Exception:
                continue

        return urls

    async def _try_api_endpoints(self, page, api_urls: List[str]) -> List[str]:
        """Try to extract chapter URLs from discovered API endpoints."""
        urls = []

        for api_url in api_urls[:5]:  # Limit to first 5 to avoid too many requests
            try:
                # Navigate to the API URL
                await page.goto(api_url)

                # Try to parse JSON response
                content = await page.inner_text('pre, body')
                if content:
                    json_urls = self._parse_json_for_urls(content)
                    urls.extend(json_urls)

            except Exception:
                continue

        return urls

    async def _extract_via_javascript(self, page) -> List[str]:
        """Extract URLs by executing JavaScript on the page."""
        try:
            # JavaScript to extract chapter URLs from common patterns
            js_code = """
            (function() {
                var urls = [];

                // Try to extract from common JavaScript variables
                var variables = ['chapters', 'chapterList', 'chapterUrls', 'chapter_data'];
                for (var i = 0; i < variables.length; i++) {
                    try {
                        var data = window[variables[i]];
                        if (data && Array.isArray(data)) {
                            for (var j = 0; j < data.length; j++) {
                                var item = data[j];
                                if (item && typeof item === 'object') {
                                    var url = item.url || item.href || item.link || item.chapterUrl;
                                    if (url && typeof url === 'string' && url.includes('chapter')) {
                                        urls.push(url);
                                    }
                                }
                            }
                        }
                    } catch (e) {}
                }

                // Extract from all links that look like chapters
                var links = document.querySelectorAll('a[href*="chapter"], a[href*="chap"]');
                for (var i = 0; i < links.length; i++) {
                    var href = links[i].getAttribute('href');
                    if (href) {
                        urls.push(href);
                    }
                }

                return urls;
            })();
            """

            result = await page.evaluate(js_code)
            if result and isinstance(result, list):
                # Normalize URLs
                normalized_urls = []
                for url in result:
                    if isinstance(url, str):
                        full_url = self._normalize_url(url)
                        normalized_urls.append(full_url)

                return normalized_urls

        except Exception as e:
            logger.debug(f"JavaScript extraction failed: {e}")

        return []

    def _parse_json_for_urls(self, content: str) -> List[str]:
        """Parse JSON content for chapter URLs."""
        try:
            import json
            data = json.loads(content)

            urls = []

            def extract_urls(obj):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key.lower() in ['url', 'href', 'link', 'chapter_url'] and isinstance(value, str):
                            if 'chapter' in value.lower():
                                urls.append(value)
                        else:
                            extract_urls(value)
                elif isinstance(obj, list):
                    for item in obj:
                        extract_urls(item)

            extract_urls(data)
            return urls

        except (json.JSONDecodeError, ImportError):
            return []

    def _is_chapter_link(self, url: str, text: str) -> bool:
        """Check if a link is a chapter link."""
        import re

        url_lower = url.lower()
        text_lower = text.lower()

        # Text indicators
        text_indicators = ['chapter', 'chap', 'ch ', 'episode', 'ep ', '第', '章']
        has_text_indicator = any(indicator in text_lower for indicator in text_indicators)

        # URL indicators
        url_indicators = ['chapter', 'chap', 'ch-', 'ch_', 'episode', '/c/', '/chapter/']
        has_url_indicator = any(indicator in url_lower for indicator in url_indicators)

        # Must have numbers
        has_number = bool(re.search(r'\d+', url))

        return (has_text_indicator or has_url_indicator) and has_number

    def _normalize_url(self, url: str) -> str:
        """Normalize a URL to absolute form."""
        if not url:
            return url

        if url.startswith(('http://', 'https://')):
            return url
        else:
            from urllib.parse import urljoin
            return urljoin(self.base_url, url)

    def _deduplicate_urls(self, urls: List[str]) -> List[str]:
        """Remove duplicate URLs while preserving order."""
        seen = set()
        unique_urls = []

        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return unique_urls

    def _filter_by_chapter_range(
        self,
        urls: List[str],
        min_chapter: Optional[int],
        max_chapter: Optional[int]
    ) -> List[str]:
        """Filter URLs by chapter number range."""
        if not min_chapter and not max_chapter:
            return urls

        filtered_urls = []
        from ..chapter_parser import extract_chapter_number

        for url in urls:
            chapter_num = extract_chapter_number(url)
            if chapter_num:
                if min_chapter and chapter_num < min_chapter:
                    continue
                if max_chapter and chapter_num > max_chapter:
                    continue
                filtered_urls.append(url)

        return filtered_urls

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