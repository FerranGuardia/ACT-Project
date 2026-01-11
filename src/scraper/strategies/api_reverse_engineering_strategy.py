"""
API Reverse Engineering Strategy.

Analyzes network requests and reverse-engineers API endpoints for modern
single-page applications (SPAs) and API-driven sites.
"""

import asyncio
import json
import time
from typing import List, Optional, Callable, Any, Tuple, Dict, Set
from urllib.parse import urlparse, parse_qs, urljoin

from core.logger import get_logger
from ..universal_url_detector import BaseDetectionStrategy, DetectionResult

logger = get_logger("scraper.strategies.api_reverse")


class ApiReverseEngineeringStrategy(BaseDetectionStrategy):
    """Strategy that reverse-engineers API endpoints for modern web applications."""

    def __init__(self, base_url: str, session_manager):
        super().__init__("api_reverse", base_url, session_manager)
        self._playwright_available = self._check_playwright_available()

    async def detect(self, toc_url: str, should_stop: Optional[Callable[[], bool]] = None) -> DetectionResult:
        """Detect chapter URLs by reverse-engineering API endpoints."""
        start_time = time.time()

        if not self._playwright_available:
            return self._create_result(
                [],
                confidence=0.0,
                error="Playwright not available for API monitoring",
                response_time=time.time() - start_time,
            )

        try:
            urls = await self._reverse_engineer_apis(toc_url, should_stop)

            if not urls:
                return self._create_result(
                    [], confidence=0.0, error="No API endpoints or URLs found", response_time=time.time() - start_time
                )

            # Validate and normalize
            urls, validation_score = self._validate_urls(urls)

            # Analyze coverage
            coverage_range = self._analyze_coverage(urls)

            confidence = min(0.7 + (validation_score * 0.3), 1.0)

            return self._create_result(
                urls=urls,
                confidence=confidence,
                coverage_range=coverage_range,
                validation_score=validation_score,
                response_time=time.time() - start_time,
                metadata={"extraction_method": "api_reverse_engineering", "api_driven": True},
            )

        except Exception as e:
            logger.debug(f"API reverse engineering strategy failed: {e}")
            return self._create_result([], confidence=0.0, error=str(e), response_time=time.time() - start_time)

    def _check_playwright_available(self) -> bool:
        """Check if Playwright is available."""
        try:
            import playwright

            return True
        except ImportError:
            return False

    async def _reverse_engineer_apis(self, toc_url: str, should_stop: Optional[Callable[[], bool]]) -> List[str]:
        """Monitor network requests to reverse-engineer API endpoints."""
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                )

                page = await context.new_page()

                try:
                    # Monitor network requests
                    network_data = await self._monitor_network_requests(page, toc_url, should_stop)

                    # Analyze captured requests
                    api_endpoints = self._analyze_network_data(network_data)

                    # Try to fetch chapter data from discovered endpoints
                    urls = []
                    for endpoint in api_endpoints[:10]:  # Limit to prevent too many requests
                        if should_stop and should_stop():
                            break

                        endpoint_urls = await self._fetch_from_endpoint(page, endpoint)
                        urls.extend(endpoint_urls)

                    # Also extract any chapter URLs found directly in responses
                    for response_data in network_data["responses"]:
                        if response_data.get("content_type", "").startswith("application/json"):
                            try:
                                data = json.loads(response_data["body"])
                                response_urls = self._extract_urls_from_api_response(data)
                                urls.extend(response_urls)
                            except (json.JSONDecodeError, KeyError):
                                continue

                    return self._deduplicate_urls(urls)

                finally:
                    await page.close()
                    await context.close()
                    await browser.close()

        except Exception as e:
            logger.debug(f"API monitoring failed: {e}")
            return []

    async def _monitor_network_requests(
        self, page, toc_url: str, should_stop: Optional[Callable[[], bool]]
    ) -> Dict[str, Any]:
        """Monitor network requests and responses."""
        network_data = {"requests": [], "responses": [], "api_candidates": []}

        def handle_request(request):
            request_info = {
                "url": request.url,
                "method": request.method,
                "headers": dict(request.headers),
                "timestamp": time.time(),
            }
            network_data["requests"].append(request_info)

            # Identify potential API endpoints
            if self._is_api_candidate(request.url):
                network_data["api_candidates"].append(request.url)

        def handle_response(response):
            # Only capture responses that might contain chapter data
            if self._should_capture_response(response):
                try:
                    # Get response body (this might fail for large responses)
                    body = response.text() if hasattr(response, "text") else ""
                    response_info = {
                        "url": response.url,
                        "status": response.status,
                        "headers": dict(response.headers),
                        "content_type": response.headers.get("content-type", ""),
                        "body": body[:50000],  # Limit size
                        "timestamp": time.time(),
                    }
                    network_data["responses"].append(response_info)
                except Exception:
                    pass

        # Set up event handlers
        page.on("request", handle_request)
        page.on("response", handle_response)

        # Navigate and interact with the page
        await page.goto(toc_url, wait_until="networkidle")

        # Wait for dynamic content and scroll to trigger API calls
        await page.wait_for_timeout(2000)

        # Scroll to trigger lazy loading
        await self._trigger_lazy_loading(page, should_stop)

        # Wait a bit more for any delayed API calls
        await page.wait_for_timeout(3000)

        return network_data

    async def _trigger_lazy_loading(self, page, should_stop: Optional[Callable[[], bool]]):
        """Trigger lazy loading by scrolling and interacting."""
        try:
            # Scroll down to trigger lazy loading
            for i in range(5):
                if should_stop and should_stop():
                    break

                await page.evaluate("window.scrollBy(0, 800)")
                await page.wait_for_timeout(1000)

            # Try clicking "load more" buttons
            load_more_selectors = [
                'button:has-text("Load More")',
                'button:has-text("Show More")',
                'a:has-text("Next")',
                ".load-more",
                "#load-more",
                '[data-action="load-more"]',
            ]

            for selector in load_more_selectors:
                try:
                    button = await page.query_selector(selector)
                    if button:
                        await button.click()
                        await page.wait_for_timeout(2000)
                        break
                except Exception:
                    continue

        except Exception as e:
            logger.debug(f"Lazy loading trigger failed: {e}")

    def _is_api_candidate(self, url: str) -> bool:
        """Check if a URL is a potential API endpoint."""
        url_lower = url.lower()
        parsed = urlparse(url)

        # API-like patterns
        api_indicators = ["/api/", "/ajax/", "/graphql", "/rest/", "chapters", "chapter-list", "novel-chapters"]

        has_api_indicator = any(indicator in url_lower for indicator in api_indicators)

        # JSON-like query parameters
        query_params = parse_qs(parsed.query)
        has_json_params = any(key in ["json", "format", "type"] for key in query_params)

        # RESTful patterns
        path_parts = parsed.path.strip("/").split("/")
        has_rest_pattern = len(path_parts) >= 2 and any(part.isdigit() for part in path_parts)

        return has_api_indicator or has_json_params or has_rest_pattern

    def _should_capture_response(self, response) -> bool:
        """Determine if we should capture this response."""
        try:
            url = response.url.lower()
            content_type = response.headers.get("content-type", "").lower()

            # Capture JSON responses from API-like URLs
            if "json" in content_type and any(keyword in url for keyword in ["api", "ajax", "chapter"]):
                return True

            # Capture responses from known API endpoints
            if any(keyword in url for keyword in ["/api/", "/ajax/", "/chapters"]):
                return True

            return False

        except Exception:
            return False

    def _analyze_network_data(self, network_data: Dict[str, Any]) -> List[str]:
        """Analyze network data to identify chapter API endpoints."""
        endpoints = []

        # Extract unique API candidate URLs
        seen_urls = set()
        for url in network_data["api_candidates"]:
            if url not in seen_urls:
                seen_urls.add(url)
                endpoints.append(url)

        # Also check successful API responses
        for response in network_data["responses"]:
            if response.get("status") == 200:
                url = response["url"]
                if url not in seen_urls and self._is_api_candidate(url):
                    seen_urls.add(url)
                    endpoints.append(url)

        # Generate pagination variations
        paginated_endpoints = []
        for endpoint in endpoints:
            paginated_endpoints.extend(self._generate_pagination_endpoints(endpoint))

        return endpoints + paginated_endpoints

    def _generate_pagination_endpoints(self, base_url: str) -> List[str]:
        """Generate pagination variations of an API endpoint."""
        endpoints = []
        parsed = urlparse(base_url)
        query_params = parse_qs(parsed.query)

        # Common pagination patterns
        pagination_patterns = [
            ("page", "1"),
            ("offset", "0"),
            ("start", "0"),
            ("limit", "50"),
            ("p", "1"),
            ("skip", "0"),
        ]

        for param_name, param_value in pagination_patterns:
            if param_name not in query_params:
                new_query = query_params.copy()
                new_query[param_name] = [param_value]

                # Rebuild query string
                query_string = "&".join([f"{k}={v[0]}" for k, v in new_query.items()])
                new_url = parsed._replace(query=query_string).geturl()

                endpoints.append(new_url)

        return endpoints

    async def _fetch_from_endpoint(self, page, endpoint: str) -> List[str]:
        """Fetch and extract chapter URLs from an API endpoint."""
        try:
            # Navigate to the endpoint
            await page.goto(endpoint)

            # Try to get the response content
            content_element = await page.query_selector("pre, body")
            if content_element:
                content = await content_element.inner_text()
                if content:
                    return self._extract_urls_from_api_response_text(content)

        except Exception as e:
            logger.debug(f"Failed to fetch from endpoint {endpoint}: {e}")

        return []

    def _extract_urls_from_api_response_text(self, content: str) -> List[str]:
        """Extract chapter URLs from API response text."""
        urls = []

        try:
            # Try to parse as JSON
            data = json.loads(content)
            urls.extend(self._extract_urls_from_api_response(data))

        except (json.JSONDecodeError, ValueError):
            # Try to extract URLs using regex patterns
            import re

            # Look for URL patterns in the text
            url_patterns = [
                r'"url"\s*:\s*"([^"]*chapter[^"]*)"',
                r'"href"\s*:\s*"([^"]*chapter[^"]*)"',
                r'"link"\s*:\s*"([^"]*chapter[^"]*)"',
                r'"chapterUrl"\s*:\s*"([^"]*chapter[^"]*)"',
            ]

            for pattern in url_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                urls.extend(matches)

        return urls

    def _extract_urls_from_api_response(self, data: Any) -> List[str]:
        """Recursively extract chapter URLs from API response data."""
        urls = []

        def extract_from_obj(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key.lower() in ["url", "href", "link", "chapter_url", "chapterUrl"]:
                        if isinstance(value, str) and "chapter" in value.lower():
                            urls.append(value)
                    else:
                        extract_from_obj(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_from_obj(item)

        extract_from_obj(data)
        return urls

    def _deduplicate_urls(self, urls: List[str]) -> List[str]:
        """Remove duplicate URLs while preserving order."""
        seen = set()
        unique_urls = []

        for url in urls:
            if url and url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return unique_urls

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
