"""
HTML Structure Analysis Strategy.

Parses HTML directly to find chapter links using intelligent selectors
and pattern recognition.
"""

import re
import time
from typing import List, Optional, Callable, Any, Tuple, Set
from collections import defaultdict

from core.logger import get_logger
from ..universal_url_detector import BaseDetectionStrategy, DetectionResult

logger = get_logger("scraper.strategies.html_parsing")


class HtmlParsingStrategy(BaseDetectionStrategy):
    """Strategy that parses HTML structure to find chapter links."""

    def __init__(self, base_url: str, session_manager):
        super().__init__("html_parsing", base_url, session_manager)
        self._adaptive_selectors = self._load_adaptive_selectors()

    async def detect(self, toc_url: str, should_stop: Optional[Callable[[], bool]] = None) -> DetectionResult:
        """Detect chapter URLs by parsing HTML structure."""
        start_time = time.time()

        try:
            response = self._fetch_with_retry(toc_url)
            if not response:
                return self._create_result(
                    [], confidence=0.0, error="Failed to fetch page", response_time=time.time() - start_time
                )

            html = response.text

            # Extract URLs using multiple HTML parsing methods
            urls = self._extract_from_html(html)

            if not urls:
                return self._create_result(
                    [], confidence=0.0, error="No chapter links found", response_time=time.time() - start_time
                )

            # Validate and normalize
            urls, validation_score = self._validate_urls(urls)

            # Analyze coverage
            coverage_range = self._analyze_coverage(urls)

            # Learn from successful patterns
            if urls:
                self._learn_patterns(html, urls)

            confidence = min(0.6 + (validation_score * 0.3), 1.0)

            return self._create_result(
                urls=urls,
                confidence=confidence,
                coverage_range=coverage_range,
                validation_score=validation_score,
                response_time=time.time() - start_time,
                metadata={"extraction_method": "html_parsing", "selectors_used": len(self._adaptive_selectors)},
            )

        except Exception as e:
            logger.debug(f"HTML parsing strategy failed: {e}")
            return self._create_result([], confidence=0.0, error=str(e), response_time=time.time() - start_time)

    def _extract_from_html(self, html: str) -> List[str]:
        """Extract chapter URLs from HTML using various methods."""
        urls = []

        # Method 1: Use adaptive CSS selectors
        urls.extend(self._extract_with_selectors(html))

        # Method 2: Use regex patterns for common link structures
        urls.extend(self._extract_with_patterns(html))

        # Method 3: Look for structured data (JSON-LD, etc.)
        urls.extend(self._extract_structured_data(html))

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return unique_urls

    def _extract_with_selectors(self, html: str) -> List[str]:
        """Extract URLs using CSS selectors."""
        urls = []

        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")

            # Try adaptive selectors based on site learning
            for selector_info in self._adaptive_selectors:
                selector = selector_info["selector"]
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        url = self._extract_url_from_element(element)
                        if url:
                            urls.append(url)
                except Exception:
                    continue  # Skip invalid selectors

            # Try common chapter link selectors
            common_selectors = [
                'a[href*="chapter"]',
                'a[href*="chap"]',
                'a[href*="ch-"]',
                'a[href*="ch_"]',
                'a[href*="episode"]',
                'a[href*="part"]',
                ".chapter-link a",
                ".chapter-item a",
                ".chapter-list a",
                'li a[href*="chapter"]',
                'td a[href*="chapter"]',
                '.toc a[href*="chapter"]',
                '#toc a[href*="chapter"]',
            ]

            for selector in common_selectors:
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        url = self._extract_url_from_element(element)
                        if url and url not in urls:  # Avoid duplicates
                            urls.append(url)
                except Exception:
                    continue

        except ImportError:
            # Fallback without BeautifulSoup
            urls.extend(self._extract_with_patterns(html))

        return urls

    def _extract_url_from_element(self, element) -> Optional[str]:
        """Extract URL from a BeautifulSoup element."""
        try:
            href = element.get("href")
            if not href:
                return None

            # Check if it's a chapter link
            text = element.get_text().strip()
            if self._is_chapter_link(href, text):
                return href

        except Exception:
            pass

        return None

    def _extract_with_patterns(self, html: str) -> List[str]:
        """Extract URLs using regex patterns."""
        urls = []

        # Pattern 1: Standard anchor tags with chapter URLs
        link_patterns = [
            r'href=["\']([^"\']*chapter[^"\']*)["\'][^>]*>([^<]*)</a>',
            r'href=["\']([^"\']*chap[^"\']*)["\'][^>]*>([^<]*)</a>',
            r'href=["\']([^"\']*ch[^"\']*\d+[^"\']*)["\'][^>]*>([^<]*)</a>',
        ]

        for pattern in link_patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                url = match.group(1)
                text = match.group(2).strip()

                if self._is_chapter_link(url, text):
                    urls.append(url)

        # Pattern 2: Look for structured chapter listings
        list_patterns = [
            r'<li[^>]*>.*?<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]*Chapter[^<]*)</a>.*?</li>',
            r'<tr[^>]*>.*?<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]*Chapter[^<]*)</a>.*?</tr>',
            r'<div[^>]*class="[^"]*chapter[^"]*"[^>]*>.*?<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>.*?</div>',
        ]

        for pattern in list_patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                url = match.group(1)
                text = match.group(2).strip()

                if self._is_chapter_link(url, text):
                    urls.append(url)

        return urls

    def _extract_structured_data(self, html: str) -> List[str]:
        """Extract URLs from structured data (JSON-LD, etc.)."""
        urls = []

        # JSON-LD structured data
        json_ld_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
        matches = re.finditer(json_ld_pattern, html, re.IGNORECASE | re.DOTALL)

        for match in matches:
            try:
                import json

                data = json.loads(match.group(1))

                # Look for chapter URLs in structured data
                def find_chapter_urls(obj):
                    if isinstance(obj, dict):
                        for key, value in obj.items():
                            if key.lower() in ["url", "sameAs"] and isinstance(value, str):
                                if "chapter" in value.lower():
                                    urls.append(value)
                            else:
                                find_chapter_urls(value)
                    elif isinstance(obj, list):
                        for item in obj:
                            find_chapter_urls(item)

                find_chapter_urls(data)

            except (json.JSONDecodeError, ImportError):
                continue

        return urls

    def _is_chapter_link(self, url: str, text: str) -> bool:
        """Determine if a link is a chapter link."""
        url_lower = url.lower()
        text_lower = text.lower()

        # Text-based indicators
        text_indicators = ["chapter", "chap", "ch ", "episode", "ep ", "part", "第", "章", "话", "节", "回"]  # Chinese

        has_text_indicator = any(indicator in text_lower for indicator in text_indicators)

        # URL-based indicators
        url_indicators = ["chapter", "chap", "ch-", "ch_", "episode", "ep-", "/c/", "/chapter/", "/chap/"]

        has_url_indicator = any(indicator in url_lower for indicator in url_indicators)

        # Must have numbers (chapter numbers)
        has_number = bool(re.search(r"\d+", url))

        # Not too short
        reasonable_length = len(url) > 5

        return (has_text_indicator or has_url_indicator) and has_number and reasonable_length

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

    def _load_adaptive_selectors(self) -> List[dict]:
        """Load adaptive selectors based on site learning."""
        # Default selectors that work for most sites
        default_selectors = [
            {"selector": 'a[href*="chapter"]', "success_rate": 0.8},
            {"selector": ".chapter-list a", "success_rate": 0.7},
            {"selector": '.toc a[href*="chapter"]', "success_rate": 0.6},
            {"selector": 'li a[href*="chap"]', "success_rate": 0.5},
            {"selector": 'td a[href*="chapter"]', "success_rate": 0.4},
        ]

        # In a real implementation, this would load from a learned configuration
        # based on the site domain

        return default_selectors

    def _learn_patterns(self, html: str, successful_urls: List[str]):
        """Learn successful patterns for future use."""
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")

            # Find common patterns in successful URLs
            successful_patterns = []

            for url in successful_urls[:10]:  # Sample first 10
                # Find the element containing this URL
                element = soup.find("a", href=url)
                if element:
                    # Generate CSS selector for this element
                    selector = self._generate_selector(element)
                    if selector:
                        successful_patterns.append(selector)

            # Update adaptive selectors with successful patterns
            for pattern in successful_patterns:
                # Add or update success rate
                existing = next((s for s in self._adaptive_selectors if s["selector"] == pattern), None)
                if existing:
                    existing["success_rate"] = min(existing["success_rate"] + 0.1, 1.0)
                else:
                    self._adaptive_selectors.append(
                        {"selector": pattern, "success_rate": 0.6}  # Initial success rate for new patterns
                    )

            # Sort by success rate
            self._adaptive_selectors.sort(key=lambda x: x["success_rate"], reverse=True)

        except (ImportError, Exception):
            pass  # Learning failed, but don't break the main flow

    def _generate_selector(self, element) -> Optional[str]:
        """Generate a CSS selector for a BeautifulSoup element."""
        try:
            # Simple selector generation
            selectors = []

            # ID is most specific
            element_id = element.get("id")
            if element_id:
                selectors.append(f"#{element_id}")

            # Class combinations
            classes = element.get("class", [])
            if classes:
                class_selector = ".".join(classes)
                selectors.append(f"a.{class_selector}")

            # Parent element context
            parent = element.parent
            if parent and parent.name:
                parent_classes = parent.get("class", [])
                if parent_classes:
                    parent_selector = f'{parent.name}.{".".join(parent_classes)} a'
                    selectors.append(parent_selector)

            # Return the most specific selector
            return selectors[0] if selectors else None

        except Exception:
            return None
