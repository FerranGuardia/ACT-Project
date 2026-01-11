"""
AJAX Endpoint Discovery Strategy.

Discovers and queries AJAX endpoints that provide chapter lists.
Handles lazy-loading and paginated content via API calls.
"""

import json
import re
import time
from typing import List, Optional, Callable, Any, Dict, Tuple
from urllib.parse import urljoin, urlparse, parse_qs

from core.logger import get_logger
from ..universal_url_detector import BaseDetectionStrategy, DetectionResult

logger = get_logger("scraper.strategies.ajax")


class AjaxStrategy(BaseDetectionStrategy):
    """Strategy that discovers and queries AJAX endpoints for chapter data."""

    def __init__(self, base_url: str, session_manager):
        super().__init__("ajax", base_url, session_manager)

    async def detect(self, toc_url: str, should_stop: Optional[Callable[[], bool]] = None) -> DetectionResult:
        """Detect chapter URLs via AJAX endpoints."""
        start_time = time.time()

        try:
            # First, fetch the TOC page to discover endpoints
            response = self._fetch_with_retry(toc_url)
            if not response:
                return self._create_result(
                    [], confidence=0.0, error="Failed to fetch page", response_time=time.time() - start_time
                )

            html = response.text

            # Extract novel ID if available
            novel_id = self._extract_novel_id(html)

            # Discover potential AJAX endpoints
            endpoints = self._discover_endpoints(html, novel_id)

            if not endpoints:
                return self._create_result(
                    [], confidence=0.0, error="No AJAX endpoints found", response_time=time.time() - start_time
                )

            # Try each endpoint
            all_urls = []
            successful_endpoints = 0

            for endpoint in endpoints:
                if should_stop and should_stop():
                    break

                urls = self._try_endpoint(endpoint, novel_id)
                if urls:
                    all_urls.extend(urls)
                    successful_endpoints += 1

                # If we have enough URLs, we can stop
                if len(all_urls) >= 100:  # Reasonable threshold
                    break

            if not all_urls:
                return self._create_result(
                    [], confidence=0.0, error="No URLs from AJAX endpoints", response_time=time.time() - start_time
                )

            # Remove duplicates and validate
            all_urls = self._normalize_urls(all_urls)
            urls, validation_score = self._validate_urls(all_urls)

            # Analyze coverage
            coverage_range = self._analyze_coverage(urls)

            confidence = min(0.7 + (validation_score * 0.2) + (successful_endpoints * 0.1), 1.0)

            return self._create_result(
                urls=urls,
                confidence=confidence,
                coverage_range=coverage_range,
                validation_score=validation_score,
                response_time=time.time() - start_time,
                metadata={
                    "extraction_method": "ajax_endpoints",
                    "endpoints_tried": len(endpoints),
                    "successful_endpoints": successful_endpoints,
                },
            )

        except Exception as e:
            logger.debug(f"AJAX strategy failed: {e}")
            return self._create_result([], confidence=0.0, error=str(e), response_time=time.time() - start_time)

    def _extract_novel_id(self, html: str) -> Optional[str]:
        """Extract novel ID from HTML content."""
        # Try data attributes
        data_patterns = [
            r'data-novel-id=["\'](\d+)["\']',
            r'data-book-id=["\'](\d+)["\']',
            r'data-id=["\'](\d+)["\']',
        ]

        for pattern in data_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1)

        # Try JavaScript variables
        js_patterns = [
            r'novelId["\']?\s*[:=]\s*["\']?([^"\']+)["\']?',
            r'novel_id["\']?\s*[:=]\s*["\']?([^"\']+)["\']?',
            r'bookId["\']?\s*[:=]\s*["\']?([^"\']+)["\']?',
        ]

        for pattern in js_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                novel_id = match.group(1).strip().strip("\"'")
                if novel_id.isdigit():
                    return novel_id

        # Try URL patterns
        url_patterns = [
            r"/novel/(\d+)/",
            r"/book/(\d+)/",
            r"/b/([^/]+)",
        ]

        parsed_url = urlparse(self.base_url)
        path = parsed_url.path

        for pattern in url_patterns:
            match = re.search(pattern, path)
            if match:
                return match.group(1)

        return None

    def _discover_endpoints(self, html: str, novel_id: Optional[str]) -> List[str]:
        """Discover potential AJAX endpoints from HTML."""
        endpoints = []

        # Method 1: JavaScript variable patterns
        js_endpoint_patterns = [
            r'ajaxChapterUrl["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'chapterApiUrl["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'ajaxUrl["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'apiEndpoint["\']?\s*[:=]\s*["\']([^"\']+)["\']',
        ]

        for pattern in js_endpoint_patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE)
            for match in matches:
                url = match.group(1)
                endpoints.extend(self._expand_endpoint(url, novel_id))

        # Method 2: Common endpoint patterns
        if novel_id:
            common_patterns = [
                f"/api/chapters?novel_id={novel_id}",
                f"/ajax/chapter-list?novelId={novel_id}",
                f"/api/novel/{novel_id}/chapters",
                f"/book/ajax-chapters?bookId={novel_id}",
                f"/api/chapter/archive?novelId={novel_id}",
                f"/ajax/get-chapters?novel_id={novel_id}",
            ]
            endpoints.extend(common_patterns)

        # Method 3: Look for fetch() or XMLHttpRequest calls
        fetch_patterns = [
            r'fetch\(\s*["\']([^"\']*chapters?[^"\']*)["\']',
            r'XMLHttpRequest[^}]*open\(\s*["\']GET["\']\s*,\s*["\']([^"\']*chapters?[^"\']*)["\']',
        ]

        for pattern in fetch_patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                url = match.group(1)
                endpoints.extend(self._expand_endpoint(url, novel_id))

        # Remove duplicates while preserving order
        seen = set()
        unique_endpoints = []
        for endpoint in endpoints:
            if endpoint not in seen:
                seen.add(endpoint)
                unique_endpoints.append(endpoint)

        return unique_endpoints[:20]  # Limit to prevent too many requests

    def _expand_endpoint(self, url: str, novel_id: Optional[str]) -> List[str]:
        """Expand a template endpoint URL."""
        endpoints = []

        # Handle template variables
        if novel_id:
            expanded = url.replace("{novelId}", novel_id)
            expanded = expanded.replace("{id}", novel_id)
            expanded = expanded.replace("{novel_id}", novel_id)
            endpoints.append(expanded)

        # Add pagination variations
        base_endpoint = url.split("?")[0] if "?" in url else url
        query = parse_qs(url.split("?", 1)[1]) if "?" in url else {}

        # Try different pagination parameters
        pagination_params = [
            ("page", "1"),
            ("offset", "0"),
            ("start", "0"),
            ("p", "1"),
        ]

        for param_name, param_value in pagination_params:
            if param_name not in query:
                paginated_query = query.copy()
                paginated_query[param_name] = [param_value]
                paginated_url = base_endpoint + "?" + "&".join([f"{k}={v[0]}" for k, v in paginated_query.items()])
                endpoints.append(paginated_url)

        return endpoints

    def _try_endpoint(self, endpoint: str, novel_id: Optional[str]) -> List[str]:
        """Try to fetch chapter URLs from an AJAX endpoint."""
        try:
            # Make endpoint absolute
            if not endpoint.startswith(("http://", "https://")):
                endpoint = urljoin(self.base_url, endpoint)

            response = self._fetch_with_retry(endpoint)
            if not response:
                return []

            content_type = response.headers.get("content-type", "").lower()

            if "json" in content_type:
                return self._parse_json_response(response.text)
            elif "html" in content_type or "text" in content_type:
                return self._parse_html_response(response.text)
            else:
                # Try JSON first, then HTML
                try:
                    return self._parse_json_response(response.text)
                except (json.JSONDecodeError, ValueError):
                    return self._parse_html_response(response.text)

        except Exception as e:
            logger.debug(f"Failed to query endpoint {endpoint}: {e}")
            return []

    def _parse_json_response(self, text: str) -> List[str]:
        """Parse JSON response for chapter URLs."""
        urls = []

        try:
            data = json.loads(text)

            # Handle different JSON structures
            if isinstance(data, dict):
                # Try common data structures
                chapter_arrays = self._find_chapter_arrays(data)
                for chapter_array in chapter_arrays:
                    urls.extend(self._extract_urls_from_chapters(chapter_array))

            elif isinstance(data, list):
                # Direct array of chapters
                urls.extend(self._extract_urls_from_chapters(data))

        except (json.JSONDecodeError, ValueError):
            logger.debug("Failed to parse JSON response")

        return urls

    def _parse_html_response(self, text: str) -> List[str]:
        """Parse HTML response for chapter URLs."""
        urls = []

        # Look for links in the HTML
        link_pattern = r'href=["\']([^"\']*chapter[^"\']*)["\']'
        matches = re.finditer(link_pattern, text, re.IGNORECASE)

        for match in matches:
            url = match.group(1)
            if self._is_likely_chapter_url(url):
                urls.append(url)

        return urls

    def _find_chapter_arrays(self, data: Dict[str, Any]) -> List[List[Dict[str, Any]]]:
        """Find arrays containing chapter data in JSON structure."""
        arrays = []

        # Common keys that might contain chapter arrays
        chapter_keys = [
            "chapters",
            "chapterList",
            "data",
            "list",
            "items",
            "chapter_data",
            "chapters_list",
            "chapter_items",
        ]

        def search_obj(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key.lower() in chapter_keys and isinstance(value, list):
                        arrays.append(value)
                    search_obj(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    search_obj(item, f"{path}[{i}]")

        search_obj(data)
        return arrays

    def _extract_urls_from_chapters(self, chapters: List[Dict[str, Any]]) -> List[str]:
        """Extract URLs from chapter objects."""
        urls = []

        for chapter in chapters:
            if isinstance(chapter, dict):
                # Try common URL field names
                url_fields = ["url", "href", "link", "chapter_url", "chapterUrl"]

                for field in url_fields:
                    if field in chapter and isinstance(chapter[field], str):
                        url = chapter[field].strip()
                        if url and self._is_likely_chapter_url(url):
                            urls.append(url)
                            break

        return urls

    def _is_likely_chapter_url(self, url: str) -> bool:
        """Check if URL looks like a chapter URL."""
        url_lower = url.lower()

        # Must have chapter indicator
        chapter_indicators = ["chapter", "ch", "chap", "episode", "ep", "第", "章"]
        has_indicator = any(indicator in url_lower for indicator in chapter_indicators)

        # Must have number
        has_number = bool(re.search(r"\d+", url))

        # Reasonable length
        reasonable_length = 10 <= len(url) <= 500

        return has_indicator and has_number and reasonable_length

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
